import json
import time

from fastapi.testclient import TestClient

import app as curriculum


def _seed_approved_lesson(monkeypatch, tmp_path):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "language-lesson.sqlite3")
    curriculum.init_db()
    now = time.time()
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO sources
               (id,board,academic_year,class_level,subject,medium,term,edition,title,source_url,
                license_note,sha256,status,page_count,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("source-1", "CBSE", "2026-27", 6, "Science", "English", "", "2026",
             "Test textbook", "", "Test fixture", "language-test-sha", "ready", 1, now),
        )
        conn.execute(
            "INSERT INTO chunks (id,source_id,chunk_no,chapter,page_start,page_end,text) VALUES (?,?,?,?,?,?,?)",
            ("chunk-1", "source-1", 0, "Test chapter", 1, 1, "The key idea is explained in this textbook passage."),
        )
        lesson = {
            "chapter_title": "Test chapter",
            "overview": "A short overview.",
            "learning_objectives": ["Explain the key idea."],
            "concept_map": [{"concept": "Key idea", "prerequisite": "", "source_chunk_ids": ["chunk-1"]}],
            "teaching_sequence": [{
                "id": "step-1",
                "title": "Key idea",
                "teacher_says": "Let us study the key idea carefully.",
                "caption": "The key idea is explained here.",
                "example": "A source-supported example.",
                "misconception": "",
                "checkpoint": None,
                "source_chunk_ids": ["chunk-1"],
                "visual": {"type": "none", "objects": [], "actions": [], "narration_sync": []},
            }],
        }
        refs = [{"chunk_id": "chunk-1", "source_id": "source-1", "title": "Test textbook",
                 "page_start": 1, "page_end": 1, "chunk_no": 0}]
        conn.execute(
            """INSERT INTO chapter_lessons
               (id,board,class_level,subject,medium,chapter,topic,status,lesson_json,source_refs_json,
                model,review_feedback,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,'approved',?,?,?,?,?,?)""",
            ("lesson-1", "CBSE", 6, "Science", "English", "Test chapter", "Key idea",
             json.dumps(lesson), json.dumps(refs), "test-model", "", now, now),
        )


def _lesson_request():
    return {
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
        "app_language": "Tanglish", "chapter": "Test chapter", "topic": "Key idea",
        "message": "Teach this lesson", "max_segments": 4,
    }


def test_tanglish_selection_translates_approved_lesson_and_caches_variant(monkeypatch, tmp_path):
    _seed_approved_lesson(monkeypatch, tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            payload = {"teaching_sequence": [{
                "id": "step-1",
                "teacher_says": "Namma key idea-a simple-a paakalam. Idhu textbook-la irukkura main concept.",
                "caption": "Ippo key idea-a paakalam.",
            }]}
            return json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]}).encode()

    def fake_urlopen(request, timeout):
        calls.append(json.loads(request.data.decode()))
        return FakeResponse()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    client = TestClient(curriculum.app)
    first = client.post("/tutor/lesson-plan", json=_lesson_request())
    assert first.status_code == 200, first.text
    assert first.json()["provider"] == "approved_chapter_lesson"
    assert first.json()["language"] == "Tanglish"
    assert first.json()["segments"][0]["spoken_text"].startswith("Namma key idea-a")
    assert len(calls) == 1
    prompt = calls[0]["contents"][0]["parts"][0]["text"]
    assert "Never use Tamil script in Tanglish output" in prompt
    with curriculum.db() as conn:
        cached = conn.execute(
            "SELECT language,lesson_json FROM chapter_lesson_language_variants WHERE lesson_id=?",
            ("lesson-1",),
        ).fetchone()
    assert cached["language"] == "Tanglish"
    assert json.loads(cached["lesson_json"])["teaching_sequence"][0]["source_chunk_ids"] == ["chunk-1"]

    def unexpected_translation(*args, **kwargs):
        raise AssertionError("cached Tanglish variant should be reused without another translation request")

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", unexpected_translation)
    second = client.post("/tutor/lesson-plan", json=_lesson_request())
    assert second.status_code == 200, second.text
    assert second.json()["segments"][0]["spoken_text"] == first.json()["segments"][0]["spoken_text"]


def test_tanglish_selection_fails_closed_if_translation_is_invalid(monkeypatch, tmp_path):
    _seed_approved_lesson(monkeypatch, tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            payload = {"teaching_sequence": [{
                "id": "step-1", "teacher_says": "The key idea is very important.",
                "caption": "The key idea is explained here.",
            }]}
            return json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]}).encode()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", lambda request, timeout: FakeResponse())
    response = TestClient(curriculum.app).post("/tutor/lesson-plan", json=_lesson_request())
    assert response.status_code == 502
    assert "failed validation" in response.json()["detail"].lower()
    with curriculum.db() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM chapter_lesson_language_variants").fetchone()["n"]
    assert count == 0
