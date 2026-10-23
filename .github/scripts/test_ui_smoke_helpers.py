#!/usr/bin/env python3
"""Regression tests for accessibility-tree selectors; no emulator required."""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ui_smoke import assert_live, concept_candidates, exact_color_mask, exact_text_candidates



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


class LiveCheckpointLabelRegressionTests(unittest.TestCase):
    def test_actual_understanding_checkpoint_label_is_a_valid_live_lesson_state(self):
        # Match the wording shown by the real Compose checkpoint, not just older labels.
        xml = """<hierarchy>
          <node text="Patterns in Mathematics" bounds="[0,0][400,60]"/>
          <node text="Pause" bounds="[0,60][100,110]"/>
          <node text="Stop" bounds="[100,60][200,110]"/>
          <node text="The All 1s pattern repeats the number 1" bounds="[0,120][400,180]"/>
          <node text="WATCH THE PATTERN" bounds="[0,180][400,220]"/>
          <node text="1, 1, 1, 1, 1" bounds="[0,220][400,260]"/>
          <node text="Does that make sense so far?" bounds="[0,270][400,320]"/>
          <node text="I understand" bounds="[0,320][200,370]"/>
          <node text="Explain again" bounds="[200,320][400,370]"/>
          <node text="I have a question" bounds="[0,370][400,420]"/>
        </hierarchy>"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", encoding="utf-8") as handle:
            handle.write(xml)
            handle.flush()
            assert_live(handle.name)


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
        self.assertIn("system-image: google_apis", workflow)
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
        self.assertIn("rm -f home.xml tutor.xml", script)
        for evidence_file in ("live-resumed.xml", "live-checkpoint.xml", "live-continued.xml"):
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



class CheckpointLayoutRegressionTests(unittest.TestCase):
    def test_checkpoint_caption_wraps_naturally_without_debug_visual_focus_row(self):
        tutor = (Path(__file__).resolve().parents[2] / "app" / "src" / "main" /
                 "java" / "com" / "padippupal" / "app" / "TutorScreen.kt").read_text()
        self.assertIn("modifier.fillMaxWidth().wrapContentHeight()", tutor)
        self.assertNotIn("heightIn(min = 64.dp, max = 108.dp)", tutor)
        self.assertNotIn("Visual focus ·", tutor)
        # The lesson must be a continuous scrollable transcript, not a compact page.
        live_layout = tutor[tutor.index("// One continuous, scrollable lesson transcript"):tutor.index('if (!liveLessonActive && status.isNotBlank())')]
        self.assertIn(".verticalScroll(liveLessonScrollState)", live_layout)
        self.assertIn("for (pastIndex in 0 until liveSegmentIndex.coerceAtMost(liveSegments.size))", live_layout)
        self.assertIn("WordByWordCaption(liveCaption, speechActive, liveWordIndex", live_layout)
        self.assertIn("verticalArrangement = Arrangement.spacedBy(12.dp)", live_layout)
        # When a checkpoint appears, auto-scroll must reveal all feedback controls.
        self.assertIn("LaunchedEffect(awaitingUnderstanding, liveLessonComplete, liveLessonActive)", tutor)
        self.assertIn("liveLessonScrollState.animateScrollTo(liveLessonScrollState.maxValue)", tutor)
        smoke_script = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        checkpoint_capture = smoke_script.index('> ui-screenshots/live-checkpoint.png')
        self.assertIn("sleep 1", smoke_script[max(0, checkpoint_capture - 120):checkpoint_capture])
        self.assertNotIn("Arrangement.Center", live_layout)
        self.assertNotIn(" / ${liveSegments.size}", tutor)
        self.assertNotIn("Preparing segment ${index + 1} of ${liveSegments.size}", tutor)
        self.assertIn('.put("max_segments", 8)', tutor)
        self.assertIn("Teach this topic fully", tutor)
        # Assert the user-visible label independently of Kotlin argument formatting/order.
        self.assertRegex(live_layout, r'Text\(\s*"I have a question"')
        # Assert the intended control contract separately: full-width, balanced-height outlined action.
        self.assertIn("modifier = Modifier.fillMaxWidth().height(48.dp)", live_layout)
        self.assertIn("border = BorderStroke(1.dp, TutorAccentSoft)", live_layout)
        self.assertNotIn("if (liveVisualAction.isNotBlank()) {\n                        }", tutor)
        # Word highlighting still auto-scrolls during active speech.
        self.assertIn("scrollState.animateScrollTo(target)", tutor)
        self.assertIn("if (active && layout != null && words.isNotEmpty())", tutor)
        # A completed lesson must remain visible as a reviewable transcript.
        self.assertIn("var liveLessonComplete by remember { mutableStateOf(false) }", tutor)
        self.assertIn("if (index >= liveSegments.size) { liveLessonComplete = true", tutor)
        self.assertIn("if (liveLessonComplete) {", live_layout)
        self.assertIn("TOPIC COMPLETE", tutor)
        # Checkpoint feedback controls share a deliberate size and consistent rounded styling.
        self.assertIn("modifier = Modifier.weight(1f).height(52.dp)", live_layout)
        self.assertIn("shape = RoundedCornerShape(16.dp)", live_layout)
        self.assertIn("modifier = Modifier.fillMaxWidth().height(48.dp)", live_layout)
        smoke = (Path(__file__).resolve().parent / "android-ui-smoke.sh").read_text()
        self.assertIn('Now look at the sequence.', smoke)
        self.assertIn('The All 1s pattern repeats the number 1', smoke)
        self.assertNotIn("current_counter=$(grep", smoke)
        helpers = (Path(__file__).resolve().parent / "ui_smoke.py").read_text()
        self.assertIn("Page-style segment progress reappeared", helpers)


if __name__ == "__main__":
    unittest.main()
