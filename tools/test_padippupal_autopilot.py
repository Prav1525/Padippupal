import json
import tempfile
import unittest
from pathlib import Path

from padippupal_autopilot import (
    MAX_REPAIR_GENERATIONS,
    approved_task,
    classify_log,
    next_generation,
    validate,
)


class ClassificationTests(unittest.TestCase):
    def test_known_android_failure_is_classified(self):
        self.assertEqual(classify_log("Execution failed for task :app:testDebugUnitTest")[0],
                         "android_build_or_test")

    def test_unknown_failure_requires_review(self):
        self.assertEqual(classify_log("strange opaque runner event")[0],
                         "unknown_requires_review")


class RepairLimitTests(unittest.TestCase):
    def test_all_five_generations_are_available(self):
        self.assertEqual([next_generation(n) for n in range(5)], [1, 2, 3, 4, 5])

    def test_sixth_generation_is_blocked(self):
        self.assertIsNone(next_generation(MAX_REPAIR_GENERATIONS))

    def test_negative_generation_is_rejected(self):
        with self.assertRaises(ValueError):
            next_generation(-1)


class ApprovalTests(unittest.TestCase):
    def test_only_exact_approved_task_is_eligible(self):
        ledger = {"tasks": [
            {"id": "A", "status": "APPROVED"},
            {"id": "B", "status": "PROPOSED"},
        ]}
        self.assertIsNotNone(approved_task("A", ledger))
        self.assertIsNone(approved_task("B", ledger))
        self.assertIsNone(approved_task("C", ledger))

    def test_duplicate_or_incomplete_approved_entries_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rel in ("TESTING_GUIDANCE.md", "TEST_INVESTIGATION.md",
                        "docs/TESTING_ERRORS.md", "docs/TEST_FAILURE_REGISTER.md",
                        ".github/testing-regression-checklist.md"):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("guide", encoding="utf-8")
            ledger = {"policy":"approved-roadmap-only", "max_repair_generations":5,
                      "tasks":[{"id":"A","status":"APPROVED"}]}
            (root / "docs/approved-work.json").write_text(json.dumps(ledger), encoding="utf-8")
            self.assertTrue(any("lacks scope" in item for item in validate(root)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
