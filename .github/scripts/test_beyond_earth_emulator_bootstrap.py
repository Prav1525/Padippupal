#!/usr/bin/env python3
"""Regression checks for the Beyond Earth visual-only emulator bootstrap."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beyond_earth_emulator_profile import PROFILE_XML, seed_profile_preferences

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / ".github/scripts/run_beyond_earth_emulator_acceptance.sh"
TUTOR = ROOT / "app/src/main/java/com/padippupal/app/TutorScreen.kt"


class BeyondEarthEmulatorBootstrapTests(unittest.TestCase):
    def test_uses_lightweight_aosp_image_on_software_emulation_runner(self):
        script = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("system-images;android-35;default;x86_64", script)
        self.assertNotIn("google_apis_playstore", script)
        self.assertIn("-accel off", script)
        self.assertNotIn("accel-check", script)

    def test_visual_acceptance_does_not_depend_on_device_tts(self):
        script = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertNotIn("android-tts-preflight.sh", script)
        tutor = TUTOR.read_text(encoding="utf-8")
        segment_start = tutor.index("fun playLiveSegment(index: Int)")
        caption_published = tutor.index("liveCaption = words", segment_start)
        speech_started = tutor.index("speak(words", segment_start)
        self.assertLess(caption_published, speech_started)

    def test_adb_offline_state_has_bounded_recovery(self):
        script = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn('timeout 8s "$ADB" reconnect offline', script)
        self.assertIn("adb_server_restart_attempted", script)
        self.assertIn("offline_since", script)
        self.assertIn("wait_for_adb_device 120", script)

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
