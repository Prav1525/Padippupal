import json

from fastapi.testclient import TestClient

import app as curriculum


def test_tutor_requires_server_side_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = TestClient(curriculum.app)
    response = client.post("/tutor/chat", json={
        "board": "CBSE",
        "class_level": 6,
        "subject": "Science",
        "medium": "English",
        "app_language": "Tanglish",
        "message": "Explain photosynthesis simply.",
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_tutor_uses_profile_and_gentle_prompt(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({
                "candidates": [{"content": {"parts": [{"text": "Namma simple-a paakalam. Plants use sunlight to make food."}]}}]
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = request.headers
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {
        "matches": [{
            "text": "Plants use sunlight to make food.",
            "source": {
                "title": "Class 6 Science textbook",
                "board": "CBSE",
                "class_level": 6,
                "subject": "Science",
                "medium": "English",
                "page_start": 12,
                "page_end": 12,
                "url": "https://example.invalid/book.pdf",
            },
        }],
        "warning": None,
    })
    monkeypatch.setattr(curriculum, "find_visual_lesson", lambda board, grade, subject, query: {
        "title": "Photosynthesis", "steps": [{"label": "Sunlight"}, {"label": "Plant makes food"}]
    } if "photosynthesis" in query.casefold() else None)
    client = TestClient(curriculum.app)
    response = client.post("/tutor/chat", json={
        "board": "CBSE",
        "class_level": 6,
        "subject": "Science",
        "medium": "English",
        "app_language": "Tanglish",
        "student_name": "Test learner",
        "chapter": "Life Processes",
        "topic": "Photosynthesis",
        "message": "Explain this simply.",
        "history": [{"role": "user", "content": "I am confused."}],
    })
    assert response.status_code == 200
    assert response.json()["answer"].startswith("Namma")
    assert response.json()["grounded"] is True
    assert response.json()["visual_lesson"]["title"] == "Photosynthesis"
    assert "systemInstruction" in captured["payload"]
    prompt = captured["payload"]["systemInstruction"]["parts"][0]["text"]
    assert "warm, patient school tutor" in prompt
    assert "Tanglish" in prompt
    assert "chapter=Life Processes" in prompt
    assert "subtopic=Photosynthesis" in prompt
    assert "SYLLABUS AND LESSON-PLAN BOUNDARY" in prompt
    assert "Do not silently introduce later-grade material" in prompt
    assert "Never invent NCERT chapter titles" in prompt
    assert "Do not answer from general knowledge, web sources, or memory" in prompt
    assert captured["timeout"] == 45

def test_tutor_speech_requires_server_side_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = TestClient(curriculum.app)
    response = client.post("/tutor/speech", json={
        "text": "Let's learn this one small step at a time.",
        "app_language": "English",
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_tutor_speech_returns_wav_and_uses_gentle_voice(monkeypatch):
    import base64
    import io
    import wave

    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            pcm = b"\x00\x00" * 24
            return json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{
                            "inlineData": {
                                "mimeType": "audio/L16;rate=24000",
                                "data": base64.b64encode(pcm).decode("ascii"),
                            }
                        }]
                    }
                }]
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = request.headers
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    client = TestClient(curriculum.app)
    response = client.post("/tutor/speech", json={
        "text": "Namma idha simple-a paakalam.",
        "app_language": "Tanglish",
    })
    assert response.status_code == 200
    body = response.json()
    wav_bytes = base64.b64decode(body["audio_base64"])
    with wave.open(io.BytesIO(wav_bytes), "rb") as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getframerate() == 24000
        assert audio.readframes(24) == b"\x00\x00" * 24
    assert body["provider"] == "gemini"
    assert captured["headers"]["X-goog-api-key"] == "test-gemini-key"
    assert captured["payload"]["generationConfig"]["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"] == "Aoede"
    assert "Tanglish" in captured["payload"]["contents"][0]["parts"][0]["text"]

def test_voice_health_reports_configuration_without_secret(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-returned")
    response = TestClient(curriculum.app).get("/health/voice")
    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert response.json()["provider"] == "gemini"
    assert "must-not-be-returned" not in response.text




def test_subject_detection_switches_subject_automatically():
    assert curriculum.infer_tutor_subject("Can you solve 2 + 2?", "Science") == "Mathematics"
    assert curriculum.infer_tutor_subject("Explain photosynthesis", "Mathematics") == "Science"
    assert curriculum.infer_tutor_subject("What is a noun?", "Science") == "English"
    assert curriculum.infer_tutor_subject("Explain democracy", "Mathematics") == "Social Science"
    assert curriculum.infer_tutor_subject("Why is this step correct?", "Mathematics") == "Mathematics"



def test_interactive_lesson_catalog_covers_all_class_six_chapters(monkeypatch, tmp_path):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "interactive-lessons.sqlite3")
    curriculum.init_db()
    client = TestClient(curriculum.app)
    science = client.get("/interactive-lessons", params={"board": "CBSE", "class_level": 6, "subject": "Science", "limit": 100})
    maths = client.get("/interactive-lessons", params={"board": "CBSE", "class_level": 6, "subject": "Mathematics", "limit": 100})
    assert science.status_code == 200
    assert maths.status_code == 200
    assert science.json()["count"] == 36
    assert maths.json()["count"] == 91
    assert all(item["objects"] and item["steps"] and item["challenge"]["question"] for item in science.json()["lessons"] + maths.json()["lessons"])
    assert len({item["chapter"] for item in science.json()["lessons"]}) == 12
    assert len({item["chapter"] for item in maths.json()["lessons"]}) == 10


def test_interactive_lesson_match_returns_simulation_blueprint(monkeypatch, tmp_path):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "interactive-match.sqlite3")
    curriculum.init_db()
    client = TestClient(curriculum.app)
    response = client.get("/interactive-lessons/match", params={
        "board": "CBSE", "class_level": 6, "subject": "Science",
        "chapter": "Exploring Magnets", "topic": "Magnetic and non-magnetic materials"
    })
    assert response.status_code == 200
    lesson = response.json()["interactive_lesson"]
    assert lesson["scene_type"] == "magnet_test"
    assert lesson["challenge"]["question"]
    assert len(lesson["objects"]) >= 3



def test_tutor_does_not_answer_without_matching_database_passage(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-called")
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {
        "matches": [],
        "warning": "No exact curriculum match found.",
    })

    def unexpected_urlopen(*args, **kwargs):
        raise AssertionError("Gemini must not be called without textbook context")

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", unexpected_urlopen)
    response = TestClient(curriculum.app).post("/tutor/chat", json={
        "board": "CBSE",
        "class_level": 6,
        "subject": "Science",
        "medium": "English",
        "app_language": "English",
        "chapter": "A Book of Solutions",
        "topic": "Test topic",
        "message": "Explain this topic.",
    })

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["sources"] == []
    assert body["provider"] == "curriculum_database"
    assert "couldn't find a matching passage" in body["answer"].lower()
    assert "no external knowledge was used" in body["grounding_warning"].lower()



def test_chapter_matching_uses_the_stored_book_opening_not_other_chapters():
    assert curriculum.chapter_matches_source(
        "Lines and Angles",
        "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp102.pdf)",
        "[Page 1] Lines and angLes2 In this chapter, we explore points, lines, rays, and angles.",
    )
    assert not curriculum.chapter_matches_source(
        "Fractions",
        "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp102.pdf)",
        "[Page 1] Lines and angLes2 In this chapter, we explore points, lines, rays, and angles.",
    )
    assert curriculum.chapter_matches_source(
        "A Journey through States of Water",
        "NCERT Curiosity Class 6 Science — Chapter PDF (fecu108.pdf)",
        "[Page 1] A Journey through States of Water8 Chapter On a bright summer afternoon...",
    )
