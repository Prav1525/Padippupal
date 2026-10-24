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

def test_tutor_speech_requires_cloud_tts_configuration(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("SARVAM_API_KEY", "")
    client = TestClient(curriculum.app)
    response = client.post("/tutor/speech", json={
        "text": "Let's learn this one small step at a time.",
        "app_language": "English",
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()



def test_tutor_speech_falls_back_to_sarvam_when_gemini_is_not_configured(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam-key")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    captured = {}

    def fake_sarvam(text, language):
        captured["text"] = text
        captured["language"] = language
        return {
            "audio_base64": "d2F2",
            "mime_type": "audio/wav",
            "provider": "sarvam",
            "word_timings": [],
        }

    def unexpected_gemini_request(*args, **kwargs):
        raise AssertionError("Gemini must not be called when Sarvam succeeds")

    monkeypatch.setattr(curriculum, "_sarvam_tutor_speech", fake_sarvam)
    monkeypatch.setattr(curriculum.urllib.request, "urlopen", unexpected_gemini_request)
    response = TestClient(curriculum.app).post("/tutor/speech", json={
        "text": "We learn one small step at a time.",
        "app_language": "English",
    })

    assert response.status_code == 200
    assert response.json()["provider"] == "sarvam"
    assert captured == {
        "text": "We learn one small step at a time.",
        "language": "English",
    }

def test_tutor_speech_returns_wav_and_uses_gentle_voice(monkeypatch):
    import base64
    import io
    import wave

    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    captured = {}

    def unexpected_sarvam_fallback(text, language):
        raise AssertionError("Gemini must be attempted before Sarvam when both providers are configured")

    monkeypatch.setattr(curriculum, "_sarvam_tutor_speech", unexpected_sarvam_fallback)

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
    monkeypatch.setenv("SARVAM_API_KEY", "")
    response = TestClient(curriculum.app).get("/health/voice")
    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert response.json()["provider"] == "gemini"
    assert "must-not-be-returned" not in response.text


def test_voice_health_reports_sarvam_as_primary_when_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam-key")
    response = TestClient(curriculum.app).get("/health/voice")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "sarvam"
    assert body["model"] == "bulbul:v3"
    assert body["fallback"] == "gemini"
    assert body["fallback_chain"] == ["sarvam", "gemini", "android-tts"]
    assert "test-sarvam-key" not in response.text




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
    science = client.get("/interactive-lessons", params={"board": "CBSE", "class_level": 6, "subject": "Science", "limit": 200})
    maths = client.get("/interactive-lessons", params={"board": "CBSE", "class_level": 6, "subject": "Mathematics", "limit": 200})
    assert science.status_code == 200
    assert maths.status_code == 200
    assert science.json()["count"] == 36
    # The catalogue may grow as chapter-specific lessons are added.
    assert maths.json()["count"] >= 91
    chapter_one = client.get("/interactive-lessons", params={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "chapter": "Patterns in Mathematics", "limit": 100
    })
    chapter_lessons = chapter_one.json()["lessons"]
    assert chapter_one.status_code == 200
    assert len(chapter_lessons) >= 20
    topics = {item["topic"] for item in chapter_lessons}
    assert {
        "What is Mathematics?", "All 1s", "Patterns in Numbers",
        "Odd and Even Numbers", "Triangular Numbers", "Square Numbers",
        "Cube Numbers", "Virahanka Numbers", "Powers of 2 and 3",
        "Visualising Number Sequences", "Odd Numbers Make Squares",
        "Two Triangles Make a Square", "Relations among Number Sequences",
        "Hexagonal Numbers and Cubes", "Patterns in Shapes", "Regular Polygons",
        "Complete Graphs", "Stacked Shapes", "Koch Snowflake",
        "Relation to Number Sequences"
    }.issubset(topics)
    assert all(item["objects"] and len(item["steps"]) >= 3 and item["challenge"]["question"] for item in chapter_lessons)
    # Chapter 1's All 1s visual must teach repetition, not unrelated arithmetic.
    all_ones = next(item for item in chapter_lessons if item["topic"] == "All 1s")
    assert all(obj["label"] == "1" for obj in all_ones["objects"])
    assert "1, 1, 1" in all_ones["steps"][0]["text"]
    assert "repeat" in all_ones["steps"][1]["text"].lower()
    assert all_ones["challenge"]["answer"] == "1"
    assert all(option in {"1", "2", "3"} for option in all_ones["challenge"]["options"])
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


def test_lesson_plan_retries_when_generated_segment_has_empty_speech(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    chunk_id = "chunk-empty-segment"
    responses = [
        {"segments": [{
            "id": "empty", "spoken_text": "   ", "caption_text": "",
            "source_chunk_ids": [chunk_id],
            "visual_action": {"type": "none", "target": "", "value": ""},
            "checkpoint": None,
        }]},
        {"segments": [{
            "id": "valid", "spoken_text": "The number one repeats.",
            "caption_text": "The number one repeats.",
            "source_chunk_ids": [chunk_id],
            "visual_action": {"type": "highlight", "target": "one", "value": ""},
            "checkpoint": "Does that make sense so far?",
        }]},
    ]
    request_count = {"value": 0}

    class FakeResponse:
        def __init__(self, payload): self.payload = payload
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(self.payload)}]}}]}).encode()

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode())
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        result = responses[min(request_count["value"], len(responses) - 1)]
        request_count["value"] += 1
        return FakeResponse(result)

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [{
        "text": "The All 1s pattern repeats the number one.",
        "source": {"chunk_id": chunk_id, "source_id": "source-1",
                   "title": "Class 6 Mathematics", "board": "CBSE", "class_level": 6,
                   "subject": "Mathematics", "medium": "English", "page_start": 3, "page_end": 3},
    }]})

    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics", "medium": "English",
        "app_language": "English", "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach me All 1s",
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grounded"] is True
    assert len(body["segments"]) == 1
    assert body["segments"][0]["spoken_text"] == "The number one repeats."
    assert request_count["value"] == 2


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

