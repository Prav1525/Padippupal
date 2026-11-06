#!/usr/bin/env python3
"""Regression checks for the Beyond Earth hardware-accelerated emulator bootstrap."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beyond_earth_emulator_profile import PROFILE_XML, seed_profile_preferences

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/beyond-earth-emulator-acceptance.yml"
BOOTSTRAP = ROOT / ".github/scripts/run_beyond_earth_emulator_acceptance.sh"
TUTOR = ROOT / "app/src/main/java/com/padippupal/app/TutorScreen.kt"


class BeyondEarthEmulatorBootstrapTests(unittest.TestCase):
    def test_ui_acceptance_requires_linux_kvm_and_separate_hosted_validation(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("validate-and-build:", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        ui_job = workflow.split("  beyond-earth-emulator:", 1)[1]
        self.assertIn("needs: validate-and-build", ui_job)
        self.assertIn("runs-on: [self-hosted, linux, x64, kvm]", ui_job)
        self.assertIn("reactivecircus/android-emulator-runner@v2", ui_job)
        self.assertIn("api-level: 35", ui_job)
        self.assertIn("arch: x86_64", ui_job)
        self.assertIn("-gpu host", ui_job)
        self.assertIn("script: python3 .github/scripts/test_beyond_earth_emulator.py", ui_job)
        self.assertNotIn("macos-", workflow)
        self.assertNotIn("swiftshader", ui_job)

    def test_visual_acceptance_does_not_depend_on_device_tts(self):
        tutor = TUTOR.read_text(encoding="utf-8")
        segment_start = tutor.index("fun playLiveSegment(index: Int)")
        caption_published = tutor.index("liveCaption = words", segment_start)
        speech_started = tutor.index("speak(words", segment_start)
        self.assertLess(caption_published, speech_started)

    def test_legacy_manual_bootstrap_is_not_used_by_acceptance_workflow(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("run: bash .github/scripts/run_beyond_earth_emulator_acceptance.sh", workflow)
        self.assertIn("script: python3 .github/scripts/test_beyond_earth_emulator.py", workflow)

    def test_profile_seed_uses_safe_adb_shell_argument_boundaries(self):
        calls = []

        def fake_run(args, **kwargs):
            calls.append((args, kwargs))

        adb = ["adb", "-s", "emulator-5554"]
        seed_profile_preferences(adb, fake_run)

        self.assertEqual(
            calls[0][0],
            adb + ["shell", "run-as", "com.padippupal.app", "mkdir", "-p", "shared_prefs"],
        )
        self.assertEqual(
            calls[1][0],
            adb + [
                "shell",
                "run-as com.padippupal.app sh -c 'cat > shared_prefs/padippupal_profile.xml'",
            ],
        )
        self.assertEqual(calls[1][1]["input"], PROFILE_XML)
        self.assertIs(calls[1][1]["text"], True)
        self.assertNotIn("mkdir -p", calls[1][0][-1])


if __name__ == "__main__":
    unittest.main()
