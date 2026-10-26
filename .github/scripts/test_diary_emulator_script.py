#!/usr/bin/env python3
"""Static regression checks for the diary emulator's ADB command construction."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui_smoke
from ui_smoke import tap_file, photo_picker_item_candidates

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "diary_crop_emulator_test.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "android-ui-smoke.yml"


class DiaryEmulatorCommandRegressionTests(unittest.TestCase):
    def test_picker_uses_photo_picker_contract_and_selects_fixture_by_filename(self):
        app = (ROOT / "app" / "src" / "main" / "java" / "com" / "padippupal" / "app" / "StudyFeatures.kt").read_text(encoding="utf-8")
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("ActivityResultContracts.PickVisualMedia()", app)
        self.assertIn("import androidx.activity.result.PickVisualMediaRequest", app)
        self.assertIn("picker.launch(PickVisualMediaRequest(", app)
        self.assertNotIn("ActivityResultContracts.PickVisualMediaRequest", app)
        self.assertIn("ActivityResultContracts.PickVisualMedia.ImageOnly", app)
        self.assertIn('ui_smoke.py tap-photo-picker-item ui-screenshots/diary-test/diary-picker.xml', source)
        self.assertNotIn('system Photo Picker does not expose the indexed fixture by filename', source)
        self.assertIn('dump_ui diary-picker-selection-result', source)
        self.assertIn('PickVisualMedia did not return to PadippuPal', source)
        self.assertIn('assert_has ui-screenshots/diary-test/diary-photo-selected.xml "Crop this photo and rescan"', source)
        self.assertNotIn('ui_smoke.py tap-file', source)
        self.assertNotIn('preview_icon', source)
        picker_section = source[source.index('log "Opening gallery/photo picker"'):source.index('log "Opening crop editor')]
        self.assertNotIn('KEYCODE_DPAD_CENTER', picker_section)
        self.assertNotIn('List view', picker_section)
        self.assertNotIn('Downloads', picker_section)
        self.assertEqual(picker_section.count('dump_ui diary-picker\n'), 1)

    def test_api35_photo_picker_tile_is_selected_without_relying_on_hidden_filename(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring("""<hierarchy>
          <node class="android.widget.FrameLayout" package="com.android.providers.media.module"
                content-desc="Photo taken on Oct 26, 2026, 4:52 AM"
                clickable="true" enabled="true" bounds="[0,1217][354,1571]" />
          <node class="android.widget.FrameLayout" package="com.android.providers.media.module"
                content-desc="" clickable="false" bounds="[0,1217][354,1571]" />
        </hierarchy>""")
        candidates = photo_picker_item_candidates(list(root.iter("node")))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].attrib["bounds"], "[0,1217][354,1571]")
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("tap-photo-picker-item", source)
        helper = (ROOT / ".github" / "scripts" / "ui_smoke.py").read_text(encoding="utf-8")
        self.assertIn("exactly one clickable photo tile", helper)
        self.assertNotIn('grep -qi "PadippuPal-diary-test.jpg" ui-screenshots/diary-test/diary-picker.xml', source)

    def test_picker_return_is_verified_before_crop_assertions(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('package="com.padippupal.app"', source)
        self.assertIn('dump_ui diary-picker-selection-result', source)
        self.assertIn('FAIL: PickVisualMedia did not return to PadippuPal', source)
        self.assertIn('assert_has ui-screenshots/diary-test/diary-photo-selected.xml "Crop this photo and rescan"', source)

    def test_failure_register_exists_and_names_regression_expectations(self):
        register = ROOT / "docs" / "TEST_FAILURE_REGISTER.md"
        self.assertTrue(register.is_file(), "Recurring failures must be recorded in the repository")
        text = register.read_text(encoding="utf-8")
        self.assertIn("root cause", text.lower())
        self.assertIn("regression test", text.lower())
        self.assertIn("3dde5052105d82c1c54fa5968d6c495baef62b54", text)

    def test_launcher_activity_preflight_passes_all_arguments_in_one_shell_command(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        command = "adb -s emulator-5554 shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.padippupal.app"
        self.assertIn(command, workflow)
        self.assertNotIn("resolve-activity --brief \\\n              -a android.intent.action.MAIN", workflow)

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
