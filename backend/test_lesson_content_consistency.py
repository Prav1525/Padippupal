import unittest

from syllabus_synthesis import validate_lesson_content_consistency


class LessonContentConsistencyTests(unittest.TestCase):
    def test_fractions_rejects_rig_veda_modern_notation_conflation(self):
        errors = validate_lesson_content_consistency({
            "chapter_title": "Fractions",
            "teaching_sequence": [{
                "title": "History of Fractions",
                "teacher_says": "The Rig Veda used tri-pada. Ancient texts used notation very similar to ours.",
                "visual": {"type": "diagram"},
            }],
        })
        self.assertTrue(any("Rig Veda" in error for error in errors), errors)

    def test_fractions_rejects_chikki_visual_thirds_vs_narration_sixths(self):
        errors = validate_lesson_content_consistency({
            "chapter_title": "Fractions",
            "teaching_sequence": [{
                "title": "Parts of a Whole",
                "teacher_says": "A chikki divided into 6 equal parts gives six 1/6 pieces.",
                "visual": {"type": "diagram", "narration_sync": ["A whole chikki broken into 3 equal pieces."]},
            }],
        })
        self.assertTrue(any("thirds" in error for error in errors), errors)

    def test_fractions_rejects_number_line_denominator_mismatch(self):
        errors = validate_lesson_content_consistency({
            "chapter_title": "Fractions",
            "teaching_sequence": [{
                "title": "Marking Fractions on the Number Line",
                "teacher_says": "Divide into 2 equal parts. Divide into 3 equal parts.",
                "visual": {"type": "number_line", "narration_sync": ["Divide into 5 equal parts."]},
            }],
        })
        self.assertTrue(any("fifths" in error for error in errors), errors)

    def test_data_handling_rejects_four_strokes_for_five_mark_tally(self):
        errors = validate_lesson_content_consistency({
            "chapter_title": "Data Handling and Presentation",
            "teaching_sequence": [{
                "title": "Organising Data and Tally Marks",
                "teacher_says": "Cross every fifth mark as |||| to count preferences.",
                "visual": {"type": "table"},
            }],
        })
        self.assertTrue(any("four vertical strokes" in error for error in errors), errors)

    def test_perimeter_area_rejects_overgeneralized_diagonal_claim(self):
        errors = validate_lesson_content_consistency({
            "chapter_title": "Perimeter and Area",
            "teaching_sequence": [{
                "title": "Straight vs. Diagonal Units",
                "teacher_says": "A diagonal line is longer than a straight grid unit!",
                "visual": {"type": "geometry"},
            }],
        })
        self.assertTrue(any("unit square" in error for error in errors), errors)

    def test_perimeter_area_rejects_unspecified_corresponding_rectangle(self):
        errors = validate_lesson_content_consistency({
            "chapter_title": "Perimeter and Area",
            "teaching_sequence": [{
                "title": "Area of Triangles and Composite Shapes",
                "teacher_says": "Any rectangle cut along its diagonal gives two equal triangles. The triangle is half the area.",
                "visual": {"type": "geometry"},
            }],
        })
        self.assertTrue(any("same base" in error for error in errors), errors)

    def test_corrected_wording_is_not_flagged(self):
        errors = validate_lesson_content_consistency({
            "chapter_title": "Perimeter and Area",
            "teaching_sequence": [{
                "title": "Area of Triangles",
                "teacher_says": "A triangle has half the area of a rectangle with the same base and corresponding height.",
                "visual": {"type": "geometry"},
            }],
        })
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