def test_lesson_plan_filters_unrelated_topic_passages_before_calling_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-called")
    retrieval_requests = []
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: (
        retrieval_requests.append(payload) or {"matches": [{
            "text": "Let us look at a pattern by adding counting numbers up and then down.",
            "source": {"chunk_id": "wrong-topic", "title": "Class 6 Mathematics",
                       "page_start": 1, "page_end": 1},
        }]}
    ))

    def unexpected_urlopen(*args, **kwargs):
        raise AssertionError("Gemini must not be called with an unrelated passage")

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", unexpected_urlopen)
    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "app_language": "English",
        "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach this as a patient teacher in short, simple segments. Explain examples, add natural pauses, and ask whether I understand.",
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grounded"] is False
    assert body["segments"] == []
    assert body["sources"] == []
    assert "selected topic" in body["warning"].lower()
    assert len(retrieval_requests) == 1
    assert retrieval_requests[0].query == "All 1s Patterns in Mathematics"
    assert retrieval_requests[0].limit == 10


def test_lesson_plan_falls_back_to_matched_source_when_gemini_drifts_from_all_ones(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    chunk_id = "all-ones-source"
    generated = {"segments": [
        {"id": "s1", "spoken_text": "Welcome to the topic All ones.",
         "caption_text": "Welcome to the topic All ones.", "source_chunk_ids": [chunk_id],
         "visual_action": {"type": "label", "target": "ones", "value": ""},
         "checkpoint": None},
        {"id": "s2", "spoken_text": "Let us look at a beautiful pattern by adding counting numbers up and then down.",
         "caption_text": "Let us look at a beautiful pattern by adding counting numbers up and then down.",
         "source_chunk_ids": [chunk_id],
         "visual_action": {"type": "reveal", "target": "pattern-sequence", "value": "1 + 2 + 1 = 4"},
         "checkpoint": "Does that make sense so far?"},
    ]}

    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(generated)}]}}]}).encode()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", lambda request, timeout: FakeResponse())
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [{
        "text": "The All 1s pattern repeats the number 1: 1, 1, 1, 1.",
        "source": {"chunk_id": chunk_id, "source_id": "source-1",
                   "title": "Class 6 Mathematics", "board": "CBSE", "class_level": 6,
                   "subject": "Mathematics", "medium": "English", "page_start": 1, "page_end": 1},
    }]})

    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "app_language": "English",
        "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach me All 1s",
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grounded"] is True
    assert body["provider"] == "textbook_extract_fallback"
    assert len(body["segments"]) == 1
    assert body["segments"][0]["source_chunk_ids"] == [chunk_id]
    assert "The All 1s pattern repeats the number 1" in body["segments"][0]["spoken_text"]
    assert "off-topic" in body["warning"].lower()




