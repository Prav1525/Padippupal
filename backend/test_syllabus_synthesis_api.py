import json
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

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

    return FakeResponse()


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
        conn.execute(
            """INSERT INTO chunks (id,source_id,chunk_no,chapter,page_start,page_end,text)
               VALUES (?,?,?,?,?,?,?)""",
            ("chunk-test", source_id, 0, "Test chapter", 1, 1, "Textbook evidence for the key idea."),
        )

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    captured = {}
    def fake_urlopen(request, *_args, **_kwargs):
        captured["request"] = json.loads(request.data.decode("utf-8"))
        return _fake_gemini_response()
    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
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
    # Synthesis and visual generation are one pipeline: every saved synthesis
    # round immediately attempts source-cited visual generation. Candidates stay
    # inactive until a reviewer approves the lesson.
    assert data["visual_candidates_generated"] >= 1
    assert data["visual_candidates_active"] == 0
    synthesis_prompt = captured["request"]["systemInstruction"]["parts"][0]["text"]
    assert "copyright-respectful" in synthesis_prompt
    assert "reference_page_numbers" in synthesis_prompt
    assert "Never trace" in synthesis_prompt

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
    with curriculum.db() as conn:
        generated_assets = conn.execute(
            "SELECT topic, step_id, source_chunk_ids_json, active, blueprint_json "
            "FROM tutor_topic_visual_assets WHERE chapter=?",
            ("Test chapter",),
        ).fetchall()
    assert len(generated_assets) >= 1
    assert all(row["active"] == 0 for row in generated_assets)
    assert all(json.loads(row["source_chunk_ids_json"]) == ["chunk-test"] for row in generated_assets)
    assert topics[0]["page_start"] == 1
    assert topics[0]["page_end"] == 1
    # Do not copy chapter-wide objectives into every topic when the model omitted step-level objectives.
    assert json.loads(topics[0]["learning_objectives_json"]) == []
    assert "left empty rather than copying chapter-wide objectives" in json.loads(topics[0]["validation_notes_json"])[1]

    listed = client.get(
        "/admin/syllabus-synthesis/rounds",
        headers={"X-Admin-Token": "test-token"},
        params={"board": "CBSE", "class_level": 6, "subject": "Science"},
    )
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    detail = client.get(
        f"/admin/syllabus-synthesis/rounds/{data['synthesis_round_id']}",
        headers={"X-Admin-Token": "test-token"},
    )
    assert detail.status_code == 200
    assert detail.json()["topics"][0]["citation_refs"] == ["chunk-test"]

    # Regression: a legacy admin client incorrectly serialized the ID object
    # into the URL path instead of sending the scalar identifier.
    malformed_round_path = quote(json.dumps({"round_id": data["synthesis_round_id"]}))
    legacy_round_detail = client.get(
        f"/admin/syllabus-synthesis/rounds/{malformed_round_path}",
        headers={"X-Admin-Token": "test-token"},
    )
    assert legacy_round_detail.status_code == 200, legacy_round_detail.text

    lesson_id = data["lesson_id"]
    malformed_lesson_path = quote(json.dumps({"lesson_id": lesson_id}))
    legacy_lesson_detail = client.get(
        f"/admin/chapter-lessons/{malformed_lesson_path}",
        headers={"X-Admin-Token": "test-token"},
    )
    assert legacy_lesson_detail.status_code == 200, legacy_lesson_detail.text
    assert legacy_lesson_detail.json()["id"] == lesson_id

    # The tutor serves approved chapter_lessons; synthesis review state must follow
    # the same explicit human decision instead of remaining misleadingly "draft".
    reviewed = client.post(
        f"/admin/chapter-lessons/{lesson_id}/review",
        headers={"X-Admin-Token": "test-token"},
        json={"decision": "approve", "feedback": "Source citations checked."},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "approved"
    with curriculum.db() as conn:
        round_row = conn.execute(
            "SELECT status FROM syllabus_synthesis_rounds WHERE id=?",
            (data["synthesis_round_id"],),
        ).fetchone()
        topic_row = conn.execute(
            "SELECT approval_status FROM syllabus_topic_syntheses WHERE round_id=?",
            (data["synthesis_round_id"],),
        ).fetchone()
    assert round_row["status"] == "approved"
    assert topic_row["approval_status"] == "approved"

    # Re-running unchanged evidence must reuse the approved lesson and preserve
    # approval instead of adding duplicate lesson rows or demoting the round.
    retry = client.post(
        "/admin/chapter-lessons/generate",
        headers={"X-Admin-Token": "test-token"},
        json={"board": "CBSE", "class_level": 6, "subject": "Science",
              "medium": "English", "chapter": "Test chapter"},
    )
    assert retry.status_code == 200, retry.text
    assert retry.json()["lesson_id"] == lesson_id
    assert retry.json()["status"] == "approved"
    assert retry.json()["reused_existing"] is True
    with curriculum.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM chapter_lessons WHERE board='CBSE' AND chapter='Test chapter'"
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT status FROM syllabus_synthesis_rounds WHERE id=?",
            (data["synthesis_round_id"],),
        ).fetchone()["status"] == "approved"


