#!/usr/bin/env python3
"""Unit tests for the free-first PadippuPal AutoPilot helper."""
import tempfile
import unittest
from pathlib import Path

from padippupal_autopilot import check_guides, classify, read_log


class ClassificationTests(unittest.TestCase):
    def test_recognizes_runner_infrastructure_signature(self):
        self.assertEqual(classify("Hosted runner lost communication")[0], "runner_infrastructure")

    def test_recognizes_network_signature(self):
        self.assertEqual(classify("HTTP 429 Too Many Requests")[0], "dependency_or_network")

    def test_recognizes_android_build_failure(self):
        self.assertEqual(classify("Execution failed for task :app:compileDebugKotlin")[0], "android_build_or_test")

    def test_recognizes_emulator_failure(self):
        self.assertEqual(classify("adb: device offline")[0], "emulator_or_adb")

    def test_unknown_failure_is_review_only(self):
        category, evidence = classify("Unexpected failure with no known signature")
        self.assertEqual(category, "unknown_requires_review")
        self.assertIn("No allowlisted signature matched", evidence)

    def test_log_excerpt_is_bounded_to_last_60000_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "job.log"
            log.write_text("x" * 60005 + "TAIL", encoding="utf-8")
            result = read_log(log)
            self.assertEqual(len(result), 60000)
            self.assertTrue(result.endswith("TAIL"))


class GuideCheckTests(unittest.TestCase):
    def test_requires_all_project_records_and_discovers_docs_guides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "AGENTS.md", "README.md", "PROJECT_STATUS.md",
                "docs/TESTING_ERRORS.md", ".github/testing-regression-checklist.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("readable", encoding="utf-8")
            (root / "docs" / "EXTRA_GUIDE.md").write_text("guide", encoding="utf-8")
            self.assertEqual(check_guides(root), 0)

    def test_missing_required_record_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("guide", encoding="utf-8")
            self.assertEqual(check_guides(root), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