def test_lesson_plan_retries_when_a_later_segment_is_generic_not_all_ones(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    chunk_id = "all-ones-source"
    outputs = [
        {"segments": [
            {"id": "intro", "spoken_text": "Today we will learn All 1s: 1, 1, 1.",
             "caption_text": "All 1s: 1, 1, 1.", "source_chunk_ids": [chunk_id],
             "visual_action": {"type": "highlight", "target": "ones", "value": ""},
             "checkpoint": None},
            {"id": "generic", "spoken_text": "Mathematics is the search for patterns and explanations.",
             "caption_text": "Mathematics is the search for patterns and explanations.",
             "source_chunk_ids": [chunk_id],
             "visual_action": {"type": "none", "target": "", "value": ""},
             "checkpoint": "Does that make sense so far?"},
        ]},
        {"segments": [
            {"id": "intro", "spoken_text": "Today we will learn All 1s: 1, 1, 1.",
             "caption_text": "All 1s: 1, 1, 1.", "source_chunk_ids": [chunk_id],
             "visual_action": {"type": "highlight", "target": "ones", "value": ""},
             "checkpoint": None},
            {"id": "repeat", "spoken_text": "The number 1 repeats, so each term stays the same.",
             "caption_text": "The number 1 repeats, so each term stays the same.",
             "source_chunk_ids": [chunk_id],
             "visual_action": {"type": "highlight", "target": "repeated-ones", "value": ""},
             "checkpoint": "Does that make sense so far?"},
        ]},
    ]
    requests = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(self.payload)}]}}]}).encode()

    def fake_urlopen(request, timeout):
        requests.append(json.loads(request.data.decode()))
        return FakeResponse(outputs[min(len(requests) - 1, len(outputs) - 1)])

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [{
        "text": "The All 1s pattern repeats the number 1: 1, 1, 1, 1.",
        "source": {"chunk_id": chunk_id, "source_id": "source-1",
                   "title": "Class 6 Mathematics", "board": "CBSE", "class_level": 6,
                   "subject": "Mathematics", "medium": "English", "page_start": 3, "page_end": 3},
    }]})

    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "app_language": "English",
        "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach me All 1s",
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(requests) == 2, "generic later segment must trigger the one allowed retry"
    assert body["grounded"] is True
    assert [segment["id"] for segment in body["segments"]] == ["intro", "repeat"]
    assert "repeats" in body["segments"][1]["spoken_text"].lower()

def test_lesson_plan_retries_once_after_malformed_json(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    chunk_id = "chunk-retry-verified"
    lesson_json = json.dumps({"segments": [{
        "id": "segment-1",
        "spoken_text": "A magnet has two poles.",
        "caption_text": "A magnet has two poles.",
        "source_chunk_ids": [chunk_id],
        "visual_action": {"type": "none", "target": "", "value": ""},
        "checkpoint": None,
    }]})
    outputs = ["this is not JSON", lesson_json]
    requests = []
    class FakeResponse:
        def __init__(self, text): self.text = text
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{"text": self.text}]}}]}).encode()
    def fake_urlopen(request, timeout):
        body = json.loads(request.data.decode())
        requests.append(body)
        return FakeResponse(outputs.pop(0))
    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [{
        "text": "A magnet has two poles.", "source": {"chunk_id": chunk_id, "source_id": "source-1",
        "title": "Class 6 Science", "board": "CBSE", "class_level": 6, "subject": "Science",
        "medium": "English", "page_start": 10, "page_end": 10}}]})
    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
        "chapter": "Exploring Magnets", "topic": "Magnet poles", "message": "Teach me magnet poles",
        "app_language": "English"})
    assert response.status_code == 200, response.text
    assert len(requests) == 2
    assert requests[0]["generationConfig"]["responseMimeType"] == "application/json"
    assert "previous response failed" in requests[1]["contents"][0]["parts"][0]["text"].lower()
    assert response.json()["segments"][0]["source_chunk_ids"] == [chunk_id]

def test_lesson_plan_rejects_unretrieved_chunk_ids():
    import pytest
    with pytest.raises(curriculum.HTTPException):
        curriculum._validate_lesson_plan(json.dumps({"segments": [{
            "id": "s1", "spoken_text": "Invented fact.", "caption_text": "Invented fact.",
            "source_chunk_ids": ["unknown"], "visual_action": {"type": "none", "target": "", "value": ""},
            "checkpoint": None}]}), {"known"}, 5)


