#!/usr/bin/env python3
"""Regression tests for accessibility-tree selectors; no emulator required."""
import re
import sys
import tempfile
from unittest.mock import patch
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_smoke import (assert_composer_question, assert_followup_question, assert_home, assert_live, concept_candidates, exact_color_mask,
                       exact_text_candidates, main as ui_smoke_main, tap, tap_input)



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
        self.assertIn('tap follow-up-typed.xml "Send follow-up question"', script)
        self.assertIn("assert-followup-question follow-up-sent.xml", script)
        self.assertIn("follow-up-sent.xml", script)
        self.assertIn("follow-up-typed.xml", script)

    def test_follow_up_question_assertion_checks_posted_chat_bubble(self):
        posted = ET.fromstring("""<hierarchy>
          <node class="android.widget.TextView" text="Why does All 1s repeat?" bounds="[0,0][300,80]"/>
        </hierarchy>""")
        path = Path(__file__).resolve().parent / "tmp-follow-up-question-test.xml"
        try:
            path.write_text(ET.tostring(posted, encoding="unicode"))
            assert_followup_question(str(path))
        finally:
            path.unlink(missing_ok=True)

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

    def test_live_lesson_polling_clears_stale_accessibility_trees(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        poll_start = script.index('log "Waiting for each live module')
        poll_end = script.index('log "Waiting for playback to finish', poll_start)
        poll = script[poll_start:poll_end]
        self.assertIn("rm -f live-lesson.xml", poll)
        self.assertIn('shell rm -f /data/local/tmp/live-lesson.xml', poll)
        self.assertLess(poll.index('shell rm -f /data/local/tmp/live-lesson.xml'), poll.index('shell uiautomator dump /data/local/tmp/live-lesson.xml'))

        completion_start = script.index('log "Waiting for playback to finish')
        completion_end = script.index('assert-completed-lesson live-complete.xml ui-screenshots/live-module-4.xml | tee', completion_start)
        completion_poll = script[completion_start:completion_end]
        self.assertIn("rm -f live-complete.xml", completion_poll)
        self.assertIn('shell rm -f /data/local/tmp/live-complete.xml', completion_poll)
        self.assertLess(completion_poll.index('shell rm -f /data/local/tmp/live-complete.xml'), completion_poll.index('shell uiautomator dump /data/local/tmp/live-complete.xml'))

    def test_live_lesson_assertion_reads_icon_only_pause_and_stop_labels(self):
        root = ET.fromstring("""<hierarchy>
          <node text="Live lesson · segment 1 of 4" bounds="[0,0][300,50]"/>
          <node text="NOW LEARNING" bounds="[0,50][300,75]"/>
          <node text="What is an All 1s pattern" bounds="[0,75][300,105]"/>
          <node text="The All 1s pattern repeats the same number each time. Each term stays 1, and the number does not increase or decrease. The rule is simple: write 1 again each time. This is a complete explanation of the repeated-one pattern with enough detail to teach the selected concept clearly." bounds="[0,105][300,305]"/>
          <node text="An All 1s example" bounds="[0,305][300,330]"/>
          <node text="" content-desc="What is an All 1s pattern diagram" bounds="[0,330][300,360]"/>
          <node text="A common mistake" bounds="[0,360][300,390]"/>
          <node text="Quick recap" bounds="[0,390][300,420]"/>
          <node text="" content-desc="Pause playback" bounds="[0,420][100,470]"/>
          <node text="" content-desc="Stop lesson" bounds="[100,420][200,470]"/>
        </hierarchy>""")
        path = Path(__file__).resolve().parent / "tmp-live-lesson-accessibility-test.xml"
        try:
            path.write_text(ET.tostring(root, encoding="unicode"))
            assert_live(str(path))
        finally:
            path.unlink(missing_ok=True)

    def test_live_assertion_accepts_a_short_first_segment_before_later_segments(self):
        root = ET.fromstring("""<hierarchy>
          <node text="Live lesson · segment 1 of 4" bounds="[0,0][300,50]"/>
          <node text="NOW LEARNING" bounds="[0,50][300,75]"/>
          <node text="What is an All 1s pattern" bounds="[0,75][300,105]"/>
          <node text="The All 1s pattern repeats the same number each time. Each term stays 1, and the number does not increase or decrease. The rule stays the same." bounds="[0,105][300,255]"/>
          <node text="An All 1s example" bounds="[0,255][300,285]"/>
          <node text="" content-desc="What is an All 1s pattern diagram" bounds="[0,285][300,315]"/>
          <node text="A common mistake" bounds="[0,315][300,345]"/>
          <node text="Quick recap" bounds="[0,345][300,375]"/>
          <node text="" content-desc="Pause playback" bounds="[0,375][100,425]"/>
          <node text="" content-desc="Stop lesson" bounds="[100,375][200,425]"/>
        </hierarchy>""")
        path = Path(__file__).resolve().parent / "tmp-live-short-segment-test.xml"
        try:
            path.write_text(ET.tostring(root, encoding="unicode"))
            assert_live(str(path))
        finally:
            path.unlink(missing_ok=True)

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


class SynthesisInlineVisualContractTests(unittest.TestCase):
    def test_smoke_api_supplies_a_source_mapped_original_2d_visual(self):
        fixture = (Path(__file__).resolve().parent / "tutor_smoke_api.py").read_text()
        self.assertIn('"scene_type": "synthesis_static"', fixture)
        self.assertIn('"title": "All 1s pattern visual"', fixture)
        self.assertIn('"nodes": ["1", "1", "1", "1", "1"]', fixture)
        self.assertIn('"source_chunk_ids": ["smoke-source"]', fixture)
        self.assertIn('"animation": "narration_synced_2d"', fixture)

    def test_first_live_fixture_segment_contains_the_exact_mapped_visual_caption(self):
        fixture = (Path(__file__).resolve().parent / "tutor_smoke_api.py").read_text()
        first = fixture.split('"id": "all-ones-definition"', 1)[1].split('"id": "all-ones-example"', 1)[0]
        self.assertIn("Each term stays 1. The pattern repeats without growing.", first)

    def test_live_smoke_checks_accessible_image_mapping_without_caption_text(self):
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        start = smoke.index("def active_module_index(path):")
        end = smoke.index("\ndef exact_color_mask", start)
        live = smoke[start:end]
        self.assertNotIn("Live lesson is not exposing its active playback segment progress", live)
        self.assertIn('"what is an all 1s pattern"', live)
        self.assertIn('"quick recap"', live)
        self.assertIn('active_module_index(path)', live)
        self.assertIn('matching mapped image', live)
        self.assertNotIn('"each term stays 1" not in joined', live)

    def test_live_smoke_accepts_inline_visual_but_still_rejects_separate_visual_overlay(self):
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        start = smoke.index("def active_module_index(path):")
        end = smoke.index("\ndef exact_color_mask", start)
        live = smoke[start:end]
        self.assertNotIn("Live lesson is not exposing its active playback segment progress", live)
        self.assertIn('"what is an all 1s pattern"', live)
        self.assertIn('"quick recap"', live)
        self.assertIn('active_module_index(path)', live)
        self.assertIn('matching mapped image', live)
        self.assertNotIn('"each term stays 1" not in joined', live)
        self.assertNotIn('"watch the pattern"', live)
        self.assertIn("assert-live-layout", (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text())


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
        smoke = (Path(__file__).resolve().parents[2] / ".github" / "scripts" / "android-ui-smoke.sh").read_text()
        self.assertIn('tap home.xml "Start learning"', smoke)
        self.assertNotIn('tap home.xml "Begin lesson"', smoke)


class TutorInlineVisualContractTests(unittest.TestCase):
    def test_curriculum_diagrams_and_source_page_references_render_inline(self):
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        start = tutor.index("private fun DatabaseInteractiveLessonLab(")
        end = tutor.index("private enum class LessonVisualKind", start)
        lab = tutor[start:end]
        self.assertIn('"fraction_builder" -> {', lab)
        self.assertIn("drawArc(", lab)
        self.assertIn('lesson.optJSONArray("source_refs")', lab)
        self.assertIn('sourceRef.optInt("page_start", 0)', lab)
        self.assertIn('sourceRef.optInt("page_end", pageStart)', lab)
        backend = (Path(__file__).resolve().parents[2] / "backend/app.py").read_text()
        row_start = backend.index("def _interactive_lesson_row(")
        row_end = backend.index("def find_interactive_lesson(", row_start)
        self.assertIn('"source_refs": payload.get("source_refs", [])', backend[row_start:row_end])
        lesson_plan = backend[backend.index('def tutor_lesson_plan('):backend.index('@app.post("/tutor/chat")')]
        self.assertIn('"interactive_lesson": matched_visual', lesson_plan)
        self.assertNotIn("This product mode is text-only", lesson_plan)
        self.assertIn("optional inline concept visuals", backend)
        self.assertIn('response.optJSONObject("interactive_lesson")', tutor)
        live_start = tutor.index('if (liveLessonActive) {')
        live_end = tutor.index('Inline learner checkpoint', live_start)
        live = tutor[live_start:live_end]
        self.assertIn("liveInteractiveLesson != null -> DatabaseInteractiveLessonLab(", live)
        self.assertIn("compact = true", live)
        self.assertIn("liveWordIndex", live)


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


class ScreenshotFrameDispatchTests(unittest.TestCase):
    def test_highlight_frame_command_accepts_a_directory_argument(self):
        # An empty directory reaches the PNG checker and fails for the expected
        # reason; it must not be rejected by the XML-file validator.
        with tempfile.TemporaryDirectory() as frames_dir:
            with patch.object(sys, "argv", ["ui_smoke.py", "assert-highlight-frames", frames_dir]):
                with self.assertRaisesRegex(SystemExit, "No live lesson frames were captured"):
                    ui_smoke_main()


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
        for evidence_file in ("live-resumed.xml", "live-complete.xml", "live-lesson.xml", "follow-up-sent.xml", "follow-up.xml"):
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

    def test_spoken_caption_preserves_source_paragraphs(self):
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        caption = tutor[tutor.index("private fun WordByWordCaption("):tutor.index("private fun ChapterOneMathAnimation(")]
        self.assertIn("text.substring(cursor, matchStart)", caption)
        self.assertIn("if (cursor < text.length) append(text.substring(cursor))", caption)
        self.assertNotIn("sentencesInParagraph", caption)
        self.assertNotIn("separate paragraphs only after every third sentence", caption)

    def test_follow_up_chat_scrolls_to_exchange_instead_of_completion_card(self):
        tutor = (Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        self.assertIn('var chapterFollowUpStarted by remember { mutableStateOf(savedSession.optBoolean("chapter_follow_up_started", false)) }', tutor)
        self.assertIn('if (chapterCompleted) chapterFollowUpStarted = true', tutor)
        self.assertIn('val completionCardVisible = chapterCompleted && !chapterFollowUpStarted', tutor)
        self.assertIn('if (chapterCompleted && !chapterFollowUpStarted)', tutor)
        self.assertIn('FilterChip(selected = false, onClick = { sendMessage("Can you explain that more simply?") }', tutor)
        self.assertIn('sendMessage("Can you show me another example?")', tutor)
        self.assertNotIn('Why does this rule work?', tutor)
        self.assertEqual(tutor.count("FilterChip("), 2)
        self.assertIn('label = { Text(if (chapterCompleted) "Follow-up question" else "Message your teacher") }', tutor)
        self.assertIn('contentDescription = if (chapterCompleted) "Send follow-up question" else "Send question"', tutor)
        self.assertIn('.put("chapter_follow_up_started", chapterFollowUpStarted)', tutor)

    def test_completed_lesson_is_kept_for_follow_up_chat(self):
        root = Path(__file__).resolve().parents[2]
        tutor = (root / "app/src/main/java/com/padippupal/app/TutorScreen.kt").read_text()
        self.assertIn('messages.add(TutorMessage("assistant", completedLesson, interactiveLesson = liveInteractiveLesson))', tutor)
        self.assertIn('status = "Live lesson complete."', tutor)
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        self.assertIn("def assert_completed_lesson(path, lesson_snapshot_path=None):", smoke)
        self.assertIn("def assert_followup_answer(path):", smoke)
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("Waiting for playback to finish", script)
        self.assertIn("assert-followup follow-up.xml", script)
        self.assertIn("assert-completed-lesson live-complete.xml ui-screenshots/live-module-4.xml", script)
        self.assertIn("pre-completion lesson snapshot is required", smoke)
        self.assertIn("preceding live-module snapshot", smoke)

    def test_smoke_waits_for_full_caption_and_rejects_checkpoint_ui(self):
        script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn("assert-live live-lesson.xml > live-assertion.log 2>&1", script)
        self.assertIn("cp live-assertion.log live-assertion-last.log", script)
        self.assertIn("Last module assertion:", script)
        self.assertIn("Sampled module assertion history:", script)
        self.assertIn("live-assertion-history.log", script)
        self.assertIn("lesson_poll_count % 10", script)
        self.assertIn("live-complete.xml", script)
        self.assertNotIn("explicit understanding checkpoint", script)
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        live_start = smoke.index("def assert_live(path):")
        live_end = smoke.index(chr(10) + "def exact_color_mask", live_start)
        live_assertion = smoke[live_start:live_end]
        self.assertNotIn("Live lesson is not exposing its active playback segment progress", live_assertion)
        self.assertIn('if "pause" not in joined or "stop" not in joined:', live_assertion)
        self.assertIn('seen_modules', script)
        self.assertIn('live-module-index', script)
        self.assertLess(script.index('module_index=$(python3 .github/scripts/ui_smoke.py live-module-index'), script.index('if python3 .github/scripts/ui_smoke.py assert-live'))
        self.assertIn('Discover/capture the exact active module independently of the broader', script)
        self.assertIn('live-module-${module_index}.png', script)
        self.assertIn('active_module_index(path)', live_assertion)
        self.assertIn('own heading and mapped image', live_assertion)
        self.assertIn('if [ "$seen_modules" = ",1,2,3,4," ]; then', script)
        self.assertIn('lesson_started=1', script)
        self.assertLess(script.index('lesson_started=1'), script.index('if [ "$lesson_started" -ne 1 ]; then'))


    def test_synthesized_visuals_follow_exact_spoken_segment_boundaries(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn('inlineVisual?.optString("scene_type") == "synthesis_static"', tutor)
        self.assertIn('inlineVisual.put("step_word_boundaries", wordBoundaries)', tutor)
        self.assertIn('val stepWordBoundaries = liveInteractiveLesson?.optJSONArray("step_word_boundaries")', tutor)
        self.assertIn('spokenWordPosition <= stepWordBoundaries.optInt(it, Int.MAX_VALUE)', tutor)
        self.assertIn('visualSteps.length() == lessonSegments.size', tutor)


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


class ChapterCompletionFlowTests(unittest.TestCase):
    def test_smoke_audio_duration_and_word_timings_share_one_contract(self):
        fixture = (Path(__file__).resolve().parent / "tutor_smoke_api.py").read_text()
        self.assertIn("SMOKE_AUDIO_DURATION_MS = 20_000", fixture)
        self.assertIn("duration_ms = SMOKE_AUDIO_DURATION_MS", fixture)
        self.assertIn('assert smoke_timings[-1]["end_ms"] == SMOKE_AUDIO_DURATION_MS', fixture)
        self.assertIn('assert all(left["end_ms"] == right["start_ms"] for left, right in zip(smoke_timings, smoke_timings[1:]))', fixture)
        self.assertNotIn('smoke_timings[-1]["end_ms"] == 6000', fixture)

    def test_completed_chapter_offers_prominent_next_chapter_action(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn('completedChapterTitle = chapter', tutor)
        self.assertIn('chapterCompleted = chapter.isNotBlank()', tutor)
        self.assertIn('if (chapterCompleted && !chapterFollowUpStarted)', tutor)
        self.assertIn('val nextChapter = if (completedIndex >= 0) chapterOptions.getOrNull(completedIndex + 1) else null', tutor)
        self.assertIn('Text("Start next chapter  →"', tutor)
        self.assertIn('chapter = nextTitle', tutor)
        self.assertIn('topic = nextTopic', tutor)
        self.assertIn('tutorMainHandler.postDelayed({ startLiveLesson() }, 350L)', tutor)
        self.assertIn('.put("chapter_completed", chapterCompleted)', tutor)
        self.assertIn('.put("completed_chapter", completedChapterTitle)', tutor)
        self.assertIn('LaunchedEffect(messages.size, loading, liveLessonActive, chapterCompleted, chapterOptions, chapterFollowUpStarted)', tutor)
        self.assertIn('(if (completionCardVisible) 1 else 0)', tutor)
        self.assertIn('chatListState.animateScrollToItem(itemCount - 1)', tutor)
        self.assertIn('delay(700L)', tutor)
        self.assertIn('once that asynchronous layout has settled', tutor)
        self.assertNotIn("scrollOffset = 10000", tutor)
        fixture = (Path(__file__).resolve().parent / "tutor_smoke_api.py").read_text()
        self.assertIn('deterministic_silent_smoke_audio', fixture)
        self.assertIn("SMOKE_AUDIO_DURATION_MS = 20_000", fixture)
        self.assertIn("duration_ms = SMOKE_AUDIO_DURATION_MS", fixture)
        self.assertIn('word_timings', fixture)

    def test_live_module_cards_use_refined_active_state_without_redundant_number_pill(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        start = tutor.index("private fun LiveLessonModuleSection(")
        end = tutor.index("private fun DatabaseInteractiveLessonLab(", start)
        section = tutor[start:end]
        self.assertIn('Color(0xFFF8FBFF)', section)
        self.assertIn('RoundedCornerShape(24.dp)', section)
        self.assertIn('"NOW LEARNING"', section)
        self.assertIn('shadowElevation = if (active) 3.dp else 0.dp', section)

    def test_completion_card_has_scroll_room_above_fixed_composer(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn("bottom = if (chapterCompleted && !chapterFollowUpStarted) 360.dp else 10.dp", tutor)
        self.assertIn("chatListState.animateScrollToItem(itemCount - 1)", tutor)

    def test_emulator_fixture_exposes_next_chapter_and_completion_assertion_checks_it(self):
        fixture = (Path(__file__).resolve().parent / "tutor_smoke_api.py").read_text()
        self.assertIn('"title": "Growing Number Patterns"', fixture)
        self.assertIn('"topics": ["Square Numbers"]', fixture)
        smoke = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        start = smoke.index("def assert_completed_lesson(path, lesson_snapshot_path=None):")
        end = smoke.index("\ndef assert_followup_answer", start)
        completed = smoke[start:end]
        self.assertIn('"start next chapter" not in joined', completed)
        self.assertIn('"growing number patterns" not in joined', completed)


if __name__ == "__main__":
    unittest.main()
