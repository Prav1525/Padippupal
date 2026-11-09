import unittest

from tools.audit_lesson_visual_coverage import audit


class VisualCoverageAuditTests(unittest.TestCase):
    def setUp(self):
        self.curriculum = [
            {"id": "lesson-a", "subject": "Mathematics", "chapter": "Fractions",
             "modules": [
                 {"step_id": "step_1", "title": "Fractions", "caption": "Show one quarter as equal parts."},
                 {"step_id": "step_2", "title": "Practice", "caption": "Try another example."},
             ]},
            {"id": "lesson-b", "subject": "Science", "chapter": "Plants",
             "modules": [
                 {"step_id": "step_1", "title": "Parts of a plant", "caption": "Observe the leaf and flower."},
             ]},
        ]

    def test_reports_unmapped_and_routes_abstract_concept_to_original(self):
        result = audit(self.curriculum, {"images": []})
        self.assertEqual(result["summary"]["total_modules"], 3)
        self.assertEqual(result["summary"]["unmapped_modules"], 3)
        self.assertEqual(result["review_queue"][0]["proposed_route"], "ORIGINAL_DIAGRAM")
        self.assertEqual(result["review_queue"][1]["proposed_route"], "HUMAN_REVIEW")
        self.assertEqual(result["review_queue"][2]["proposed_route"], "WEB_PHOTO_OR_ORIGINAL")

    def test_plural_fraction_title_is_classified_as_original_diagram(self):
        from tools.audit_lesson_visual_coverage import route_for

        route, _ = route_for({"title": "Fractions", "caption": "Show one quarter as equal parts."})
        self.assertEqual(route, "ORIGINAL_DIAGRAM")

    def test_validates_exact_step_mapping(self):
        result = audit(self.curriculum, {"images": [
            {"lesson_id": "lesson-a", "module_key": "module-1", "step_ids": ["wrong"]}
        ]})
        self.assertEqual(result["summary"]["mapped_modules"], 1)
        self.assertEqual(result["errors"][0]["type"], "step_id_mismatch")

    def test_detects_duplicate_and_unknown_mapping(self):
        item = {"lesson_id": "lesson-a", "module_key": "module-1", "step_ids": ["step_1"]}
        result = audit(self.curriculum, {"images": [item, item, {
            "lesson_id": "not-real", "module_key": "module-9", "step_ids": []
        }]})
        types = [e["type"] for e in result["errors"]]
        self.assertIn("duplicate_mapping", types)
        self.assertIn("unknown_mapping", types)


if __name__ == "__main__":
    unittest.main()
