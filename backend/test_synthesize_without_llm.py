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

    def test_tanglish_variant_and_manageable_lesson_pacing(self):
        chunks = [
            {"id": f"c{i}", "text": f"Water changes state in example number {i}. Heating and cooling can cause changes in water.", "page_start": i}
            for i in range(1, 25)
        ]
        lesson, validation = build_lesson("Science", "A Journey through States of Water", chunks)
        self.assertTrue(validation["valid"], validation["errors"])
        self.assertLessEqual(len(lesson["teaching_sequence"]), 8)
        self.assertGreaterEqual(len(lesson["teaching_sequence"]), 3)
        self.assertEqual(lesson["language_variants"]["Tanglish"]["available"], True)
        self.assertTrue(lesson["language_variants"]["Tanglish"]["human_review_required"])
        self.assertEqual(len(lesson["learning_objectives"]), len(lesson["learning_objectives_tanglish"]))
        cited = {
            cid
            for step in lesson["teaching_sequence"]
            for cid in step["source_chunk_ids"]
        }
        self.assertEqual(cited, {chunk["id"] for chunk in chunks})
        openings = (
            "Seri, idha easy-aa purinjukkalaam.",
            "Okay, indha part-a serndhu paapom.",
            "Nalla, inga oru mukkiyamaana idea irukku.",
            "Ippo indha concept-a simple-aa break panni paapom.",
            "Sari, indha example enna solludhu-nu yosippom.",
            "Konjam slow-aa paapom; avasaram illa.",
            "Super, indha idea purinja next part easy-aa irukkum.",
            "Oru chinna recap pannittu continue pannalaam.",
        )
        self.assertTrue(all(step["tanglish"]["teacher_says"].startswith(("Seri", "Okay", "Nalla", "Ippo", "Sari", "Konjam", "Super", "Oru")) for step in lesson["teaching_sequence"]))
        self.assertTrue(all("un words-la sollu" in step["tanglish"]["example"] for step in lesson["teaching_sequence"]))
        self.assertTrue(all("confusing-aa irundhaa parava illa" in step["tanglish"]["misconception"] for step in lesson["teaching_sequence"]))
        self.assertTrue(all(len(step["tanglish"]["checkpoint"]) >= 35 for step in lesson["teaching_sequence"]))
        self.assertTrue(all(len(step["caption"]) <= 500 for step in lesson["teaching_sequence"]))
        self.assertTrue(all(len(step["caption"]) <= 600 for step in lesson["teaching_sequence"]))
        self.assertTrue(all(len(step["tanglish"]["teacher_says"]) < 1000 for step in lesson["teaching_sequence"]))
        self.assertTrue(all("unga vaarthaigal-la" not in step["tanglish"]["teacher_says"].lower() for step in lesson["teaching_sequence"]))
        self.assertTrue(all(len(step["title"]) < 100 for step in lesson["teaching_sequence"]))

    def test_tanglish_explains_common_topics_without_reading_english_passage_aloud(self):
        fractions, _ = build_lesson("Mathematics", "Fractions", [
            {"id": "f1", "text": "Fractions tell us how much each share is when a roti is divided equally between two children.", "page_start": 1},
            {"id": "f2", "text": "The numerator tells how many parts are being considered and denominator tells the total equal parts.", "page_start": 2},
            {"id": "f3", "text": "Fractions represent equal shares of a whole.", "page_start": 3},
        ])
        first_math = fractions["teaching_sequence"][0]["tanglish"]["teacher_says"]
        self.assertIn("roti-a rendu per equal-aa share", first_math)
        self.assertIn("fraction-la", first_math)
        self.assertNotIn("Textbook-la indha point:", first_math)

        water, _ = build_lesson("Science", "A Journey through States of Water", [
            {"id": "w1", "text": "An ice cube melts into liquid water when left on a table.", "page_start": 1},
            {"id": "w2", "text": "Water can exist as a solid, liquid, or gas.", "page_start": 2},
            {"id": "w3", "text": "Cooling water vapour can cause it to condense into liquid water.", "page_start": 3},
        ])
        first_science = water["teaching_sequence"][0]["tanglish"]["teacher_says"]
        self.assertIn("ice-ku", first_science.lower())
        self.assertIn("melt aagi water-a maarum", first_science.lower())
        self.assertLess(len(first_science), 400)

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