def test_lesson_plan_normalizes_optional_presentation_fields_without_inventing_citations():
    chunk_id = "chunk-verified"
    raw = json.dumps({"segments": [{
        "spoken_text": "Look at this number pattern.",
        "source_chunk_ids": [chunk_id],
    }]})
    result = curriculum._validate_lesson_plan(raw, {chunk_id}, 5)
    segment = result["segments"][0]
    assert segment["id"] == "segment-1"
    assert segment["caption_text"] == segment["spoken_text"]
    assert segment["visual_action"] == {"type": "none", "target": "", "value": ""}
    assert segment["checkpoint"] is None
    assert segment["source_chunk_ids"] == [chunk_id]


def test_lesson_plan_normalizes_numeric_segment_id_without_weakening_citations():
    chunk_id = "chunk-verified"
    raw = json.dumps({"segments": [{
        "id": 1,
        "spoken_text": "Look at the repeating ones.",
        "caption_text": "Look at the repeating ones.",
        "source_chunk_ids": [chunk_id],
        "visual_action": {"type": "none", "target": "", "value": ""},
    }]})
    result = curriculum._validate_lesson_plan(raw, {chunk_id}, 5)
    segment = result["segments"][0]
    assert segment["id"] == "segment-1"
    assert segment["spoken_text"] == "Look at the repeating ones."
    assert segment["source_chunk_ids"] == [chunk_id]

def test_lesson_plan_normalizes_malformed_presentation_metadata_but_keeps_grounding_strict():
    chunk_id = "chunk-verified"
    raw = json.dumps({"segments": [{
        "id": 7,
        "spoken_text": "Look at the repeating ones.",
        "caption_text": 42,
        "source_chunk_ids": [chunk_id],
        "visual_action": {"type": "teleport", "target": 3, "value": ["bad"]},
        "checkpoint": 17,
    }]})
    result = curriculum._validate_lesson_plan(raw, {chunk_id}, 5)
    segment = result["segments"][0]
    assert segment["id"] == "segment-1"
    assert segment["caption_text"] == "Look at the repeating ones."
    assert segment["visual_action"] == {"type": "none", "target": "", "value": ""}
    assert segment["checkpoint"] is None
    assert segment["source_chunk_ids"] == [chunk_id]

def test_lesson_plan_validation_reports_missing_required_field_without_model_input():
    import pytest
    with pytest.raises(curriculum.HTTPException) as captured:
        curriculum._validate_lesson_plan(json.dumps({"segments": [{
            "id": "s1", "spoken_text": "A sourced explanation.",
            "caption_text": "A sourced explanation.",
            "visual_action": {"type": "none", "target": "", "value": ""},
        }]}), {"known"}, 5)
    assert captured.value.status_code == 502
    assert "source_chunk_ids" in captured.value.detail
    assert "fields:" in captured.value.detail


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
    monkeypatch.setattr(curriculum, "ADMIN_TOKEN", "test-admin")
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



def test_lesson_plan_does_not_use_chapter_wide_approved_lesson_for_specific_topic(monkeypatch):
    from contextlib import contextmanager

    approved_row = {
        "id": "chapter-wide-lesson",
        "chapter": "Patterns in Mathematics",
        "topic": "",
        "lesson_json": json.dumps({"chapter_title": "Patterns in Mathematics", "teaching_sequence": []}),
        "source_refs_json": "[]",
    }

    class FakeResult:
        def fetchall(self):
            return [approved_row]

    class FakeConnection:
        def execute(self, query, params=()):
            return FakeResult()

    @contextmanager
    def fake_db():
        yield FakeConnection()

    monkeypatch.setattr(curriculum, "db", fake_db)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {
        "matches": [], "warning": None
    })
    client = TestClient(curriculum.app)
    response = client.post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "app_language": "English",
        "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach me All 1s",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    # Fail closed when only a chapter-wide approved lesson exists.
    assert body.get("provider") != "approved_chapter_lesson"
    assert body["grounded"] is False
    assert body["segments"] == []
    assert "no lesson was generated" in body["warning"].lower()


def test_chapter_lesson_admin_routes_fail_closed_without_token(monkeypatch, tmp_path):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "chapter-lessons-auth.sqlite3")
    monkeypatch.setenv("PADIPPUPAL_ADMIN_TOKEN", "")
    monkeypatch.setattr(curriculum, "ADMIN_TOKEN", "")
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



