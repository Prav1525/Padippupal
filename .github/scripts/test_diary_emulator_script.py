#!/usr/bin/env python3
"""Static regression checks for the diary emulator's ADB command construction."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "diary_crop_emulator_test.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "android-ui-smoke.yml"


class DiaryEmulatorCommandRegressionTests(unittest.TestCase):
    def test_picker_hierarchy_dump_uses_dump_ui_helper(self):
        source = SCRIPT.read_text(encoding="utf-8")
        helper = source[source.index("dump_ui(){"):source.index("\ntap_label(){")]
        self.assertIn('shell uiautomator dump "/data/local/tmp/${name}.xml"', helper)
        self.assertIn('pull "/data/local/tmp/${name}.xml" "ui-screenshots/diary-test/${name}.xml"', helper)
        self.assertIn("dump_ui diary-picker-list", source)

    def test_picker_dump_is_pulled_before_it_is_parsed(self):
        source = SCRIPT.read_text(encoding="utf-8")
        dump = source.index("dump_ui diary-picker-list")
        parse = source.index('path="ui-screenshots/diary-test/diary-picker-list.xml"')
        self.assertLess(dump, parse)
        self.assertIn('ns=getnodes(path)', source[parse:])

    def test_failure_register_exists_and_names_regression_expectations(self):
        register = ROOT / "docs" / "TEST_FAILURE_REGISTER.md"
        self.assertTrue(register.is_file(), "Recurring failures must be recorded in the repository")
        text = register.read_text(encoding="utf-8")
        self.assertIn("root cause", text.lower())
        self.assertIn("regression test", text.lower())
        self.assertIn("3dde5052105d82c1c54fa5968d6c495baef62b54", text)


    def test_workflow_records_outcomes_even_when_a_step_fails(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: always()", workflow)
        self.assertIn("Record test outcomes and failure diagnostics", workflow)
        self.assertIn("test-failure-report.md", workflow)
        self.assertIn("padippupal-emulator-ui", workflow)
        report_script = ROOT / ".github" / "scripts" / "write_test_failure_report.py"
        report_source = report_script.read_text(encoding="utf-8")
        self.assertIn("Inspect this run's step logs and the padippupal-emulator-ui artifact.", report_source)
        self.assertIn("write_test_failure_report.py", workflow)



if __name__ == "__main__":
    unittest.main(verbosity=2)
