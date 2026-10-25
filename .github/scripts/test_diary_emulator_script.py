#!/usr/bin/env python3
"""Static regression checks for the diary emulator's ADB command construction."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "diary_crop_emulator_test.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "android-ui-smoke.yml"


class DiaryEmulatorCommandRegressionTests(unittest.TestCase):
    def test_picker_uses_real_thumbnail_tap_not_long_press_select_guess(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('shell content insert --uri content://media/external/images/media', source)
        self.assertIn('content query --uri content://media/external/images/media', source)
        self.assertIn('--projection _id:_display_name:_data | grep -Fq "PadippuPal-diary-test.jpg"', source)
        self.assertNotIn('--bind display_name:s:', source)
        self.assertNotIn('--bind relative_path:s:', source)
        self.assertIn('"padippupal-diary-test.jpg" in (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()', source)
        self.assertIn('r"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]"', source)
        self.assertIn('endswith(":id/thumbnail")', source)
        self.assertIn('Tap fixture thumbnail at', source)
        self.assertIn('["adb","-s","emulator-5554","shell","input","tap",str(x),str(y)]', source)
        self.assertIn('if ! grep -q \'package="com.android.documentsui"\'', source)
        self.assertNotIn('Long-press filename to enter selection mode', source)
        self.assertNotIn('No visible Select action after long-press', source)
        self.assertNotIn('Tap observed DocumentsUI action', source)

    def test_picker_return_is_verified_before_crop_assertions(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('dump_ui diary-picker-selection-result', source)
        self.assertIn('FAIL: tapping the fixture thumbnail did not return from DocumentsUI', source)
        self.assertIn('assert_has ui-screenshots/diary-test/diary-photo-selected.xml "Crop this photo and rescan"', source)

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
