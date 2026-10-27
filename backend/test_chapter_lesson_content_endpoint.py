import json
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

import app as curriculum


def _valid_lesson(chunk_id="content-chunk-1"):
    return {
        "chapter_title": "Test chapter",
        "overview": "A source-grounded overview.",
        "learning_objectives": ["Explain the key idea."],
        "concept_map": [{
            "concept": "Key idea",
            "prerequisite": "",
            "source_chunk_ids": [chunk_id],
        }],
        "teaching_sequence": [{
            "id": "step-1",
            "title": "First idea",
            "teacher_says": "Let's study the key idea.",
            "caption": "The textbook introduces this idea.",
            "example": "A source-supported example.",
            "misconception": "Do not confuse the two terms.",
            "checkpoint": "What is the key idea?",
            "source_chunk_ids": [chunk_id],
            "visual": {"type": "none", "objects": [], "actions": [], "narration_sync": []},
        }],
    }


def _seed_draft():
    curriculum.DB_PATH = Path(tempfile.mkstemp(suffix=".sqlite3")[1])
    curriculum.ADMIN_TOKEN = "content-test-token"
    curriculum.init_db()
    now = time.time()
    source_id, chunk_id, lesson_id = "content-source-1", "content-chunk-1", "content-lesson-1"
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO sources
            (id,board,academic_year,class_level,subject,medium,term,edition,title,source_url,
             license_note,sha256,status,page_count,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (source_id, "CBSE", "2026-27", 6, "Science", "English", "", "2026",
             "Official test textbook", "", "Test fixture", "content-test-sha", "ready", 1, now),
        )
        conn.execute(
            """INSERT INTO chunks (id,source_id,chunk_no,chapter,page_start,page_end,text)
               VALUES (?,?,?,?,?,?,?)""",
            (chunk_id, source_id, 0, "Test chapter", 1, 1, "Textbook evidence for the key idea."),
        )
        conn.execute(
            """INSERT INTO chapter_lessons
            (id,board,class_level,subject,medium,chapter,topic,status,lesson_json,source_refs_json,
             model,review_feedback,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,'draft',?,?,?,?,?,?)""",
            (lesson_id, "CBSE", 6, "Science", "English", "Test chapter", "",
             json.dumps(_valid_lesson()), json.dumps([{
                 "chunk_id": chunk_id, "source_id": source_id, "title": "Official test textbook",
                 "page_start": 1, "page_end": 1, "chunk_no": 0,
             }]), "test-model", "", now, now),
        )
    return lesson_id, chunk_id


def test_content_edit_requires_admin_authentication():
    lesson_id, _ = _seed_draft()
    response = TestClient(curriculum.app).put(
        f"/admin/chapter-lessons/{lesson_id}/content",
        json={"lesson": _valid_lesson()},
    )
    assert response.status_code == 401


def test_content_edit_validates_citations_and_keeps_draft_status():
    lesson_id, chunk_id = _seed_draft()
    client = TestClient(curriculum.app)
    headers = {"X-Admin-Token": "content-test-token"}

    invalid = _valid_lesson("invented-chunk")
    rejected = client.put(
        f"/admin/chapter-lessons/{lesson_id}/content",
        headers=headers,
        json={"lesson": invalid, "feedback": "Attempt with unsupported citation."},
    )
    assert rejected.status_code == 422
    with curriculum.db() as conn:
        assert conn.execute("SELECT status FROM chapter_lessons WHERE id=?", (lesson_id,)).fetchone()["status"] == "draft"

    corrected = _valid_lesson(chunk_id)
    saved = client.put(
        f"/admin/chapter-lessons/{lesson_id}/content",
        headers=headers,
        json={"lesson": corrected, "feedback": "Corrected against the source; needs human review."},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["status"] == "draft"
    assert saved.json()["validation"]["valid"] is True
    assert saved.json()["review_required"] is True
    with curriculum.db() as conn:
        row = conn.execute("SELECT status,lesson_json,review_feedback FROM chapter_lessons WHERE id=?", (lesson_id,)).fetchone()
    assert row["status"] == "draft"
    assert json.loads(row["lesson_json"])["teaching_sequence"][0]["source_chunk_ids"] == [chunk_id]
    assert "human review" in row["review_feedback"]


def test_content_edit_cannot_modify_approved_lesson():
    lesson_id, chunk_id = _seed_draft()
    with curriculum.db() as conn:
        conn.execute("UPDATE chapter_lessons SET status='approved' WHERE id=?", (lesson_id,))
    response = TestClient(curriculum.app).put(
        f"/admin/chapter-lessons/{lesson_id}/content",
        headers={"X-Admin-Token": "content-test-token"},
        json={"lesson": _valid_lesson(chunk_id)},
    )
    assert response.status_code == 409
    with curriculum.db() as conn:
        assert conn.execute("SELECT status FROM chapter_lessons WHERE id=?", (lesson_id,)).fetchone()["status"] == "approved"
