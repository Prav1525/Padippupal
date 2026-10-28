import json
import time

from fastapi.testclient import TestClient

import app as curriculum


def _seed_syntheses(tmp_path, monkeypatch):
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "synthesized-lessons.sqlite3")
    curriculum.init_db()
    now = time.time()
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO sources
            (id,board,academic_year,class_level,subject,medium,term,edition,title,source_url,
             license_note,sha256,status,page_count,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("source-1", "CBSE", "2026-27", 6, "Mathematics", "English", "",
             "2026-27", "Reviewed teaching source", "https://example.org/source",
             "Reviewed source fixture", "synth-test-sha", "ready", 2, now),
        )
        for round_id, chapter, status in (
            ("round-approved", "Patterns in Mathematics", "approved"),
            ("round-draft", "Patterns in Mathematics", "draft"),
            ("round-other-chapter", "Lines and Angles", "approved"),
        ):
            conn.execute(
                """INSERT INTO syllabus_synthesis_rounds
                (id,source_id,board,class_level,subject,chapter,curriculum_version,status,model,
                 prompt_version,source_chunk_ids_json,evidence_fingerprint,validation_json,
                 error_message,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (round_id, "source-1", "CBSE", 6, "Mathematics", chapter, "v-test",
                 status, "test-model", "test-prompt", "[]", "fingerprint-" + round_id,
                 "{}", "", now, now),
            )
        for lesson_id, round_id, topic, approval, validation in (
            ("topic-approved", "round-approved", "Repeating patterns", "approved", "passed"),
            ("topic-draft", "round-draft", "Draft pattern", "approved", "passed"),
            ("topic-unapproved", "round-approved", "Unreviewed topic", "draft", "passed"),
            ("topic-failed", "round-approved", "Failed validation", "approved", "failed"),
            ("topic-other-chapter", "round-other-chapter", "Angles", "approved", "passed"),
        ):
            conn.execute(
                """INSERT INTO syllabus_topic_syntheses
                (id,round_id,source_id,topic,page_start,page_end,learning_objectives_json,
                 explanation_json,examples_json,practice_questions_json,citation_refs_json,
                 validation_status,validation_notes_json,approval_status,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (lesson_id, round_id, "source-1", topic, 1, 2,
                 json.dumps(["Identify the pattern"]),
                 json.dumps({"summary": "A source-checked explanation"}),
                 json.dumps(["A simple example"]), json.dumps(["What repeats?"]),
                 json.dumps(["source-1"]), validation, "[]", approval, now, now),
            )


def test_synthesized_lessons_returns_only_approved_valid_profile_matches(tmp_path, monkeypatch):
    _seed_syntheses(tmp_path, monkeypatch)
    response = TestClient(curriculum.app).get(
        "/curriculum/synthesized-lessons",
        params={
            "board": "CBSE", "class_level": 6, "subject": "Mathematics",
            "medium": "English", "chapter": "Patterns in Mathematics",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "ok"
    assert data["count"] == 1
    assert data["lessons"][0]["id"] == "topic-approved"
    assert data["lessons"][0]["explanation"] == {"summary": "A source-checked explanation"}
    assert data["lessons"][0]["learning_objectives"] == ["Identify the pattern"]


def test_synthesized_lessons_topic_filter_and_empty_profile_are_safe(tmp_path, monkeypatch):
    _seed_syntheses(tmp_path, monkeypatch)
    client = TestClient(curriculum.app)
    params = {
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "medium": "English", "chapter": "Patterns in Mathematics",
        "topic": "Repeating patterns",
    }
    found = client.get("/curriculum/synthesized-lessons", params=params)
    assert found.status_code == 200
    assert [row["id"] for row in found.json()["lessons"]] == ["topic-approved"]

    wrong_profile = client.get(
        "/curriculum/synthesized-lessons",
        params={**params, "medium": "Tamil"},
    )
    assert wrong_profile.status_code == 200
    assert wrong_profile.json()["lessons"] == []
