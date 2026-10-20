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

    assert curriculum.chapter_matches_source(
        "Chapter 7: Fractions",
        "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp107.pdf)",
    )
    assert curriculum.chapter_matches_source(
        "Chapter 4",
        "NCERT Curiosity Class 6 Science — Chapter PDF (fecu104.pdf)",
    )
    assert not curriculum.chapter_matches_source(
        "Fractions",
        "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp102.pdf)",
    )
    assert not curriculum.chapter_matches_source(
        "Fractions",
        "NCERT Ganita Prakash Class 6 Mathematics — Preliminary Pages",
    )
    assert not curriculum.chapter_matches_source(
        "Fractions",
        "Unmapped textbook PDF",
    )
    assert curriculum.chapter_matches_chunk(
        "Fractions",
        "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp107.pdf)",
        "Fractions",
    )
    assert not curriculum.chapter_matches_chunk(
        "Fractions",
        "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp107.pdf)",
        None,
    )
    assert not curriculum.chapter_matches_chunk(
        "Fractions",
        "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp102.pdf)",
        "Fractions",
    )


def test_lesson_plan_returns_short_source_grounded_segments(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    chunk_id = "chunk-123"
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            payload = {"segments": [{"id": "s1", "spoken_text": "A magnet has two poles.",
                "caption_text": "A magnet has two poles", "source_chunk_ids": [chunk_id],
                "visual_action": {"type": "highlight", "target": "magnet-poles", "value": ""}, "checkpoint": None}]}
            return json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]}).encode()
    def fake_urlopen(request, timeout):
        body = json.loads(request.data.decode())
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        return FakeResponse()
    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [{
        "text": "A magnet has two poles.", "source": {"chunk_id": chunk_id, "source_id": "source-1",
        "title": "Class 6 Science", "board": "CBSE", "class_level": 6, "subject": "Science",
        "medium": "English", "page_start": 10, "page_end": 10}}]})
    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
        "chapter": "Exploring Magnets", "topic": "Magnet poles", "message": "Teach me magnet poles",
        "app_language": "English"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["timing_mode"] == "segment"
    assert body["word_timestamps_available"] is False
    assert body["segments"][0]["source_chunk_ids"] == [chunk_id]

def test_lesson_plan_rejects_unretrieved_chunk_ids():
    import pytest
    with pytest.raises(curriculum.HTTPException):
        curriculum._validate_lesson_plan(json.dumps({"segments": [{
            "id": "s1", "spoken_text": "Invented fact.", "caption_text": "Invented fact.",
            "source_chunk_ids": ["unknown"], "visual_action": {"type": "none", "target": "", "value": ""},
            "checkpoint": None}]}), {"known"}, 5)

def test_lesson_plan_does_not_generate_when_retrieval_is_empty(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": []})
    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
        "chapter": "Exploring Magnets", "message": "Teach me magnets"})
    assert response.status_code == 200
    assert response.json()["grounded"] is False
    assert response.json()["segments"] == []
    assert "No matching textbook passage" in response.json()["warning"]


def test_chapter_lesson_draft_schema_and_review_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "chapter-lessons.sqlite3")
    monkeypatch.setenv("PADIPPUPAL_ADMIN_TOKEN", "test-admin")
    curriculum.init_db()
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO chapter_lessons
               (id,board,class_level,subject,medium,chapter,topic,status,lesson_json,
                source_refs_json,model,review_feedback,created_at,updated_at)
               VALUES (?,?,?,?,?,?,'','draft',?,?,?,'',?,?)""",
            ("draft-1","CBSE",6,"Mathematics","English","Patterns in Mathematics",
             json.dumps({"overview":"Patterns repeat","teaching_sequence":[{"title":"Spot the rule"}]}),
             json.dumps([{"chunk_id":"c1","page_start":1}]),"test-model",1.0,1.0))
    client = TestClient(curriculum.app)
    headers = {"x-admin-token":"test-admin"}
    listing = client.get("/admin/chapter-lessons", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    detail = client.get("/admin/chapter-lessons/draft-1", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["lesson"]["overview"] == "Patterns repeat"
    reviewed = client.post("/admin/chapter-lessons/draft-1/review", headers=headers,
                           json={"decision":"approve","feedback":"Verified against source pages"})
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "approved"
    approved = client.get("/chapter-lessons/approved", params={
        "board":"CBSE","class_level":6,"subject":"Mathematics","medium":"English",
        "chapter":"Patterns in Mathematics"})
    assert approved.status_code == 200
    assert approved.json()["lesson_id"] == "draft-1"
    assert approved.json()["lesson"]["overview"] == "Patterns repeat"


def test_chapter_lesson_admin_routes_fail_closed_without_token(monkeypatch, tmp_path):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "chapter-lessons-auth.sqlite3")
    monkeypatch.setenv("PADIPPUPAL_ADMIN_TOKEN", "")
    monkeypatch.delenv("PADIPPUPAL_ALLOW_UNAUTHENTICATED_ADMIN", raising=False)
    curriculum.init_db()
    response = TestClient(curriculum.app).get("/admin/chapter-lessons")
    assert response.status_code == 503


def test_chapter_source_chunks_only_selects_exact_chapter_and_profile(monkeypatch, tmp_path):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "chapter-source.sqlite3")
    curriculum.init_db()
    now = 1.0
    with curriculum.db() as conn:
        conn.execute("""INSERT INTO sources
            (id,board,academic_year,class_level,subject,medium,term,edition,title,source_url,
             license_note,sha256,status,page_count,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("s1","CBSE","2026-27",6,"Mathematics","English","","1",
             "NCERT Ganita Prakash Class 6 Mathematics — Chapter PDF (fegp101.pdf)","",
             "licensed","hash1","ready",5,now))
        conn.execute("""INSERT INTO chunks (id,source_id,chunk_no,chapter,page_start,page_end,text)
            VALUES (?,?,?,?,?,?,?)""",("c1","s1",0,"Patterns in Mathematics",1,2,"Number patterns repeat."))
        conn.execute("""INSERT INTO chunks (id,source_id,chunk_no,chapter,page_start,page_end,text)
            VALUES (?,?,?,?,?,?,?)""",("c2","s1",1,"Lines and Angles",3,4,"Angles meet."))
    payload = curriculum.ChapterLessonGenerateRequest(board="CBSE",class_level=6,
        subject="Mathematics",medium="English",chapter="Patterns in Mathematics")
    rows = curriculum._chapter_source_chunks(payload)
    assert [row["chunk_id"] for row in rows] == ["c1"]