def test_lesson_plan_prefers_exact_approved_chapter_lesson(monkeypatch):
    from contextlib import contextmanager

    chunk_id = "chunk-verified-1"
    approved_row = {
        "id": "lesson-approved-1",
        "chapter": "Life Processes",
        "topic": "",
        "lesson_json": json.dumps({
            "chapter_title": "Life Processes",
            "overview": "Plants make food using light.",
            "learning_objectives": ["Understand photosynthesis"],
            "teaching_sequence": [{
                "id": "step-1",
                "teacher_says": "Let's look at how a plant makes its food.",
                "caption": "Plants use light to make food.",
                "checkpoint": "What does the plant need?",
                "source_chunk_ids": [chunk_id],
                "visual": {"type": "process", "objects": ["sunlight", "leaf"], "actions": ["reveal"]},
            }],
        }),
        "source_refs_json": json.dumps([{
            "chunk_id": chunk_id, "source_id": "source-1", "title": "Class 6 Science",
            "page_start": 12, "page_end": 13,
        }]),
    }

    class FakeResult:
        def fetchall(self):
            return [approved_row]

    class FakeConnection:
        def execute(self, query, params=()):
            assert "status='approved'" in query
            assert params == ("CBSE", 6, "Science", "English")
            return FakeResult()

    @contextmanager
    def fake_db():
        yield FakeConnection()

    monkeypatch.setattr(curriculum, "db", fake_db)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: (_ for _ in ()).throw(
        AssertionError("approved lesson should bypass fresh retrieval")))
    client = TestClient(curriculum.app)
    response = client.post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Science",
        "medium": "English", "app_language": "Tanglish",
        "chapter": "Life Processes", "message": "Continue the lesson",
        "max_segments": 5,
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["provider"] == "approved_chapter_lesson"
    assert body["lesson_id"] == "lesson-approved-1"
    assert body["chapter_overview"] == "Plants make food using light."
    assert body["segments"][0]["source_chunk_ids"] == [chunk_id]
    assert body["segments"][0]["visual_action"]["type"] == "reveal"
    assert body["segments"][0]["checkpoint"] == "What does the plant need?"


def test_lesson_plan_uses_exact_textbook_excerpt_when_gemini_fails(monkeypatch):
    from urllib.error import HTTPError

    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    chunk_id = "all-ones-source"
    passage = "The All 1s pattern repeats the number 1: 1, 1, 1, 1."

    def fail_gemini(request, timeout):
        raise HTTPError(request.full_url, 503, "temporarily unavailable", {}, None)

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fail_gemini)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [{
        "text": passage,
        "source": {"chunk_id": chunk_id, "source_id": "source-1",
                   "title": "Class 6 Mathematics", "board": "CBSE", "class_level": 6,
                   "subject": "Mathematics", "medium": "English", "page_start": 1, "page_end": 1},
    }]})

    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "app_language": "English",
        "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach me All 1s",
    })

    # A one-sentence excerpt is source-grounded but not a complete lesson.
    # Do not silently present it as if the selected topic has been taught.
    assert response.status_code == 503, response.text
    assert "no safe textbook fallback" in response.json()["detail"].lower()

def test_lesson_plan_does_not_fallback_to_off_topic_textbook_excerpt(monkeypatch):
    """A provider outage must not bypass topic validation through the excerpt fallback."""
    from urllib.error import HTTPError

    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    chunk_id = "unrelated-sequence-source"
    passage = "Some important examples of number sequences include square numbers and counting numbers."

    def fail_gemini(request, timeout):
        raise HTTPError(request.full_url, 503, "temporarily unavailable", {}, None)

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fail_gemini)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [{
        "text": passage,
        "source": {"chunk_id": chunk_id, "source_id": "source-1",
                   "title": "Class 6 Mathematics", "board": "CBSE", "class_level": 6,
                   "subject": "Mathematics", "medium": "English", "page_start": 1, "page_end": 1},
    }]})

    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "app_language": "English",
        "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach me All 1s",
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grounded"] is False
    assert body["segments"] == []
    assert "no lesson was generated" in body["warning"].lower()


