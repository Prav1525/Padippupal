#!/usr/bin/env python3
"""Regression tests for accessibility-tree selectors; no emulator required."""
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_smoke import (assert_composer_question, assert_home, concept_candidates, exact_color_mask,
                       exact_text_candidates, tap, tap_input)



class ExactSelectorTests(unittest.TestCase):
    def test_teach_selector_does_not_match_chat_text_containing_teach(self):
        root = ET.fromstring("""<hierarchy>
          <node text="Teach this as a patient primary-school teacher." bounds="[0,0][300,80]" clickable="true"/>
          <node text="▶ Teach" bounds="[200,0][300,80]" clickable="false"/>
          <node text="▶ Teach" bounds="[190,0][310,90]" clickable="true"/>
        </hierarchy>""")
        # The production helper must reject longer chat text containing "teacher".
        candidates = exact_text_candidates(list(root.iter("node")), "▶ Teach")
        self.assertEqual(len(candidates), 2)
        selected = next((n for n in candidates if n.attrib.get("clickable") == "true"), candidates[0])
        self.assertEqual(selected.attrib["bounds"], "[190,0][310,90]")

    def test_accessibility_content_description_can_select_send_button(self):
        root = ET.fromstring("""<hierarchy>
          <node text="" content-desc="Send question" bounds="[900,800][1040,980]" clickable="true"/>
        </hierarchy>""")
        candidates = exact_text_candidates(list(root.iter("node")), "Send question")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].attrib["content-desc"], "Send question")

    def test_follow_up_smoke_focuses_edit_text_and_asserts_question_before_send(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("tap-input follow-up-input.xml", script)
        self.assertIn("assert-composer-question follow-up-typed.xml", script)
        self.assertIn('tap follow-up-typed.xml "Send question"', script)
        self.assertIn("follow-up-typed.xml", script)

    def test_composer_assertion_rejects_empty_input_before_send(self):
        empty = ET.fromstring("""<hierarchy>
          <node class="android.widget.EditText" text="" bounds="[0,0][300,80]"/>
        </hierarchy>""")
        path = Path(__file__).resolve().parent / "tmp-empty-composer-test.xml"
        try:
            path.write_text(ET.tostring(empty, encoding="unicode"))
            with self.assertRaises(SystemExit):
                assert_composer_question(str(path))
        finally:
            path.unlink(missing_ok=True)

    def test_tap_selector_checks_content_description_as_well_as_text(self):
        source = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        tap_body = source[source.index("def tap(path, target):"):source.index("\ndef has_label", source.index("def tap(path, target):"))]
        self.assertIn('description = node.attrib.get("content-desc", "").strip()', tap_body)
        self.assertIn('target.lower() in description.lower()', tap_body)

    def test_live_lesson_client_timeout_exceeds_two_backend_generation_attempts(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        lesson_plan = tutor[tutor.index('URL("$base/tutor/lesson-plan")'):]
        self.assertIn("connection.readTimeout = 120000", lesson_plan[:900])
        self.assertIn("TOPIC GUARDRAIL: All 1s means a sequence that repeats the number 1 only", tutor)
        self.assertIn("Every teaching segment must explain that repeated-one sequence", tutor)
        validator = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                     "java" / "com" / "padippupal" / "app" / "AllOnesTopicValidator.kt").read_text()
        self.assertIn("no All 1s explanation or approved short transition", validator)
        smoke = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn('tap-exact ready-to-teach.xml "▶ Teach"', smoke)
        self.assertNotIn('tap ready-to-teach.xml "Teach"', smoke)


class HomeLayoutContractTests(unittest.TestCase):
    def test_home_smoke_contract_matches_refreshed_primary_action(self):
        root = ET.fromstring("""<hierarchy>
          <node text="YOUR LEARNING SPACE" bounds="[0,0][300,50]"/>
          <node text="YOUR PERSONAL TUTOR" bounds="[0,50][300,100]"/>
          <node text="Start learning" bounds="[0,100][300,150]"/>
        </hierarchy>""")
        path = Path(__file__).resolve().parent / "tmp-home-layout-test.xml"
        try:
            path.write_text(ET.tostring(root, encoding="unicode"))
            assert_home(str(path))
        finally:
            path.unlink(missing_ok=True)

    def test_home_has_one_primary_tutor_action_and_compact_secondary_actions(self):
        source = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                  "java" / "com" / "padippupal" / "app" / "MainActivity.kt").read_text()
        home = source[source.index("private fun Home("):source.index("@Composable private fun Stat(")]
        self.assertIn('Text(if (tamil) "பாடத்தைத் தொடங்கு" else "Start learning"', home)
        self.assertIn('else "Scan homework"', home)
        self.assertIn('else "Exam practice"', home)
        self.assertIn('else "Connect your syllabus"', home)
        self.assertNotIn('Tile("My subjects"', home)
        self.assertNotIn('Tile("Study planner"', home)
        self.assertNotIn('"01 / 04"', home)

    def test_caption_keeps_original_whitespace_and_paragraph_boundaries(self):
        source = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                  "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        caption = source[source.index("private fun WordByWordCaption("):source.index("@Composable\\nprivate fun InteractiveLessonLab(")]
        self.assertIn("text.substring(cursor, matchStart)", caption)
        self.assertNotIn("sentencesInParagraph", caption)
        self.assertIn("lineHeight = 26.sp", caption)


class TutorPromptContractTests(unittest.TestCase):
    def test_prompt_has_no_legacy_short_step_or_forced_checkpoint_rules(self):
        backend = (Path(__file__).resolve().parents[2] / "backend" / "app.py").read_text()
        start = backend.index("system_prompt = f")
        end = backend.index('"""', start + len('system_prompt = f"""'))
        prompt = backend[start:end]
        self.assertIn("teach the complete selected topic in one coherent lesson", prompt)
        self.assertIn("one connected explanation", prompt)
        self.assertNotIn("teach only its current small step", prompt)
        self.assertNotIn("usually 20–45 words total", prompt)
        self.assertNotIn("Do not answer your own question or continue to the next lesson step before the child responds", prompt)
        self.assertIn("Ask at most one specific practice question after the full explanation", prompt)

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


class BackendWarmupRegressionTests(unittest.TestCase):
    def test_emulator_workflow_uses_deterministic_local_backend_fixture(self):
        workflow = (Path(__file__).resolve().parents[1] / "workflows" /
                    "android-ui-smoke.yml").read_text()
        self.assertIn("Start deterministic tutor smoke API", workflow)
        self.assertIn("http://127.0.0.1:8765/health", workflow)
        self.assertIn("http://10.0.2.2:8765", workflow)
        self.assertIn('test "$ready" -eq 1', workflow)
        self.assertNotIn("https://padippupal-curriculum-api.onrender.com", workflow)
        self.assertLess(workflow.index("Start deterministic tutor smoke API"), workflow.index("Launch app in Android emulator"))


class CurriculumRetryRegressionTests(unittest.TestCase):
    def test_transient_outline_failures_retry_and_surface_final_error(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn("fun loadCurriculumOutline(forSubject: String, attempt: Int = 1)", tutor)
        self.assertIn("else if (attempt < 3)", tutor)
        self.assertIn("postDelayed", tutor)
        self.assertIn("Couldn't load the chapter list.", tutor)
        self.assertIn("if (subject != forSubject) return@post", tutor)


class TtsFailureRegressionTests(unittest.TestCase):
    def test_tutor_handles_tts_binding_security_exception_without_crashing(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn("catch (error: SecurityException)", tutor)
        self.assertIn("Voice engine could not initialize.", tutor)
        self.assertIn("runCatching { engine?.shutdown() }", tutor)
        smoke = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("Voice engine could not initialize", smoke)
        self.assertIn("speech engine did not finish starting", smoke)

    def test_tts_callbacks_are_bound_to_the_current_utterance_generation(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn('val utteranceId = "padippupal-tutor-$speechGeneration"', tutor)
        self.assertGreaterEqual(tutor.count("utteranceId != activeTtsUtteranceId || !speechActive"), 4)
        self.assertIn("activeTtsUtteranceId = \"\"", tutor)
        self.assertIn("if (result == TextToSpeech.ERROR)", tutor)

    def test_smoke_workflow_does_not_force_the_incompatible_hayai_engine(self):
        workflow = (Path(__file__).resolve().parents[1] / "workflows" /
                    "android-ui-smoke.yml").read_text()
        self.assertIn("api-level: [35]", workflow)
        self.assertNotIn("api-level: [30, 35]", workflow)
        self.assertIn("api-level: ${{ matrix.api-level }}", workflow)
        self.assertIn("system-image-api-level: ${{ matrix.api-level }}", workflow)
        self.assertIn("target: google_apis", workflow)
        self.assertNotIn("system-image: google_apis", workflow)
        self.assertIn("bash .github/scripts/android-tts-preflight.sh", workflow)
        self.assertNotIn("dev.ahmedmohamed.hayaitts", workflow)
        self.assertNotIn("hayaitts-x86_64", workflow)
        preflight = (Path(__file__).resolve().parent / "android-tts-preflight.sh").read_text()
        self.assertIn('readonly PACKAGE="com.reecedunn.espeak"', preflight)
        self.assertIn("https://f-droid.org/repo/index-v1.jar", preflight)
        self.assertIn("sha256sum --check --status", preflight)
        self.assertIn('settings put secure tts_default_synth "$PACKAGE"', preflight)
        self.assertIn("query-services -a android.intent.action.TTS_SERVICE", preflight)

    def test_live_smoke_reports_missing_tts_before_pause_stop_control_error(self):
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        failure_check = smoke.index('voice_failures = (')
        controls_check = smoke.index('if "pause" not in joined or "stop" not in joined:')
        self.assertLess(failure_check, controls_check)
        self.assertIn('"voice engine could not initialize"', smoke)
        self.assertIn('"speech engine did not finish starting"', smoke)


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
        self.assertIn("rm -f home.xml settings.xml ready-to-teach.xml", script)
        for evidence_file in ("live-resumed.xml", "live-complete.xml", "live-lesson.xml", "follow-up.xml"):
            self.assertIn(evidence_file, script)
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


class CompleteLessonRegressionTests(unittest.TestCase):
    def test_live_lesson_joins_segments_and_does_not_create_checkpoints(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn("The API segments are transport chunks, not separate learner-facing steps.", tutor)
        self.assertIn('listOf(completeLesson)', tutor)
        self.assertIn("currentCheckpoint = \"\"", tutor)
        self.assertIn("The lesson was too short to explain the selected topic completely.", tutor)
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        self.assertIn("Per-segment checkpoint or animation UI reappeared", smoke)
        self.assertNotIn("missing its passive auto-playing concept animation", smoke)

    def test_spoken_caption_groups_sentences_into_natural_paragraphs(self):
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        self.assertIn("separate paragraphs only after every third sentence", tutor)
        self.assertIn(r'append(if (endsSentence && sentencesInParagraph % 3 == 0) "\n\n" else " ")', tutor)
        self.assertIn("offset += if (endsSentence && sentencesInParagraph % 3 == 0) 2 else 1", tutor)

    def test_completed_lesson_is_kept_for_follow_up_chat(self):
        root = Path(__file__).resolve().parents[2]
        tutor = (root / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        self.assertIn('messages.add(TutorMessage("assistant", completedLesson))', tutor)
        self.assertIn('status = "Live lesson complete."', tutor)
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        self.assertIn("def assert_completed_lesson(path):", smoke)
        self.assertIn("def assert_followup_answer(path):", smoke)
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("Waiting for playback to finish", script)
        self.assertIn("assert-followup follow-up.xml", script)

    def test_smoke_waits_for_full_caption_and_rejects_checkpoint_ui(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("assert-live live-lesson.xml >/dev/null 2>&1", script)
        self.assertIn("live-complete.xml", script)
        self.assertNotIn("explicit understanding checkpoint", script)


class PreviousScreenSelectionTests(unittest.TestCase):
    def test_tutor_ready_screen_does_not_duplicate_selection_controls(self):
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        self.assertIn('if "change" in labels:', smoke)
        self.assertNotIn('if "change" not in labels:', smoke)
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        self.assertNotIn("TextButton(onClick = { showLessonSettings = true }", tutor)
        self.assertIn("onClick = { startLiveLesson() }", tutor)

    def test_lesson_selection_precedes_tutor_in_app_and_smoke_flow(self):
        root = Path(__file__).resolve().parents[2]
        main = (root / "app/src/main/java/com/padippupal/app/MainActivity.kt").read_text()
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("go(Page.LESSON_SETUP)", main)
        self.assertIn("Page.LESSON_SETUP -> TutorScreen", main)
        self.assertIn("setupOnly = true", main)
        self.assertIn("assert-settings settings.xml", script)
        self.assertIn("assert-tutor ready-to-teach.xml", script)
        self.assertNotIn('tap tutor.xml "Change"', script)


if __name__ == "__main__":
    unittest.main()
