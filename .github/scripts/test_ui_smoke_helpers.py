#!/usr/bin/env python3
"""Regression tests for accessibility-tree selectors; no emulator required."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_smoke import concept_candidates, exact_color_mask



class ScreenshotMaskTests(unittest.TestCase):
    def test_exact_color_mask_counts_pixels_and_returns_their_bounds(self):
        from PIL import Image, ImageDraw
        target = (216, 232, 183)
        image = Image.new("RGB", (10, 10), (0, 0, 0))
        ImageDraw.Draw(image).rectangle((2, 3, 4, 4), fill=target)
        mask = exact_color_mask(image, target)
        self.assertEqual(mask.histogram()[255], 6)
        self.assertEqual(mask.getbbox(), (2, 3, 5, 5))



class AndroidManifestContractTests(unittest.TestCase):
    def test_android_11_tts_service_is_visible_to_package_manager(self):
        manifest = Path(__file__).resolve().parents[2] / "app" / "src" / "main" / "AndroidManifest.xml"
        content = manifest.read_text(encoding="utf-8")
        self.assertRegex(
            content,
            r'<queries>\s*<intent>\s*<action android:name="android.intent.action.TTS_SERVICE"',
            "Android 11+ must be allowed to discover the system TextToSpeech service",
        )


class ConceptCandidateTests(unittest.TestCase):
    def test_compose_row_without_clickable_flag_is_still_selectable(self):
        root = ET.fromstring("""<hierarchy>
          <node text="Choose concept" bounds="[10,10][300,60]" clickable="true" enabled="true"/>
          <node text="1. All 1s" bounds="[10,70][300,130]" clickable="false" enabled="true"/>
          <node text="2. Growing number patterns" bounds="[10,140][300,200]" clickable="false"/>
          <node text="Done" bounds="[10,220][300,270]" clickable="true" enabled="true"/>
        </hierarchy>""")
        candidates = concept_candidates(list(root.iter("node")))
        self.assertEqual([n.attrib["text"] for n in candidates],
                         ["1. All 1s", "2. Growing number patterns"])

    def test_invalid_or_explicitly_disabled_rows_are_rejected(self):
        root = ET.fromstring("""<hierarchy>
          <node text="1. No bounds" clickable="true" enabled="true"/>
          <node text="2. Disabled" bounds="[0,0][20,20]" enabled="false"/>
          <node text="Chapter 1" bounds="[0,0][20,20]" enabled="true"/>
          <node text="3. Valid row" bounds="[0,20][100,60]" enabled="true"/>
        </hierarchy>""")
        candidates = concept_candidates(list(root.iter("node")))
        self.assertEqual([n.attrib["text"] for n in candidates], ["3. Valid row"])


class RetryIsolationTests(unittest.TestCase):
    def test_each_retry_clears_old_xml_and_screenshot_evidence(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke-retry.sh").read_text()
        self.assertIn("rm -rf ui-screenshots", script)
        self.assertIn("rm -f home.xml tutor.xml", script)
        self.assertLess(script.index("rm -rf ui-screenshots"), script.index("bash .github/scripts/android-ui-smoke.sh"))

    def test_smoke_attempt_resets_profile_and_saved_tutor_session_before_writing_cbse_profile(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        profile_reset = 'run-as com.padippupal.app rm -f shared_prefs/padippupal_profile.xml'
        session_reset = 'run-as com.padippupal.app rm -f shared_prefs/padippupal_tutor_sessions.xml'
        self.assertIn(profile_reset, script)
        self.assertIn(session_reset, script)
        setup = script.index("Configuring smoke-test profile")
        self.assertLess(script.index(profile_reset), setup)
        self.assertLess(script.index(session_reset), setup)


if __name__ == "__main__":
    unittest.main()
