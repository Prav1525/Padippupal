from pathlib import Path

import pytest

from syllabus_synthesis import (
    CurriculumScope,
    SyllabusTopic,
    build_synthesis_prompt,
    map_topics_to_pages,
    slug,
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
    response = TestClient(app).post(\n        "/admin/syllabus/ingest-pdf",\n        data={"metadata_json": "{}", "syllabus_json": "[]"},\n        files={"file": ("textbook.pdf", b"%PDF-1.4", "application/pdf")},\n    )
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
