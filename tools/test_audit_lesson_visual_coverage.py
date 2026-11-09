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
             "modules": [{"step_id": "step_1", "title": "Parts of a plant",
                          "caption": "Observe the leaf and flower."}],
        ]

    def test_every_module_gets_explicit_lifecycle_status(self):
        result = audit(self.curriculum, {"images": []})
        self.assertEqual(result["summary"]["total_modules"], 3)
        self.assertEqual(result["summary"]["by_status"]["NEEDS_ORIGINAL_PNG"], 1)
        self.assertEqual(result["summary"]["by_status"]["NEEDS_REVIEW"], 1)
        self.assertEqual(result["summary"]["by_status"]["NEEDS_WEB_SOURCE"], 1)
        self.assertEqual(len(result["modules"]), 3)

    def test_source_and_lifecycle_manifests_are_joined(self):
        result = audit(
            self.curriculum,
            {"images": [{"lesson_id": "lesson-a", "module_key": "module-1",
                         "step_ids": ["step_1"]}]},
            {"images": [{"lesson_id": "lesson-b", "module_key": "module-1",
                         "step_ids": ["step_1"]}]},
            {"items": [{"lesson_id": "lesson-b", "module_key": "module-1",
                        "proposed_route": "WEB_PHOTO", "decision_status": "CURATED"}]},
            {"images": [{"lesson_id": "lesson-a", "module_key": "module-1",
                         "step_ids": ["step_1"]}]},
            {"images": [{"lesson_id": "lesson-a", "module_key": "module-1",
                         "step_ids": ["step_1"]}]},
        )
        by_key = {m["module_key"] + m["lesson_id"]: m for m in result["modules"]}
        self.assertEqual(by_key["module-1lesson-a"]["status"], "RENDER_VERIFIED")
        self.assertEqual(by_key["module-1lesson-b"]["status"], "NEEDS_REVIEW")
        self.assertEqual(by_key["module-1lesson-b"]["proposed_route"], "WEB_PHOTO")

    def test_ingested_is_not_mistaken_for_render_verified(self):
        result = audit(self.curriculum, {"images": []},
                       ingestion_ledger={"images": [
                           {"lesson_id": "lesson-a", "module_key": "module-1",
                            "step_ids": ["step_1"]}]})
        first = next(m for m in result["modules"] if m["lesson_id"] == "lesson-a"
                     and m["module_key"] == "module-1")
        self.assertEqual(first["status"], "INGESTED")

    def test_detects_duplicate_unknown_and_step_mismatch(self):
        item = {"lesson_id": "lesson-a", "module_key": "module-1", "step_ids": ["wrong"]}
        result = audit(self.curriculum, {"images": [item, item, {
            "lesson_id": "not-real", "module_key": "module-9", "step_ids": []}]})
        types = [e["type"] for e in result["errors"]]
        self.assertIn("duplicate_authoring_mapping", types)
        self.assertIn("unknown_authoring_mapping", types)
        self.assertIn("authoring_mapping_step_id_mismatch", types)


if __name__ == "__main__":
    unittest.main()
