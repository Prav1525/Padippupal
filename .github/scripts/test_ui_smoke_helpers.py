#!/usr/bin/env python3
"""Regression tests for accessibility-tree selectors; no emulator required."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_smoke import concept_candidates, has_pause_control, assert_paused, assert_resumed


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


class PlaybackStateAssertionTests(unittest.TestCase):
    def test_pause_control_requires_visible_bounded_pause_or_resume_button(self):
        root = ET.fromstring("""<hierarchy>
          <node text="PAUSE FOR CHECK-IN" bounds="[10,10][300,60]" clickable="false"/>
          <node text="Pause" bounds="[10,70][120,120]" clickable="false" enabled="true"/>
          <node text="Resume" bounds="[130,70][240,120]" enabled="false"/>
        </hierarchy>""")
        path = Path(self._temporary_xml(ET.tostring(root, encoding="unicode")))
        try:
            self.assertTrue(has_pause_control(str(path)))
        finally:
            path.unlink(missing_ok=True)

    def test_paused_and_resumed_assertions_check_state_labels(self):
        paused = Path(self._temporary_xml("""<hierarchy>
          <node text="LESSON PAUSED"/>
          <node text="Lesson paused. Resume will replay this short segment from the beginning."/>
          <node text="Resume" bounds="[10,10][100,50]"/>
        </hierarchy>"""))
        resumed = Path(self._temporary_xml("""<hierarchy>
          <node text="TEACHER IS SPEAKING"/>
        </hierarchy>"""))
        try:
            assert_paused(str(paused))
            assert_resumed(str(resumed))
        finally:
            paused.unlink(missing_ok=True)
            resumed.unlink(missing_ok=True)

    @staticmethod
    def _temporary_xml(content):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as file:
            file.write(content)
            return file.name


class RetryIsolationTests(unittest.TestCase):
    def test_each_retry_clears_old_xml_and_screenshot_evidence(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke-retry.sh").read_text()
        self.assertIn("rm -rf ui-screenshots", script)
        self.assertIn("rm -f home.xml tutor.xml", script)
        self.assertLess(script.index("rm -rf ui-screenshots"), script.index("bash .github/scripts/android-ui-smoke.sh"))

    def test_playback_wait_covers_lesson_plan_and_hosted_voice_deadlines(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("readTimeout = 50000", (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text())
        self.assertIn("readTimeout = 15000", (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text())
        self.assertIn("for attempt in $(seq 1 45); do", script)
        self.assertIn("up to 90 seconds", script)

    def test_smoke_attempt_resets_profile_before_writing_cbse_profile(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        reset = 'pm clear com.padippupal.app'
        self.assertIn(reset, script)
        self.assertIn('grep -q "Success"', script)
        self.assertLess(script.index(reset), script.index("Configuring smoke-test profile"))


if __name__ == "__main__":
    unittest.main()
