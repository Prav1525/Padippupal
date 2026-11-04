#!/usr/bin/env python3
"""Regression checks for the Beyond Earth visual-only emulator bootstrap."""
from pathlib import Path
import unittest

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


if __name__ == "__main__":
    unittest.main()
