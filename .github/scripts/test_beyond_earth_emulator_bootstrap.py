#!/usr/bin/env python3
"""Regression checks for the proven hosted-Linux Android emulator bootstrap."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beyond_earth_emulator_profile import PROFILE_XML, seed_profile_preferences

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/beyond-earth-emulator-acceptance.yml"
TUTOR = ROOT / "app/src/main/java/com/padippupal/app/TutorScreen.kt"


class BeyondEarthEmulatorBootstrapTests(unittest.TestCase):
    def test_ui_acceptance_reuses_last_successful_hosted_linux_kvm_runtime(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("Enable KVM hardware acceleration for the emulator", workflow)
        self.assertIn("test -r /dev/kvm && test -w /dev/kvm", workflow)
        self.assertIn("reactivecircus/android-emulator-runner@v2", workflow)
        self.assertIn("api-level: 35", workflow)
        self.assertIn("target: google_apis", workflow)
        self.assertIn("arch: x86_64", workflow)
        self.assertIn("-gpu swiftshader_indirect", workflow)
        self.assertIn('emulator" -accel-check', workflow)
        self.assertIn("python3 .github/scripts/test_beyond_earth_emulator.py", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertNotIn("macos-", workflow)
        self.assertNotIn("-accel off", workflow)

    def test_visual_acceptance_does_not_depend_on_device_tts(self):
        tutor = TUTOR.read_text(encoding="utf-8")
        segment_start = tutor.index("fun playLiveSegment(index: Int)")
        caption_published = tutor.index("liveCaption = words", segment_start)
        speech_started = tutor.index("speak(words", segment_start)
        self.assertLess(caption_published, speech_started)

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
