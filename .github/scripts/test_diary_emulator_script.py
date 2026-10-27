#!/usr/bin/env python3
"""Static regression checks for the diary emulator's ADB command construction."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ui_smoke
from ui_smoke import tap_file, photo_picker_item_candidates, tap_photo_picker_item

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
          <node class="android.widget.FrameLayout" package="com.google.android.providers.media.module"
                content-desc="Photo taken on Oct 26, 2026, 5:02 AM"
                clickable="true" enabled="true" bounds="[0,1217][354,1571]" />
          <node class="android.widget.FrameLayout" package="com.google.android.providers.media.module"
                content-desc="" clickable="false" bounds="[0,1217][354,1571]" />
        </hierarchy>""")
        candidates = photo_picker_item_candidates(list(root.iter("node")))
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].attrib["bounds"], "[0,1217][354,1571]")
        # Exercise the exact bounds parser and tap coordinates seen in API 35 CI.
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as picker_xml:
            picker_xml.write(ET.tostring(root, encoding="unicode"))
            picker_xml.flush()
            with mock.patch("ui_smoke.subprocess.run") as adb_run:
                tap_photo_picker_item(picker_xml.name)
            adb_run.assert_called_once_with(
                ["adb", "-s", "emulator-5554", "shell", "input", "tap", "177", "1394"],
                check=True,
                timeout=45,
            )
        # Pixel/API image-provider builds can expose either package namespace.
        android_provider = ET.fromstring("""<hierarchy><node class="android.widget.FrameLayout"
          package="com.android.providers.media.module" content-desc="Photo taken on Oct 26, 2026"
          clickable="true" enabled="true" bounds="[0,1][10,10]" /></hierarchy>""")
        self.assertEqual(len(photo_picker_item_candidates(list(android_provider.iter("node")))), 1)
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

    def test_photo_picker_retries_only_when_fresh_tree_shows_unselected_tile(self):
        source = SCRIPT.read_text(encoding="utf-8")
        picker_section = source[source.index('log "Selecting the sole visible fixture tile'):source.index('sleep 1\ndump_ui diary-picker-confirmed')]
        self.assertIn('selected="false"', picker_section)
        self.assertIn('retrying once from the fresh accessibility tree', picker_section)
        self.assertGreaterEqual(picker_section.count('tap-photo-picker-item'), 2)
        # The retry is guarded by a fresh provider tree; it must not blindly tap
        # again after the picker has returned to the app.
        self.assertIn('dump_ui diary-picker-selection-result', picker_section)
        self.assertIn('if grep -q \'package="com.google.android.providers.media.module"\'', picker_section)

    def test_review_scrolls_until_save_action_is_exposed(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("for scroll_attempt in $(seq 1 8); do", source)
        self.assertIn('dump_ui diary-review-scrolled', source)
        self.assertIn('grep -qi "Save selected tasks" "$review_xml"', source)
        self.assertIn('Save selected tasks did not become visible after 8 review scroll attempts', source)
        self.assertIn('tap_label "$review_xml" "Save selected tasks"', source)
        self.assertNotIn('tap_label ui-screenshots/diary-test/diary-review-scrolled.xml "Save selected tasks"\nfor attempt', source)
    def test_planner_scrolls_before_asserting_second_saved_task(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('for attempt in $(seq 1 8); do', source[source.index('planner_xml='):])
        self.assertIn('dump_ui diary-planner', source[source.index('planner_xml='):])
        self.assertIn('input swipe 520 1350 520 650 450', source[source.index('planner_xml='):])
        self.assertIn('grep -qi "Revise Components of Food" "$planner_xml"', source[source.index('planner_xml='):])
        self.assertIn('second saved task did not become visible after 8 planner viewport checks', source)
        self.assertIn('Both saved diary tasks visible in planner accessibility tree', source)
        self.assertIn('grep -qi "Complete Q1-5" "$planner_xml"', source)
        self.assertIn('grep -qi "Revise Components of Food" "$planner_xml"', source)
        self.assertNotIn('assert_has "$planner_xml" "Today\'s homework"', source)
        self.assertIn('current PlannerScreen does not render a "Today\'s homework" heading', source)

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

    def test_tts_preflight_extracts_voice_data_before_tutor_smoke(self):
        preflight = (ROOT / ".github" / "scripts" / "android-tts-preflight.sh").read_text(encoding="utf-8")
        self.assertIn('settings put secure tts_default_synth "$PACKAGE"', preflight)
        self.assertIn('am start -W -n "$PACKAGE/.DownloadVoiceData"', preflight)
        self.assertIn('am start -W -n "$PACKAGE/.eSpeakActivity"', preflight)
        self.assertIn("Missing base resource", preflight)
        self.assertIn("Failed to extract voice data", preflight)
        self.assertIn("refusing to run tutor UI tests with a broken TTS engine", preflight)

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


    def test_workflow_targets_api35_only_and_uses_independent_job_concurrency(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("tap-photo-picker-item", source)
        self.assertNotIn("ui_smoke.py tap-file", source)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("api-level: [35]", workflow)
        self.assertNotIn("api-level: [30, 35]", workflow)
        self.assertIn("system-image-api-level: ${{ matrix.api-level }}", workflow)
        self.assertIn("group: ${{ github.workflow }}-${{ github.ref }}-${{ matrix.api-level }}", workflow)


    def test_diary_acceptance_artifacts_are_preserved_before_smoke_cleanup(self):
        retry_script = (ROOT / ".github" / "scripts" / "android-ui-smoke-retry.sh").read_text(encoding="utf-8")
        preserve = retry_script.index('cp -a ui-screenshots/diary-test attempt-artifacts/diary-acceptance/')
        cleanup = retry_script.index('rm -rf ui-screenshots')
        self.assertLess(preserve, cleanup)
        self.assertIn('Preserved diary acceptance evidence under attempt-artifacts/diary-acceptance', retry_script)
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('attempt-artifacts/', workflow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
