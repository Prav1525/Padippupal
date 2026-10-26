import json
from pathlib import Path

import pytest

from teaching_engine import (
    build_teacher_instructions,
    find_chapter,
    load_teaching_dataset,
    mastery_decision,
)


def test_class6_dataset_has_both_subjects_and_stable_topics():
    data = load_teaching_dataset()
    subjects = {chapter["subject"] for chapter in data["chapters"]}
    assert subjects == {"Science", "Mathematics"}
    assert data["completeness"]["status"] == "starter_scaffolds_only"
    ids = [topic["id"] for chapter in data["chapters"] for topic in chapter["topics"]]
    assert ids and len(ids) == len(set(ids))


def test_chapter_lookup_is_exact_and_case_insensitive():
    data = load_teaching_dataset()
    assert find_chapter(data, "mathematics", "Patterns in Mathematics") is not None
    assert find_chapter(data, "Science", "Made-up chapter") is None


def test_tanglish_prompt_requires_real_code_switching_and_matching_captions():
    prompt = build_teacher_instructions(
        subject="Science", chapter="The Wonderful World of Science",
        topic="Observation and fair tests", app_language="Tanglish",
        source_evidence=[{"source_id": "c1", "page_start": 4, "page_end": 5, "text": "Observe carefully."}],
    )
    assert "must not be English-only" in prompt
    assert "captions are the exact text being spoken" in prompt
    assert "source_id=c1" in prompt
    assert "ask 2-3 short questions" in prompt


def test_missing_source_is_not_claimed_as_textbook_verified():
    prompt = build_teacher_instructions(
        subject="Mathematics", chapter="Patterns in Mathematics",
        topic="Number patterns", app_language="English", source_evidence=[],
    )
    assert "Do not claim textbook verification" in prompt
    assert "lesson is not textbook-verified" in prompt


@pytest.mark.parametrize(
    "correct,total,explanation,expected",
    [(2, 3, True, True), (3, 3, False, False), (1, 3, True, False), (0, 2, True, False)],
)
def test_mastery_gate(correct, total, explanation, expected):
    result = mastery_decision(correct, total, explanation)
    assert result["mastered"] is expected
    assert result["can_advance"] is expected
    assert result["next_action"] == ("offer_next_concept" if expected else "reteach_and_retest")


def test_mastery_rejects_invalid_counts():
    with pytest.raises(ValueError):
        mastery_decision(4, 3, True)
