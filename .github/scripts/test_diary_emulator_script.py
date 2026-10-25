#!/usr/bin/env python3
"""Static regression checks for the diary emulator's ADB command construction."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "diary_crop_emulator_test.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "android-ui-smoke.yml"


class DiaryEmulatorCommandRegressionTests(unittest.TestCase):
    def test_picker_hierarchy_dump_is_pulled_before_parsing(self):
        source = SCRIPT.read_text(encoding="utf-8")
        # The picker switches to list mode inside an embedded Python helper,
        # which dumps and pulls the hierarchy directly rather than using dump_ui.
        self.assertIn('shell content insert --uri content://media/external/images/media', source)
        self.assertIn('content query --uri content://media/external/images/media', source)
        self.assertIn('fixture exists in shared storage but is not indexed in MediaStore', source)
        # The legacy images/media endpoint rejects modern display_name and
        # relative_path insert columns; verify by querying rows, not a quoted
        # selection expression that Android's content CLI tokenizes incorrectly.
        self.assertNotIn('--bind display_name:s:', source)
        self.assertNotIn('--bind relative_path:s:', source)
        self.assertNotIn('--where "_display_name=', source)
        self.assertIn('--projection _id:_display_name:_data | grep -Fq "PadippuPal-diary-test.jpg"', source)
        self.assertIn('subprocess.run(adb+["uiautomator","dump",remote]', source)
        self.assertIn('subprocess.run(["adb","-s","emulator-5554","pull",remote,local]', source)
        self.assertIn('dump("/data/local/tmp/diary-picker-list.xml","ui-screenshots/diary-test/diary-picker-list.xml")', source)
        dump = source.index('dump("/data/local/tmp/diary-picker-list.xml"')
        parse = source.index('path="ui-screenshots/diary-test/diary-picker-list.xml"; ns=nodes(path)')
        self.assertLess(dump, parse)

    def test_picker_selects_fixture_and_uses_observed_select_action(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"padippupal-diary-test.jpg" in (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()', source)
        self.assertIn('r"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]"', source)
        self.assertIn('print(f"Long-press filename to enter selection mode', source)
        self.assertIn('["input","swipe",str(x),str(y),str(x),str(y),"1100"]', source)
        self.assertIn('dump("/data/local/tmp/diary-picker-selection-mode.xml"', source)
        self.assertIn('label in ("select","open","use","choose","select file")', source)
        self.assertIn('if not actions: raise SystemExit("No visible Select action', source)
        self.assertIn('Tap observed DocumentsUI action', source)
        self.assertNotIn("Preview the file PadippuPal-diary-test.jpg", source)
        self.assertNotIn("Diary filename disappeared after preview", source)

    def test_picker_dump_is_pulled_before_it_is_parsed(self):
        source = SCRIPT.read_text(encoding="utf-8")
        dump = source.index('dump("/data/local/tmp/diary-picker-list.xml"')
        parse = source.index('path="ui-screenshots/diary-test/diary-picker-list.xml"; ns=nodes(path)')
        self.assertLess(dump, parse)
        self.assertIn('ns=nodes(path)', source[parse:])
        self.assertIn('def nodes(path): return list(ET.parse(path).getroot().iter("node"))', source[:parse])

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