def test_science_maths_coverage_audit_requires_current_evidence_and_approval():
    curriculum.DB_PATH = Path(tempfile.mkstemp(suffix=".sqlite3")[1])
    curriculum.ADMIN_TOKEN = "coverage-test-token"
    curriculum.init_db()
    source_id = "coverage-test-source"
    chunk_id = "coverage-chunk-1"
    chapter = "Chapter A"
    source_text = "Evidence explaining the chapter's central concept."
    now = time.time()
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO sources
            (id,board,academic_year,class_level,subject,medium,term,edition,title,source_url,
             license_note,sha256,status,page_count,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (source_id, "CBSE", "2026-27", 6, "Science", "English", "", "2026",
             "Official Science test book", "", "Test fixture", "coverage-test-sha",
             "ready", 2, now),
        )
        conn.execute(
            "INSERT INTO chunks (id,source_id,chunk_no,chapter,page_start,page_end,text) VALUES (?,?,?,?,?,?,?)",
            (chunk_id, source_id, 0, chapter, 1, 2, source_text),
        )

    evidence = curriculum.build_evidence_packet([
        curriculum.EvidenceChunk(chunk_id, source_id, chapter, 0, 1, 2, source_text)
    ])
    round_id = "coverage-round-1"
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO syllabus_synthesis_rounds
            (id,source_id,board,class_level,subject,chapter,curriculum_version,status,model,
             prompt_version,source_chunk_ids_json,evidence_fingerprint,validation_json,error_message,
             created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,'approved',?,?,?,?,?,'',?,?)""",
            (round_id, source_id, "CBSE", 6, "Science", chapter, "v1", "test-model", "v1",
             json.dumps([chunk_id]), evidence["evidence_fingerprint"], json.dumps({"valid": True, "source_chunk_count": 1, "cited_chunk_count": 1, "uncited_chunk_count": 0}), now, now),
        )
        conn.execute(
            """INSERT INTO syllabus_topic_syntheses
            (id,round_id,source_id,topic,page_start,page_end,learning_objectives_json,
             explanation_json,examples_json,practice_questions_json,citation_refs_json,
             validation_status,validation_notes_json,approval_status,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("coverage-topic-1", round_id, source_id, "Central concept", 1, 2,
             json.dumps(["Explain the central concept"]), json.dumps({"teacher_says": "Let's explore it"}),
             json.dumps(["Source-supported example"]), json.dumps(["Explain in your own words"]),
             json.dumps([chunk_id]), "passed", json.dumps(["Citations checked"]), "approved", now, now),
        )
        conn.execute(
            """INSERT INTO chapter_lessons
            (id,board,class_level,subject,medium,chapter,topic,status,lesson_json,source_refs_json,
             model,review_feedback,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,'approved',?,?,?,?,?,?)""",
            ("coverage-lesson-1", "CBSE", 6, "Science", "English", chapter, "",
             json.dumps({"chapter_title": chapter}), json.dumps([{"chunk_id": chunk_id}]),
             "test-model", "Reviewed against textbook", now, now),
        )

    client = TestClient(curriculum.app)
    headers = {"X-Admin-Token": "coverage-test-token"}
    response = client.get("/admin/syllabus-synthesis/coverage", headers=headers,
                          params={"board": "CBSE", "class_level": 6, "medium": "English"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["source_count"] == 1
    assert data["chapter_count"] == 1
    chapter_report = data["sources"][0]["chapters"][0]
    assert chapter_report["coverage_status"] == "complete"
    assert chapter_report["evidence_current"] is True
    assert chapter_report["validation_passed"] is True
    assert chapter_report["approved_tutor_lesson"] is True

    # A source that is still processing must never be reported as complete.
    with curriculum.db() as conn:
        conn.execute("UPDATE sources SET status='processing' WHERE id=?", (source_id,))
    not_ready = client.get("/admin/syllabus-synthesis/coverage", headers=headers,
                           params={"board": "CBSE", "class_level": 6, "medium": "English"})
    assert not_ready.status_code == 200, not_ready.text
    assert not_ready.json()["sources"][0]["chapters"][0]["coverage_status"] == "source_not_ready"
    with curriculum.db() as conn:
        conn.execute("UPDATE sources SET status='ready' WHERE id=?", (source_id,))

    # Editing extracted text without changing the chunk ID must invalidate the coverage result.
    with curriculum.db() as conn:
        conn.execute("UPDATE chunks SET text=? WHERE id=?", ("Changed textbook evidence.", chunk_id))
    stale = client.get("/admin/syllabus-synthesis/coverage", headers=headers,
                       params={"board": "CBSE", "class_level": 6, "medium": "English"})
    assert stale.status_code == 200, stale.text
    assert stale.json()["sources"][0]["chapters"][0]["coverage_status"] == "stale_evidence"

    # Missing textbook pages must block "complete" even when the remaining chunk,
    # synthesis, citations, and approval records are otherwise valid.
    with curriculum.db() as conn:
        conn.execute("UPDATE chunks SET text=?,page_start=1,page_end=1 WHERE id=?",
                     (source_text, chunk_id))
        refreshed = curriculum.build_evidence_packet([
            curriculum.EvidenceChunk(chunk_id, source_id, chapter, 0, 1, 1, source_text)
        ])
        conn.execute(
            "UPDATE syllabus_synthesis_rounds SET source_chunk_ids_json=?,evidence_fingerprint=? WHERE id=?",
            (json.dumps([chunk_id]), refreshed["evidence_fingerprint"], round_id),
        )
    incomplete = client.get("/admin/syllabus-synthesis/coverage", headers=headers,
                            params={"board": "CBSE", "class_level": 6, "medium": "English"})
    assert incomplete.status_code == 200, incomplete.text
    incomplete_source = incomplete.json()["sources"][0]
    assert incomplete_source["page_coverage_complete"] is False
    assert incomplete_source["missing_page_numbers"] == [2]
    assert incomplete_source["inventory_status"] == "incomplete_page_extraction"
    assert incomplete_source["chapters"][0]["coverage_status"] == "source_page_coverage_incomplete"


def test_batch_synthesis_inventory_is_read_only_bounded_and_source_specific(monkeypatch):
    curriculum.DB_PATH = Path(tempfile.mkstemp(suffix=".sqlite3")[1])
    curriculum.ADMIN_TOKEN = "batch-test-token"
    curriculum.init_db()
    now = time.time()
    sources = [
        ("batch-source-a", "Official Science book A", "Science", "ready"),
        ("batch-source-b", "Official Science book B", "Science", "ready"),
        ("batch-source-processing", "Processing Science book", "Science", "processing"),
    ]
    with curriculum.db() as conn:
        for source_id, title, subject, status in sources:
            conn.execute(
                """INSERT INTO sources
                (id,board,academic_year,class_level,subject,medium,term,edition,title,source_url,
                 license_note,sha256,status,page_count,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (source_id, "CBSE", "2026-27", 6, subject, "English", "", "2026",
                 title, "", "Test fixture", source_id + "-sha", status, 4, now),
            )
        for source_id, chapter, chunk_no in (
            ("batch-source-a", "Chapter One", 0),
            ("batch-source-a", "Chapter Two", 1),
            ("batch-source-b", "Chapter One", 0),
            ("batch-source-processing", "Hidden Chapter", 0),
        ):
            conn.execute(
                """INSERT INTO chunks
                (id,source_id,chunk_no,chapter,page_start,page_end,text)
                VALUES (?,?,?,?,?,?,?)""",
                (source_id + "-" + str(chunk_no), source_id, chunk_no, chapter,
                 chunk_no + 1, chunk_no + 1, "Textbook evidence for " + chapter),
            )

    client = TestClient(curriculum.app)
    headers = {"X-Admin-Token": "batch-test-token"}
    preview = client.post("/admin/syllabus-synthesis/batch", headers=headers, json={
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
        "max_chapters": 10,
    })
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["mode"] == "inventory_only"
    assert data["source_count"] == 2
    assert data["available_chapter_count"] == 3
    assert data["draft_count"] == 0
    assert all(item["status"] == "inventory_only" for item in data["results"])
    with curriculum.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM syllabus_synthesis_rounds").fetchone()[0] == 0

    unsafe_generate = client.post("/admin/syllabus-synthesis/batch", headers=headers, json={
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
        "max_chapters": 10, "generate": True,
    })
    assert unsafe_generate.status_code == 400
    assert "explicitly selected source_id" in unsafe_generate.json()["detail"]

    captured = []
    def fake_generate(request):
        captured.append(request)
        return {
            "status": "draft",
            "lesson_id": "draft-" + request.source_id,
            "synthesis_round_id": "round-" + request.source_id,
            "validation": {"valid": True},
        }
    monkeypatch.setattr(curriculum, "generate_chapter_lesson", fake_generate)
    generated = client.post("/admin/syllabus-synthesis/batch", headers=headers, json={
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
        "source_id": "batch-source-b", "max_chapters": 1, "generate": True,
    })
    assert generated.status_code == 200, generated.text
    result = generated.json()
    assert result["mode"] == "generate_drafts"
    assert result["available_chapter_count"] == 1
    assert result["selected_chapter_count"] == 1
    assert result["truncated"] is False
    assert result["draft_count"] == 1
    assert result["failed_count"] == 0
    assert captured[0].source_id == "batch-source-b"
    assert captured[0].chapter == "Chapter One"