def test_approved_topic_lesson_rejects_off_topic_steps_before_returning(monkeypatch):
    """An approved label/source must not let a wrong teaching sequence bypass topic validation."""
    from contextlib import contextmanager

    chunk_id = "approved-all-ones-source"
    approved_row = {
        "id": "approved-all-ones",
        "chapter": "Patterns in Mathematics",
        "topic": "All 1s",
        "lesson_json": json.dumps({
            "chapter_title": "Patterns in Mathematics",
            "overview": "All 1s repeats the number one.",
            "teaching_sequence": [{
                "id": "wrong-step",
                "teacher_says": "Now count up and down to make square numbers.",
                "caption": "Count up and down to make square numbers.",
                "checkpoint": None,
                "source_chunk_ids": [chunk_id],
                "visual": {"type": "number_pattern", "objects": ["1", "2", "3"], "actions": ["reveal"]},
            }],
        }),
        "source_refs_json": json.dumps([{
            "chunk_id": chunk_id, "source_id": "source-1", "title": "Class 6 Mathematics",
            "page_start": 1, "page_end": 2,
        }]),
    }

    class FakeResult:
        def fetchall(self):
            return [approved_row]

    class FakeConnection:
        def execute(self, query, params=()):
            return FakeResult()

    @contextmanager
    def fake_db():
        yield FakeConnection()

    monkeypatch.setattr(curriculum, "db", fake_db)
    monkeypatch.setattr(curriculum, "retrieve", lambda payload: {"matches": [], "warning": None})
    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "app_language": "English",
        "chapter": "Patterns in Mathematics", "topic": "All 1s",
        "message": "Teach me All 1s",
    })

    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("provider") != "approved_chapter_lesson"
    assert body["grounded"] is False
    assert body["segments"] == []
    assert "no lesson was generated" in body["warning"].lower()



def test_all_ones_visual_label_cannot_mask_generic_spoken_segment():
    """Topic labels in visuals must not make unrelated spoken teaching pass validation."""
    generic = {
        "spoken_text": "Mathematics is the search for patterns and explanations.",
        "caption_text": "Mathematics is the search for patterns and explanations.",
        "visual_action": {"type": "highlight", "target": "All 1s", "value": ""},
    }
    assert curriculum._lesson_segments_match_topic("All 1s", [generic]) is False



def test_all_ones_lesson_allows_supporting_explanation_without_repeated_keyword():
    segments = [
        {"spoken_text": "The sequence is 1, 1, 1, 1, 1.", "caption_text": ""},
        {"spoken_text": "The value stays the same each time; the rule is to repeat one.", "caption_text": ""},
        {"spoken_text": "A pattern can repeat without increasing or decreasing.", "caption_text": ""},
    ]
    assert curriculum._lesson_segments_match_topic("All 1s", segments)


def test_all_ones_lesson_completeness_requires_four_segments_and_topic_coverage():
    short = [
        {"spoken_text": "The All 1s pattern repeats the number 1: 1, 1, 1.", "caption_text": ""},
        {"spoken_text": "Each term stays the same.", "caption_text": ""},
        {"spoken_text": "The pattern repeats.", "caption_text": ""},
    ]
    assert not curriculum._lesson_meets_completeness_bar("All 1s", short)

    complete = [
        {"spoken_text": "The All 1s sequence is 1, 1, 1, 1, 1.", "caption_text": ""},
        {"spoken_text": "Every term stays the same because we repeat one.", "caption_text": ""},
        {"spoken_text": "Unlike 1, 2, 3, 4, this sequence does not increase.", "caption_text": ""},
        {"spoken_text": "For example, try adding one more term and notice the rule.", "caption_text": ""},
    ]
    assert curriculum._lesson_meets_completeness_bar("All 1s", complete)


def test_generic_topic_completeness_gate_does_not_change_existing_lesson_contract():
    assert curriculum._lesson_meets_completeness_bar("Magnet poles", [
        {"spoken_text": "A magnet has two poles."}
    ])


def test_all_ones_lesson_rejects_off_topic_segment_even_when_other_steps_match():
    segments = [
        {"spoken_text": "The sequence is 1, 1, 1, 1, 1.", "caption_text": ""},
        {"spoken_text": "Square numbers grow as 1, 4, 9.", "caption_text": ""},
    ]
    assert not curriculum._lesson_segments_match_topic("All 1s", segments)


def test_all_ones_lesson_requires_topic_relevance_somewhere_in_speech():
    segments = [
        {"spoken_text": "Look carefully at the sequence.", "caption_text": ""},
        {"spoken_text": "Now try the next step.", "caption_text": ""},
        {"spoken_text": "Tell me what you notice.", "caption_text": ""},
    ]
    assert not curriculum._lesson_segments_match_topic("All 1s", segments)
