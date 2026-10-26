from pathlib import Path

import pytest

from syllabus_synthesis import (
    CurriculumScope,
    SyllabusTopic,
    build_synthesis_prompt,
    map_topics_to_pages,
    slug,
    run_iterative_synthesis,
)


def scope(**overrides):
    values = {
        "board": "Tamil Nadu State Board",
        "academic_year": "2026-27",
        "medium": "Tamil",
        "standard": "6",
        "subject": "Science",
        "textbook_title": "Science Textbook",
        "edition": "2026",
        "source_authority": "Tamil Nadu Textbook Corporation",
        "rights_reviewed": True,
        "rights_note": "Approved by rights reviewer for internal processing",
    }
    values.update(overrides)
    return CurriculumScope(**values)


def test_scope_keeps_board_year_medium_standard_and_edition_distinct():
    item = scope(board="CBSE", medium="English", standard="10", edition="2025")
    assert item.board == "CBSE"
    assert item.academic_year == "2026-27"
    assert item.medium == "English"
    assert item.standard == "10"
    assert item.edition == "2025"


def test_slug_is_safe_for_hierarchy_paths():
    assert slug("../../CBSE / Class 6") == "cbse-class-6"
    assert slug("தமிழ்") == "unknown"


def test_topic_mapping_returns_page_evidence_and_flags_gaps():
    topics = [
        SyllabusTopic(id="photosynthesis", title="Photosynthesis", keywords=["chlorophyll"]),
        SyllabusTopic(id="unknown", title="Plate tectonics"),
    ]
    pages = [
        {"page": 1, "text": "Plants use chlorophyll for photosynthesis.", "needs_ocr": False},
        {"page": 2, "text": "A second unrelated page.", "needs_ocr": False},
    ]
    mapped = map_topics_to_pages(topics, pages)
    assert mapped[0]["coverage_status"] == "evidence_found"
    assert mapped[0]["page_matches"][0]["page"] == 1
    assert mapped[0]["page_matches"][0]["matched_terms"] == ["chlorophyll", "photosynthesis"]
    assert mapped[0]["synthesis_status"] == "needs_review"
    assert mapped[1]["coverage_status"] == "missing_source"
    assert mapped[1]["page_matches"] == []


def test_prompt_is_source_grounded_and_discloses_missing_evidence():
    package = {"topic_title": "Fractions", "chapter": "Numbers", "page_matches": []}
    prompt = build_synthesis_prompt(scope(), package)
    assert "Do not invent page references" in prompt
    assert "No matching source evidence was found." in prompt
    assert "needs_review" in prompt


def test_ingestion_requires_rights_review(tmp_path: Path):
    from syllabus_synthesis import create_source_package

    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"not a pdf")
    with pytest.raises(PermissionError):
        create_source_package(
            pdf,
            scope(rights_reviewed=False, rights_note=""),
            [SyllabusTopic(id="topic", title="Topic")],
            tmp_path / "out",
        )


