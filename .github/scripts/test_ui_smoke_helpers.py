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

    def test_playback_wait_has_one_real_deadline_and_bounded_ui_operations(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("readTimeout = 50000", (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text())
        self.assertIn("readTimeout = 15000", (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text())
        self.assertIn('playback_deadline=$((SECONDS + 90))', script)
        self.assertIn('while [ "$SECONDS" -lt "$playback_deadline" ]', script)
        self.assertIn('timeout 5s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-pause-control.xml', script)
        self.assertIn("live-playback-timeout.png", script)
        self.assertIn("shell rm -f /data/local/tmp/live-pause-control.xml", script)
        self.assertIn("else\n    rm -f ui-screenshots/live-pause-control.xml", script)
        self.assertNotIn("for attempt in $(seq 1 45); do", script)

    def test_chapter_wait_matches_app_retry_window_and_rejects_stale_trees(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        helper = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        self.assertIn('chapter_deadline=$((SECONDS + 105))', script)
        self.assertIn('rm -f chapter-options.xml', script)
        self.assertIn('timeout 5s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-options.xml', script)
        self.assertIn('loading approved curriculum', helper)
        self.assertIn('curriculum service is waking up; retrying', helper)
        self.assertIn("couldn't load curriculum", helper)
        self.assertIn('chapter-options-timeout.png', script)

    def test_live_lesson_panel_does_not_expand_to_fill_unused_viewport(self):
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        start = tutor.index('if (liveLessonActive && (liveCaption.isNotBlank() || liveLessonActive))')
        end = tutor.index('item(key = "live-teaching-passage")', start)
        end = tutor.index('if (liveCaption.isNotBlank() && liveLessonActive', end)
        live_panel = tutor[start:end]
        self.assertIn('Surface(\\n                        Modifier.fillMaxWidth(),', live_panel)
        self.assertIn('Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 9.dp)', live_panel)
        self.assertNotIn('fillParentMaxHeight()', live_panel)
        self.assertNotIn('Arrangement.Center', live_panel)

    def test_selecting_concept_does_not_send_internal_prompt_as_chat(self):
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        self.assertNotIn("LaunchedEffect(chapter, topic)", tutor)
        self.assertNotIn('sendMessage(\n                 "START LESSON as a warm, patient teacher.', tutor)
        self.assertIn('status = "Preparing a textbook-grounded live lesson…"', tutor)
        self.assertIn('URL("$base/tutor/lesson-plan")', tutor)

    def test_live_lesson_invalidates_stale_chat_speech_callbacks(self):
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        self.assertIn("var speechGeneration by remember { mutableIntStateOf(0) }", tutor)
        self.assertIn('if (requestGeneration != speechGeneration)', tutor)
        self.assertIn('utteranceId != "padippupal-tutor-$speechGeneration"', tutor)
        self.assertIn('if (!liveLessonActive) status = error.message ?: "Couldn\'t reach the tutor. Please try again."', tutor)
        self.assertIn('if (speakReplies) speak(answer, onStarted = { liveCaption = answer })', tutor)
        self.assertIn("speechGeneration += 1\n        audioPlayer.value?.let", tutor)
        self.assertIn("fun stopLiveLesson() {\n        speechGeneration += 1", tutor)
        self.assertIn('it.isBlank() || it.equals("null", ignoreCase = true)', tutor)

    def test_application_failure_is_not_hidden_by_retry(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke-retry.sh").read_text()
        self.assertIn('grep -q "RESULT: APP_FAILURE" ui-screenshots/test-report.txt', script)
        self.assertIn("refusing to mask it with a retry", script)

    def test_smoke_attempt_resets_profile_before_writing_cbse_profile(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        reset = 'pm clear com.padippupal.app'
        self.assertIn(reset, script)
        self.assertIn('grep -q "Success"', script)
        self.assertLess(script.index(reset), script.index("Configuring smoke-test profile"))


if __name__ == "__main__":
    unittest.main()
