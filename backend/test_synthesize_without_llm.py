import unittest

from scripts.synthesize_without_llm import (
    build_lesson,
    clean_source_text,
    quality_gate,
    source_based_example,
    specific_objective,
)


class ExtractiveSynthesisQualityTests(unittest.TestCase):
    def test_removes_known_running_headers_and_control_characters(self):
        cleaned = clean_source_text(
            "Curiosity | Textbook of Science | Grade 6 144 Activity 8.1: Let us observe. "
            "A cube of ice melts. \x8b"
        )
        self.assertNotIn("Curiosity | Textbook of Science", cleaned)
        self.assertNotIn("\x8b", cleaned)
        self.assertIn("Activity 8.1", cleaned)
        self.assertIn("A cube of ice melts.", cleaned)
        chapter_cleaned = clean_source_text("A Journey through States of Water8 Chapter On a bright summer afternoon, Aavi observes ice.", "A Journey through States of Water")
        self.assertNotIn("States of Water8 Chapter", chapter_cleaned)
        self.assertIn("On a bright summer afternoon", chapter_cleaned)

    def test_objective_is_source_specific(self):
        objective = specific_objective(
            "When ice is warmed, it changes into liquid water. This is a change of state.",
            "A Journey through States of Water",
        )
        self.assertIn("When ice is warmed", objective)
        self.assertNotIn("source section", objective.lower())

    def test_example_uses_actual_source_passage_not_placeholder(self):
        example = source_based_example("A magnet attracts objects made of iron.")
        self.assertIn("A magnet attracts objects made of iron.", example)
        self.assertNotIn("Use an example or diagram", example)

    def test_lesson_builds_specific_objectives_and_passage_based_steps(self):
        chunks = [
            {"id": "c1", "text": "When ice is warmed, it changes into liquid water.", "page_start": 1},
            {"id": "c2", "text": "Water can exist as a solid, liquid, or gas.", "page_start": 2},
            {"id": "c3", "text": "Cooling water vapour can cause it to condense into liquid water.", "page_start": 3},
            {"id": "c4", "text": "The water cycle moves water between Earth and the atmosphere.", "page_start": 4},
        ]
        lesson, validation = build_lesson("Science", "A Journey through States of Water", chunks)
        self.assertTrue(validation["valid"], validation["errors"])
        self.assertEqual(len(lesson["teaching_sequence"]), 4)
        self.assertGreaterEqual(len(lesson["learning_objectives"]), 3)
        self.assertTrue(all("source section" not in item.lower() for item in lesson["learning_objectives"]))
        self.assertTrue(all("Use an example or diagram" not in step["example"] for step in lesson["teaching_sequence"]))
        self.assertEqual(quality_gate(lesson, chunks), [])

    def test_quality_gate_rejects_generic_placeholders(self):
        lesson = {
            "learning_objectives": ["Identify and explain the main idea in source section 1."],
            "teaching_sequence": [{
                "teacher_says": "This is a sufficiently long teacher explanation for the learner.",
                "caption": "This is a sufficiently long caption for a teaching step.",
                "example": "Use an example or diagram from the cited textbook passage and explain why it fits.",
                "checkpoint": "This is a sufficiently long checkpoint prompt for the learner.",
                "source_chunk_ids": ["c1"],
            }],
        }
        errors = quality_gate(lesson, [{"id": "c1"}])
        self.assertTrue(any("generic/placeholder" in error or "placeholder example" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