def test_upload_endpoint_is_admin_only(monkeypatch):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from syllabus_synthesis import router

    monkeypatch.delenv("PADIPPUPAL_ADMIN_TOKEN", raising=False)
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).post(
        "/admin/syllabus/ingest-pdf",
        data={"metadata_json": "{}", "syllabus_json": "[]"},
        files={"file": ("textbook.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 401



def test_iterative_synthesis_refines_then_passes_page_citation_gate():
    calls = []

    def model(prompt):
        calls.append(prompt)
        if len(calls) == 1:
            return {"explanation": "Plants make food."}
        return {
            "explanation": "Plants use light energy to make food.",
            "key_points": ["Chlorophyll captures light."],
            "worked_examples": ["A plant near a window receives light."],
            "misconceptions": ["Plants get all their food from soil."],
            "understanding_checks": ["What does chlorophyll do?", "Why is light needed?"],
            "source_citations": [{"page": 1, "claim": "Chlorophyll captures light."}],
            "gaps": ["The source excerpt does not explain every chemical step."],
        }

    package = {
        "topic_id": "photosynthesis",
        "topic_title": "Photosynthesis",
        "page_matches": [{"page": 1, "matched_terms": ["photosynthesis"], "evidence_excerpt": "Chlorophyll captures light."}],
    }
    result = run_iterative_synthesis(scope(), package, model, max_rounds=3)
    assert len(calls) == 2
    assert "PREVIOUS DRAFT" in calls[1]
    assert result["status"] == "ready_for_review"
    assert result["approved"] is False
    assert result["synthesis"]["source_citations"][0]["page"] == 1


def test_iterative_synthesis_rejects_citations_outside_evidence():
    def model(prompt):
        return {
            "explanation": "A concept.",
            "key_points": ["Point"],
            "worked_examples": ["Example"],
            "misconceptions": ["Misconception"],
            "understanding_checks": ["Q1", "Q2"],
            "source_citations": [{"page": 99, "claim": "Claim"}],
            "gaps": ["None known"],
        }

    result = run_iterative_synthesis(
        scope(),
        {"topic_id": "topic", "topic_title": "Topic", "page_matches": [{"page": 1, "matched_terms": ["topic"], "evidence_excerpt": "Topic text"}]},
        model,
        max_rounds=2,
    )
    assert result["status"] == "needs_review"
    assert any("citation_page_not_in_evidence:99" in issue for issue in result["issues"])
    assert result["approved"] is False


def test_iterative_synthesis_blocks_topics_without_evidence():
    called = False

    def model(prompt):
        nonlocal called
        called = True
        return {}

    result = run_iterative_synthesis(
        scope(), {"topic_id": "missing", "topic_title": "Missing", "page_matches": []}, model
    )
    assert result["status"] == "blocked_missing_evidence"
    assert not called


def test_synthesis_round_limit_is_bounded():
    with pytest.raises(ValueError):
        run_iterative_synthesis(scope(), {"page_matches": [{"page": 1}]}, lambda _: {}, max_rounds=99)



def test_existing_class6_science_math_topics_can_seed_mapping():
    from syllabus_synthesis import load_existing_topic_seeds

    science = load_existing_topic_seeds(scope(board="CBSE", standard="6", subject="Science", medium="English"))
    maths = load_existing_topic_seeds(scope(board="CBSE", standard="6", subject="Mathematics", medium="English"))
    assert science
    assert maths
    assert all(item["id"] and item["title"] and item["chapter"] for item in science + maths)
    assert load_existing_topic_seeds(scope(board="Tamil Nadu State Board", subject="Science")) == []


def test_source_and_synthesis_rounds_persist_in_existing_curriculum_db(tmp_path, monkeypatch):
    import json
    import sqlite3
    from syllabus_synthesis import _persist_source_package, _persist_synthesis_result

    monkeypatch.setenv("PADIPPUPAL_DB", str(tmp_path / "padippupal_curriculum.sqlite3"))
    manifest = {
        "source_id": "a1b2c3d4e5f60708",
        "scope": scope().model_dump(),
        "source_sha256": "source-hash",
        "page_count": 1,
        "overall_status": "needs_review",
        "images": [{"id": "p1-i1", "page": 1, "path": "images/a.png", "review_status": "needs_topic_match"}],
        "topics": [{
            "topic_id": "photosynthesis", "topic_title": "Photosynthesis", "chapter": "Plants",
            "syllabus_reference": "Chapter 1", "coverage_status": "evidence_found",
            "page_matches": [{"page": 1, "matched_terms": ["photosynthesis"], "evidence_excerpt": "Plant text"}],
            "synthesis_status": "needs_review",
        }],
    }
    _persist_source_package(manifest, [{"page": 1, "text": "Plant text", "needs_ocr": False}])
    result = {
        "topic_id": "photosynthesis", "status": "ready_for_review",
        "rounds": [{"round": 1, "draft": {"explanation": "Original explanation"}, "validation_issues": []}],
        "synthesis": {"explanation": "Original explanation"}, "issues": [], "approved": False,
    }
    _persist_synthesis_result(manifest["source_id"], "photosynthesis", result)

    conn = sqlite3.connect(tmp_path / "padippupal_curriculum.sqlite3")
    try:
        source = conn.execute("SELECT board, standard, subject, textbook_title FROM syllabus_sources").fetchone()
        page = conn.execute("SELECT page_no, page_text FROM syllabus_source_pages").fetchone()
        topic = conn.execute("SELECT chapter, topic_title, coverage_status FROM syllabus_topics").fetchone()
        rounds = conn.execute("SELECT round_no, draft_json FROM syllabus_synthesis_rounds").fetchall()
        synthesis = conn.execute("SELECT latest_status, approved, synthesis_json FROM syllabus_topic_syntheses").fetchone()
        image_count = conn.execute("SELECT COUNT(*) FROM syllabus_source_images").fetchone()[0]
    finally:
        conn.close()

    assert source == ("Tamil Nadu State Board", "6", "Science", "Science Textbook")
    assert page == (1, "Plant text")
    assert topic == ("Plants", "Photosynthesis", "evidence_found")
    assert len(rounds) == 1 and json.loads(rounds[0][1])["explanation"] == "Original explanation"
    assert synthesis[0] == "ready_for_review" and synthesis[1] == 0
    assert json.loads(synthesis[2])["explanation"] == "Original explanation"
    assert image_count == 1



def test_existing_curriculum_book_is_reused_without_pdf_reupload(tmp_path, monkeypatch):
    import sqlite3
    from syllabus_synthesis import create_package_from_existing_source

    db_path = tmp_path / "existing.sqlite3"
    monkeypatch.setenv("PADIPPUPAL_DB", str(db_path))
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE sources (
            id TEXT PRIMARY KEY, board TEXT, academic_year TEXT, class_level INTEGER,
            subject TEXT, medium TEXT, term TEXT, edition TEXT, title TEXT, source_url TEXT,
            license_note TEXT, sha256 TEXT, status TEXT, page_count INTEGER, created_at REAL
        );
        CREATE TABLE source_content (source_id TEXT PRIMARY KEY, content TEXT);
        CREATE TABLE chunks (
            id TEXT PRIMARY KEY, source_id TEXT, chunk_no INTEGER, chapter TEXT,
            page_start INTEGER, page_end INTEGER, text TEXT
        );
    """)
    conn.execute(
        "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("existing-science-1", "CBSE", "2026-27", 6, "Science", "English", "", "2026",
         "Science Textbook", "https://ncert.nic.in/textbook.php", "Internal review note",
         "sha-existing", "ready", 1, 1.0),
    )
    conn.execute(
        "INSERT INTO source_content VALUES (?, ?)",
        ("existing-science-1", "[Page 1] Plants use chlorophyll for photosynthesis and make food using light."),
    )
    conn.execute(
        "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("chunk1", "existing-science-1", 0, "", 1, 1, "Plants use chlorophyll for photosynthesis and make food using light."),
    )
    conn.commit()
    conn.close()

    result = create_package_from_existing_source(
        "existing-science-1",
        [SyllabusTopic(id="photosynthesis", title="Photosynthesis", keywords=["chlorophyll"])],
        tmp_path / "syllabus-library",
    )
    manifest = result["manifest"]
    assert manifest["source_storage"] == "existing_curriculum_database"
    assert manifest["existing_curriculum_source_id"] == "existing-science-1"
    assert manifest["topics"][0]["coverage_status"] == "evidence_found"
    assert manifest["scope"]["rights_reviewed"] is False
    assert (Path(result["package_path"]) / "pages" / "page-0001.txt").exists()
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM syllabus_sources").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM syllabus_source_pages").fetchone()[0] == 1
    finally:
        conn.close()
