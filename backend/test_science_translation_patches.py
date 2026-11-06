import copy
import json
from pathlib import Path

import pytest

from backend.import_science_translations import apply_patch


PATCH_DIR = Path(__file__).with_name("science_translation_patches") / "cbse_class6"


@pytest.mark.parametrize("language", ["tanglish", "tamil"])
def test_beyond_earth_translation_patch_preserves_synthesis_structure(language):
    patch = json.loads((PATCH_DIR / f"beyond_earth.{language}.json").read_text(encoding="utf-8"))
    source_lesson = {
        "id": patch["lesson_id"],
        "chapter": patch["chapter"],
        "subject": "Science",
        "lesson": {
            "chapter_title": "Beyond Earth",
            "overview": "English overview",
            "learning_objectives": ["one", "two", "three", "four", "five", "six"],
            "concept_map": [{"concept": "stars", "source_chunk_ids": ["chunk-1"]}],
            "teaching_sequence": [
                {"id": f"step_{i}", "title": f"English title {i}", "caption": f"English caption {i}",
                 "teacher_says": f"English narration {i}", "checkpoint": f"English check {i}",
                 "source_chunk_ids": [f"chunk-{i}"],
                 "visual": {"type": "diagram", "objects": ["unchanged"], "actions": [], "narration_sync": True}}
                for i in range(1, 9)
            ],
        },
    }
    original = copy.deepcopy(source_lesson["lesson"])
    result = apply_patch(source_lesson, patch)
    assert len(result["teaching_sequence"]) == len(original["teaching_sequence"]) == 8
    assert [step["id"] for step in result["teaching_sequence"]] == [f"step_{i}" for i in range(1, 9)]
    assert [step["source_chunk_ids"] for step in result["teaching_sequence"]] == [
        step["source_chunk_ids"] for step in original["teaching_sequence"]
    ]
    assert [step["visual"] for step in result["teaching_sequence"]] == [
        step["visual"] for step in original["teaching_sequence"]
    ]
    assert result["concept_map"] == original["concept_map"]
    assert result["teaching_sequence"][0]["caption"] != original["teaching_sequence"][0]["caption"]


def test_translation_patch_rejects_changed_step_order():
    patch = json.loads((PATCH_DIR / "beyond_earth.tanglish.json").read_text(encoding="utf-8"))
    source = {"id": patch["lesson_id"], "chapter": patch["chapter"], "subject": "Science",
              "lesson": {"chapter_title": "Beyond Earth", "overview": "x",
                         "learning_objectives": ["a"] * 6,
                         "teaching_sequence": [{"id": f"step_{i}"} for i in range(1, 9)]}}
    patch["teaching_sequence"][0]["id"] = "step_2"
    with pytest.raises(ValueError, match="step ID"):
        apply_patch(source, patch)


def test_translation_patch_does_not_allow_visual_or_citation_edits():
    patch = json.loads((PATCH_DIR / "beyond_earth.tamil.json").read_text(encoding="utf-8"))
    source = {"id": patch["lesson_id"], "chapter": patch["chapter"], "subject": "Science",
              "lesson": {"chapter_title": "Beyond Earth", "overview": "x",
                         "learning_objectives": ["a"] * 6,
                         "teaching_sequence": [{"id": f"step_{i}"} for i in range(1, 9)]}}
    patch["teaching_sequence"][0]["visual"] = {"type": "none"}
    with pytest.raises(ValueError, match="unsupported patch fields"):
        apply_patch(source, patch)
