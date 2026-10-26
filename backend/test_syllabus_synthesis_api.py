import json
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

import app as curriculum


def _fake_gemini_response():
    lesson = {
        "chapter_title": "Test chapter",
        "overview": "A short source-grounded overview.",
        "learning_objectives": ["Describe the key idea."],
        "concept_map": [{
            "concept": "Key idea",
            "prerequisite": "",
            "source_chunk_ids": ["chunk-test"],
        }],
        "teaching_sequence": [{
            "id": "step-1",
            "title": "First idea",
            "teacher_says": "Let's study the key idea.",
            "caption": "The textbook introduces this idea.",
            "example": "A source-supported example.",
            "misconception": "Do not confuse the two terms.",
            "checkpoint": "What is the key idea?",
            "source_chunk_ids": ["chunk-test"],
            "visual": {"type": "none", "objects": [], "actions": [], "narration_sync": []},
        }],
    }
    response_body = {
        "candidates": [{
            "content": {"parts": [{"text": json.dumps(lesson)}]}
        }]
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(response_body).encode("utf-8")

    return FakeResponse


def test_chapter_generation_persists_traceable_synthesis_round(monkeypatch):
    curriculum.DB_PATH = Path(tempfile.mkstemp(suffix=".sqlite3")[1])
    curriculum.ADMIN_TOKEN = "test-token"
    curriculum.init_db()
    source_id = "synthesis-test-source"
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO sources
            (id,board,academic_year,class_level,subject,medium,term,edition,title,source_url,
             license_note,sha256,status,page_count,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (source_id, "CBSE", "2026-27", 6, "Science", "English", "", "2026",
             "Test official textbook", "", "Approved test fixture", "synthesis-test-sha",
             "ready", 1, time.time()),
        )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(curriculum.urllib.request, "urlopen", lambda *_args, **_kwargs: _fake_gemini_response())
    monkeypatch.setattr(curriculum, "_chapter_source_chunks", lambda _payload: [{
        "chunk_id": "chunk-test", "chunk_no": 0, "chunk_chapter": "Test chapter",
        "page_start": 1, "page_end": 1, "text": "Textbook evidence for the key idea.",
        "source_id": source_id, "title": "Test official textbook",
        "academic_year": "2026-27", "edition": "2026",
    }])

    client = TestClient(curriculum.app)
    response = client.post(
        "/admin/chapter-lessons/generate",
        headers={"X-Admin-Token": "test-token"},
        json={"board": "CBSE", "class_level": 6, "subject": "Science",
              "medium": "English", "chapter": "Test chapter"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "draft"
    assert data["synthesis_round_id"]
    assert len(data["evidence_fingerprint"]) == 64
    assert data["validation"]["valid"] is True

    with curriculum.db() as conn:
        rounds = conn.execute(
            "SELECT * FROM syllabus_synthesis_rounds WHERE id=?",
            (data["synthesis_round_id"],),
        ).fetchall()
        topics = conn.execute(
            "SELECT * FROM syllabus_topic_syntheses WHERE round_id=?",
            (data["synthesis_round_id"],),
        ).fetchall()
    assert len(rounds) == 1
    assert rounds[0]["status"] == "draft"
    assert json.loads(rounds[0]["source_chunk_ids_json"]) == ["chunk-test"]
    assert len(topics) == 1
    assert topics[0]["validation_status"] == "passed"
    assert topics[0]["approval_status"] == "draft"
    assert json.loads(topics[0]["citation_refs_json"]) == ["chunk-test"]
