import copy
import json
from pathlib import Path

import pytest

from import_science_translations import apply_patch


PATCH_DIR = Path(__file__).with_name("science_translation_patches") / "cbse_class6"

APPROVED_LESSONS = {
    "a_journey_through_states_of_water": ("a5eda399-5e4f-5bb3-8424-273c4f91bbad", "A Journey through States of Water", 8),
    "beyond_earth": ("10d13a36-87e9-5f3b-8210-f62eb95e8854", "Beyond Earth", 8),
    "diversity_in_the_living_world": ("4eebec1b-62e6-5843-9eaa-d4df9bbd7c87", "Diversity in the Living World", 8),
    "exploring_magnets": ("958addf6-1ff1-54c3-934e-d8d67548759f", "Exploring Magnets", 7),
    "living_creatures_exploring_their_characteristics": ("a52d8c99-b24d-5c69-9137-0222baff2bdc", "Living Creatures: Exploring their Characteristics", 8),
    "materials_around_us": ("20b0bf32-d25c-5210-bdca-2ac203fa3c00", "Materials Around Us", 7),
    "measurement_of_length_and_motion": ("435b479e-b2ce-5744-be1d-63984ba5115f", "Measurement of Length and Motion", 8),
    "methods_of_separation_in_everyday_life": ("5176cc88-77d7-5893-b67b-570c98e65c17", "Methods of Separation in Everyday Life", 8),
    "mindful_eating_a_path_to_a_healthy_body": ("6c76991a-220d-5321-82a5-c1de4f06f876", "Mindful Eating: A Path to a Healthy Body", 8),
    "natures_treasures": ("2724ac7f-6c27-5ad0-91b4-c8cde97af506", "Nature's Treasures", 7),
    "temperature_and_its_measurement": ("7ba07e6b-c3dd-5a0a-a0b1-f2102b70f9d3", "Temperature and its Measurement", 8),
    "the_wonderful_world_of_science": ("24297054-ccec-55ce-8428-ac94cbe0b79f", "The Wonderful World of Science", 7),
}

EXPECTED_PATCH_FILES = {
    f"{slug}.{language}.json"
    for slug in APPROVED_LESSONS
    for language in ("tanglish", "tamil")
}


def _source_fixture(patch, step_count):
    return {
        "id": patch["lesson_id"],
        "chapter": patch["chapter"],
        "subject": "Science",
        "lesson": {
            "chapter_title": patch["chapter"],
            "overview": "Original English overview",
            "learning_objectives": [f"English objective {i}" for i in range(6)],
            "concept_map": [{"concept": "source concept", "source_chunk_ids": ["concept-source"]}],
            "teaching_sequence": [
                {
                    "id": f"step_{i}",
                    "title": f"English title {i}",
                    "caption": f"English caption {i}",
                    "teacher_says": f"English narration {i}",
                    "checkpoint": f"English check {i}",
                    "source_chunk_ids": [f"source-{i}"],
                    "visual": {
                        "type": "diagram",
                        "objects": ["unchanged"],
                        "actions": [],
                        "narration_sync": True,
                    },
                }
                for i in range(1, step_count + 1)
            ],
        },
    }


def test_all_approved_science_lessons_have_both_language_patches():
    actual = {path.name for path in PATCH_DIR.glob("*.json")}
    assert actual == EXPECTED_PATCH_FILES


@pytest.mark.parametrize("patch_path", sorted(PATCH_DIR.glob("*.json")), ids=lambda path: path.name)
def test_each_language_patch_preserves_approved_synthesis_structure(patch_path):
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    slug, language = patch_path.stem.rsplit(".", 1)
    expected_id, expected_chapter, expected_steps = APPROVED_LESSONS[slug]

    assert patch["lesson_id"] == expected_id
    assert patch["chapter"] == expected_chapter
    assert patch["language"].casefold() == language
    assert patch.get("board") == "CBSE"
    assert patch.get("class_level") == 6
    assert patch.get("subject") == "Science"
    assert isinstance(patch.get("chapter_title"), str) and patch["chapter_title"].strip()
    assert isinstance(patch.get("overview"), str) and patch["overview"].strip()
    assert len(patch.get("learning_objectives", [])) == 6
    assert all(isinstance(value, str) and value.strip() for value in patch["learning_objectives"])
    assert len(patch.get("teaching_sequence", [])) == expected_steps
    assert [step.get("id") for step in patch["teaching_sequence"]] == [
        f"step_{i}" for i in range(1, expected_steps + 1)
    ]

    for step in patch["teaching_sequence"]:
        assert set(step) == {"id", "title", "caption", "teacher_says", "checkpoint"}
        for field in ("title", "caption", "teacher_says", "checkpoint"):
            assert isinstance(step[field], str) and step[field].strip()

    source = _source_fixture(patch, expected_steps)
    original = copy.deepcopy(source["lesson"])
    localized = apply_patch(source, patch)

    assert [step["id"] for step in localized["teaching_sequence"]] == [
        step["id"] for step in original["teaching_sequence"]
    ]
    assert [step["source_chunk_ids"] for step in localized["teaching_sequence"]] == [
        step["source_chunk_ids"] for step in original["teaching_sequence"]
    ]
    assert [step["visual"] for step in localized["teaching_sequence"]] == [
        step["visual"] for step in original["teaching_sequence"]
    ]
    assert localized["concept_map"] == original["concept_map"]
    assert localized["teaching_sequence"][0]["caption"] != original["teaching_sequence"][0]["caption"]


def test_translation_patch_rejects_changed_step_order():
    patch = json.loads((PATCH_DIR / "beyond_earth.tanglish.json").read_text(encoding="utf-8"))
    source = _source_fixture(patch, 8)
    patch["teaching_sequence"][0]["id"] = "step_2"
    with pytest.raises(ValueError, match="step ID"):
        apply_patch(source, patch)


def test_translation_patch_does_not_allow_visual_or_citation_edits():
    patch = json.loads((PATCH_DIR / "beyond_earth.tamil.json").read_text(encoding="utf-8"))
    source = _source_fixture(patch, 8)
    patch["teaching_sequence"][0]["visual"] = {"type": "none"}
    with pytest.raises(ValueError, match="unsupported patch fields"):
        apply_patch(source, patch)
