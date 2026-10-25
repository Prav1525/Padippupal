#!/usr/bin/env python3
"""Static regression checks for the diary emulator's ADB command construction."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github" / "scripts" / "diary_crop_emulator_test.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "android-ui-smoke.yml"


class DiaryEmulatorCommandRegressionTests(unittest.TestCase):
    def test_picker_hierarchy_dump_has_exactly_one_shell_argument(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            'subprocess.run(adb+["uiautomator","dump","/data/local/tmp/diary-picker-after-row.xml"]',
            source,
        )
        self.assertNotIn(
            'subprocess.run(adb+["shell","uiautomator","dump","/data/local/tmp/diary-picker-after-row.xml"]',
            source,
        )

    def test_picker_dump_is_pulled_before_it_is_parsed(self):
        source = SCRIPT.read_text(encoding="utf-8")
        dump = source.index('subprocess.run(adb+["uiautomator","dump","/data/local/tmp/diary-picker-after-row.xml"]')
        pull = source.index('subprocess.run(["adb","-s","emulator-5554","pull","/data/local/tmp/diary-picker-after-row.xml"')
        parse = source.index('ET.parse("ui-screenshots/diary-test/diary-picker-after-row.xml")')
        self.assertLess(dump, pull)
        self.assertLess(pull, parse)

    def test_failure_register_exists_and_names_regression_expectations(self):
        register = ROOT / "docs" / "TEST_FAILURE_REGISTER.md"
        self.assertTrue(register.is_file(), "Recurring failures must be recorded in the repository")
        text = register.read_text(encoding="utf-8")
        self.assertIn("root cause", text.lower())
        self.assertIn("regression test", text.lower())
        self.assertIn("3dde5052105d82c1c54fa5968d6c495baef62b54", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
