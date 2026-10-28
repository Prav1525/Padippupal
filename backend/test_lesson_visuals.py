import json
import unittest

from lesson_visuals import build_visual_records


class SynthesizedLessonVisualTests(unittest.TestCase):
    def setUp(self):
        self.lesson = {
            "chapter_title": "Fractions",
            "teaching_sequence": [
                {
                    "id": "fraction-whole",
                    "title": "Split a whole",
                    "caption": "A fraction shows equal parts of one whole.",
                    "teacher_says": "Look at these four equal parts.",
                    "source_chunk_ids": ["chunk-12"],
                    "visual": {
                        "type": "fraction",
                        "objects": ["one whole", "four equal parts", "one shaded part"],
                        "actions": ["shade one part"],
                        "narration_sync": ["four equal parts"],
                    },
                },
                {
                    "id": "fraction-recap",
                    "title": "Remember the rule",
                    "caption": "The bottom number tells how many equal parts make the whole.",
                    "source_chunk_ids": ["chunk-12", "chunk-13"],
                    "visual": {"type": "diagram", "objects": ["denominator", "equal parts"]},
                },
            ],
        }

    def test_visual_records_map_one_to_one_to_synthesis_steps(self):
        records = build_visual_records("lesson-1", self.lesson)
        self.assertEqual([r["step_id"] for r in records], ["fraction-whole", "fraction-recap"])
        self.assertEqual(records[0]["summary_text"], self.lesson["teaching_sequence"][0]["caption"])
        self.assertEqual(records[0]["source_chunk_ids_json"], '["chunk-12"]')
        self.assertEqual(records[0]["blueprint"]["nodes"], ["one whole", "four equal parts", "one shaded part"])

    def test_visuals_are_small_static_2d_blueprints(self):
        records = build_visual_records("lesson-1", self.lesson)
        for record in records:
            blueprint = record["blueprint"]
            self.assertEqual(blueprint["layout"], "compact_2d")
            self.assertEqual(blueprint["motion"], "none")
            self.assertNotIn("3d", json.dumps(blueprint).lower())
            self.assertLessEqual(len(blueprint["nodes"]), 6)

    def test_fingerprint_is_stable_and_changes_with_synthesis(self):
        first = build_visual_records("lesson-1", self.lesson)
        second = build_visual_records("lesson-1", self.lesson)
        self.assertEqual([r["content_fingerprint"] for r in first],
                         [r["content_fingerprint"] for r in second])
        self.lesson["teaching_sequence"][0]["caption"] = "A fraction names equal parts of a whole."
        changed = build_visual_records("lesson-1", self.lesson)
        self.assertNotEqual(first[0]["content_fingerprint"], changed[0]["content_fingerprint"])

    def test_empty_or_missing_sequence_produces_no_unrelated_visual(self):
        self.assertEqual(build_visual_records("lesson-2", {}), [])
        self.assertEqual(build_visual_records("lesson-2", {"teaching_sequence": []}), [])


if __name__ == "__main__":
    unittest.main()
