#!/usr/bin/env python3
"""Static regression checks for the diary emulator's ADB command construction."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui_smoke
from ui_smoke import tap_file

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "diary_crop_emulator_test.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "android-ui-smoke.yml"


class DiaryEmulatorCommandRegressionTests(unittest.TestCase):
    def test_picker_taps_filename_text_not_preview_affordance(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('ui_smoke.py tap-file ui-screenshots/diary-test/diary-picker-list.xml "PadippuPal-diary-test.jpg"', source)
        self.assertIn('ui_smoke.py tap ui-screenshots/diary-test/diary-picker-downloads.xml "List view"', source)
        self.assertIn('dump_ui diary-picker-selection-result', source)
        self.assertIn('picker-selection-result.png', source)
        self.assertIn('returned=0', source)
        self.assertIn('for attempt in $(seq 1 8); do', source)
        self.assertLess(source.index("returned=0"), source.index("for attempt in $(seq 1 8); do"))
        self.assertNotIn("com.android.documentsui:id/preview_icon", source)
        self.assertNotIn("Preview the file PadippuPal-diary-test.jpg", source)
        self.assertNotIn("PY# Give the picker time", source)
        self.assertIn('package="com.padippupal.app"', source)
        self.assertIn('assert_has ui-screenshots/diary-test/diary-photo-selected.xml "Crop this photo and rescan"', source)
        self.assertNotIn('Tap DocumentsUI item row body at', source)


    def test_tap_file_command_is_registered_in_dispatcher(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "picker.xml"
            path.write_text("<hierarchy />", encoding="utf-8")
            with mock.patch.object(ui_smoke, "tap_file") as selector, \
                 mock.patch.object(ui_smoke.sys, "argv", ["ui_smoke.py", "tap-file", str(path), "PadippuPal-diary-test.jpg"]):
                ui_smoke.main()
            selector.assert_called_once_with(str(path), "PadippuPal-diary-test.jpg")

    def test_file_selector_taps_filename_when_row_is_not_clickable(self):
        xml = """<hierarchy>
          <node text="PadippuPal-diary-test.jpg" content-desc="" clickable="false" bounds="[189,685][660,742]" />
          <node resource-id="com.android.documentsui:id/item_root" clickable="false" bounds="[0,641][1080,830]" />
          <node resource-id="com.android.documentsui:id/icon_thumb" clickable="false" bounds="[42,683][147,788]" />
          <node text="" content-desc="Preview the file PadippuPal-diary-test.jpg" clickable="true" bounds="[891,641][1080,830]" />
        </hierarchy>"""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "list.xml"
            path.write_text(xml, encoding="utf-8")
            with mock.patch("ui_smoke.subprocess.run") as run:
                tap_file(str(path), "PadippuPal-diary-test.jpg")
                args = run.call_args.args[0]
                self.assertEqual(args[-2:], ["424", "713"])
                run.assert_called_once_with(["adb", "-s", "emulator-5554", "shell", "input", "tap", "424", "713"], check=True, timeout=45)

    def test_tap_file_command_selects_row_through_dispatcher(self):
        xml = """<hierarchy>
          <node text="PadippuPal-diary-test.jpg" content-desc="" clickable="true" bounds="[20,100][350,180]" />
        </hierarchy>"""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "list.xml"
            path.write_text(xml, encoding="utf-8")
            with mock.patch.object(sys, "argv", ["ui_smoke.py", "tap-file", str(path), "PadippuPal-diary-test.jpg"]):
                with mock.patch("ui_smoke.subprocess.run") as run:
                    ui_smoke.main()
                    self.assertEqual(run.call_count, 1)
                    for call in run.call_args_list:
                        self.assertEqual(call.args[0][-2:], ["185", "140"])

    def test_file_selector_accepts_clickable_list_row_not_preview(self):
        xml = """<hierarchy>
          <node text="" content-desc="Preview the file PadippuPal-diary-test.jpg" clickable="true" bounds="[240,100][300,160]" />
          <node text="PadippuPal-diary-test.jpg" content-desc="" clickable="true" bounds="[20,100][350,180]" />
        </hierarchy>"""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "list.xml"
            path.write_text(xml, encoding="utf-8")
            with mock.patch("ui_smoke.subprocess.run") as run:
                tap_file(str(path), "PadippuPal-diary-test.jpg")
                args = run.call_args.args[0]
                self.assertEqual(args[-2:], ["185", "140"])
                self.assertEqual(run.call_count, 1)
                for call in run.call_args_list:
                    self.assertEqual(call.args[0][-2:], ["185", "140"])

    def test_file_selector_never_blindly_double_taps(self):
        source = (ROOT / ".github" / "scripts" / "ui_smoke.py").read_text(encoding="utf-8")
        start = source.index("def tap_file(")
        end = source.index("\ndef _contains_bounds", start)
        selector = source[start:end]
        self.assertIn("filename text", selector)
        self.assertIn("separate preview action", selector)
        self.assertEqual(selector.count('subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap"'), 1)

    def test_missing_filename_fails_safely_without_tapping_preview(self):
        xml = """<hierarchy>
          <node text="" content-desc="Preview the file other.jpg" clickable="true" bounds="[240,100][300,160]" />
        </hierarchy>"""
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "list.xml"
            path.write_text(xml, encoding="utf-8")
            with mock.patch("ui_smoke.subprocess.run") as run:
                with self.assertRaises(SystemExit):
                    tap_file(str(path), "PadippuPal-diary-test.jpg")
                run.assert_not_called()

    def test_picker_return_is_verified_before_crop_assertions(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('dump_ui diary-picker-selection-result', source)
        # Assert the diagnostic's intent, not a brittle, obsolete full message.
        self.assertIn('did not return from DocumentsUI', source)
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
