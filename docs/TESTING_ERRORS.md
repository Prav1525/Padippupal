# PadippuPal testing error log

This is the durable record of meaningful test failures, incorrect fixes, and test-harness mistakes. Read it **before every test run** alongside `.github/testing-regression-checklist.md`. Add a dated entry whenever a mistake is discovered; do not erase old entries when resolved. Update each entry with the final verification result and exact run/commit references when available.

## How to record an incident

For every entry, capture: **symptom/failure**, **root cause**, **why it escaped**, **corrective action**, **regression protection**, **evidence (commit/run/log)**, and **status**. If the root cause is not yet confirmed, label it as a hypothesis and do not present it as fact.

## Incidents

### TE-001 — Generic later lesson segment was incorrectly accepted
- **Date discovered:** 2026-10-23
- **Area:** Backend lesson-plan validation; Android topic guard; retry behavior.
- **Symptom/failure:** Curriculum Engine Tests run [39880904470](https://github.com/Prav1525/Padippupal/actions/runs/39880904470) failed at `test_tutor.py::test_lesson_plan_retries_when_a_later_segment_is_generic_not_all_ones`. The test expected two model requests (the initial invalid lesson plus one retry) but observed only one.
- **Root cause:** The All 1s topic validator was loosened from validating each spoken segment to accepting a lesson when any segment anywhere looked relevant. A relevant first segment therefore masked a generic unrelated later segment, preventing the required retry. The Android guard was loosened in a similar way, creating a backend/client consistency risk.
- **Why it escaped:** The change was reasoned about at whole-lesson level and the valid supporting-explanation case was not balanced against the existing generic-later-segment retry test before the change was committed. The APK build passing did not exercise this backend contract.
- **Corrective action:** Implemented per-segment validation in backend and Android. Every speech/caption segment must match an explicit All 1s signal, a narrowly defined supporting explanation, or an exact short neutral transition; every segment is still checked for forbidden content. At least one segment must explicitly signal the topic. Supporting patterns allow statements such as “A pattern can repeat without increasing or decreasing.” Visual labels do not count as relevance.
- **Regression protection required:** Preserve and pass the generic-later-segment retry test; preserve `test_all_ones_lesson_allows_supporting_explanation_without_repeated_keyword`; preserve the off-topic-segment rejection and no-topic-relevance tests. Add any additional focused tests needed to prove generic unrelated text is rejected even when another segment is relevant.
- **Evidence:** Failing curriculum run [39880904470](https://github.com/Prav1525/Padippupal/actions/runs/39880904470); APK run [39880904476](https://github.com/Prav1525/Padippupal/actions/runs/39880904476) passed on commit `dcc70153daf0123841ff51007272b70d6537243e`. UI smoke run [39880904502](https://github.com/Prav1525/Padippupal/actions/runs/39880904502) was still in progress at the last recorded check.
- **Status:** **Fix committed; verification pending.** Do not merge PR #13 until backend regression tests, Android build, and end-to-end checks pass.

### TE-002 — UI smoke test assumed a fixed number of lesson segments
- **Date discovered:** 2026-10-23
- **Area:** Android UI smoke harness / checkpoint progression.
- **Symptom/failure:** Smoke validation assumed a lesson always had five segments, which could falsely fail or misread real lesson progression when the actual segment count differed.
- **Root cause:** The test encoded an implementation-specific fixed count rather than reading the actual displayed progress counter and verifying that both the counter and active caption/text changed.
- **Why it escaped:** The harness assertion was not resilient to valid content-driven segment counts.
- **Corrective action:** Update the smoke script to compare observed progress-counter values and active caption/text rather than assume a fixed five-segment lesson; correct counter parsing to recognize the displayed `current / total` format.
- **Regression protection:** Keep unit tests for counter parsing and progression detection in `.github/scripts/test_ui_smoke_helpers.py`; check the actual UI state after selecting a lesson and advancing a checkpoint.
- **Evidence:** Commits `0ad2de5c3c7ec3159adfee888c2adfbbc624b4f1` and `d7e681acb8a37b72d8f8612fd92641ffa019b487` (verify the latest history before relying on these as the final implementation).
- **Status:** Corrective changes were committed; final end-to-end status must be checked against the latest UI smoke workflow before release.

### TE-003 — A visible option was treated as proof that selection succeeded
- **Date discovered:** 2026-10-23
- **Area:** Android Compose UI smoke / accessibility selectors.
- **Symptom/failure:** Android XML may expose a visible Compose row without reliable clickable/enabled attributes; selecting based only on accessibility flags or assuming a tap succeeded can leave the smoke test on the previous screen.
- **Root cause:** The test harness relied on selector metadata rather than observing the resulting application state.
- **Why it escaped:** UI accessibility metadata is not a reliable representation of every Compose interaction.
- **Corrective action:** Select only visible numbered rows with valid non-zero bounds; prefer clickable nodes when available, then verify the tap by observing the next screen/state.
- **Regression protection:** Keep selection-state assertions in `.github/scripts/android-ui-smoke.sh` and related helper tests; capture XML, screenshots, and logs when a transition does not occur.
- **Evidence:** See the UI selector and smoke-flow safeguards described in `.github/testing-regression-checklist.md`; attach the exact workflow run and artifacts when next reproduced or verified.
- **Status:** Safeguard documented/implemented; confirm with a successful current end-to-end run before calling fully verified.


### TE-004 — All 1s lesson rejected by the Android topic guard
- **Date discovered:** 2026-10-23
- **Area:** Live tutor request prompt; Android All 1s fail-closed validation; emulator UI smoke.
- **Symptom/failure:** Android UI smoke run [39882430428](https://github.com/Prav1525/Padippupal/actions/runs/39882430428) built the APK and passed curriculum-engine tests, but failed in the live tutor flow with: “The lesson content did not stay on All 1s. Please try again; no incorrect lesson was started.”
- **Confirmed immediate cause:** The hosted lesson-plan API returned `grounded=true` with non-empty segments, but none of the segment speech/captions passed Android's All 1s topic validator. The UI trace confirms this is a content-contract failure, not an APK build, emulator, or navigation failure.
- **Deeper root-cause finding:** The repository's current backend implementation applies the same per-segment All 1s topic gate to both approved and generated lessons and returns `grounded=false` when the model remains off-topic. The hosted endpoint nevertheless returned a grounded response that violates the client gate. This strongly indicates the hosted API is running an older/different backend contract or serving content not covered by the current server validator. The exact raw segment text was not logged (appropriately, to avoid logging learner content), so deployment drift is the best-supported explanation, not a proven identification of the exact sentence.
- **Why it escaped:** The app prompt/validator had been improved in the PR branch, but the hosted backend is independently deployed and the emulator smoke exercises that live deployment rather than the branch's backend code. The test previously reported only the client-side rejection and did not expose the backend contract mismatch.
- **Corrective action:** Keep Android fail-closed; do not relax the topic guard. Update the backend so that after its corrective model retry fails, it extracts a sentence only from the already topic-filtered textbook passages, applies the same topic validator to that sentence, and returns it with its exact chunk ID as a source-grounded fallback. If no safe source sentence exists, return `grounded=false` and no segments. This avoids starting an off-topic lesson while still allowing a grounded lesson when the model drifts.
- **Regression protection:** Add/update backend coverage for model drift falling back to a valid All 1s textbook sentence and retain the test proving unrelated textbook excerpts are rejected. Require backend tests, APK build, live emulator flow, and screenshot/log review. Before calling this resolved, verify the hosted service has deployed the backend commit and the smoke run exercises that deployment.
- **Evidence:** Failed UI run [39883728326](https://github.com/Prav1525/Padippupal/actions/runs/39883728326), artifact [12471996904](https://github.com/Prav1525/Padippupal/actions/runs/39883728326/artifacts/12471996904); prior fix commits d86174adfe5450bc77bced0e26ff9c37702b30e1 and 02f278b283eb8dcbd4e4092657d2a0bfa7fb838b; backend fallback commit e05a51f7e7a41dbd17472b396c51fc856ed9a4b8 and regression-test commit 7a7a2608d7ad391735426c975477ed1152bb91f0.
- **Status:** **Backend fallback and regression test committed; verification pending.** Do not merge PR #13 until backend tests pass and the hosted API deployment plus current-head emulator smoke test are verified.


### TE-011 — Gemini output token cap contradicted complete-lesson contract
- **Date discovered:** 2026-10-23
- **Area:** Backend tutor generation budget.
- **Symptom:** The prompt requested a complete topic explanation with examples and recap, but Gemini generation was capped at 300 output tokens, risking truncation before the lesson could be complete.
- **Root cause:** The model output budget retained an older short-response configuration after the product requirement changed to a complete chat-first lesson.
- **Why it escaped:** Prompt-text regression coverage checked the instruction but did not check the actual generation budget.
- **Corrective action:** Raised the configured maximum to 700 output tokens and added an assertion that protects the minimum budget.
- **Regression protection:** `test_tutor_uses_profile_and_gentle_prompt` now checks `generationConfig.maxOutputTokens >= 700`; full backend and end-to-end validation remains required.
- **Evidence:** Change committed on `feature/grade-aware-chat-tutor`; CI verification pending.
- **Status:** **Implemented; not yet tested.** Do not mark complete until the backend suite and full tutor journey pass.


### TE-012 — Emulator smoke test treated the unwanted checkpoint and animation as success
- **Date discovered:** 2026-10-23
- **Area:** Android lesson-flow acceptance and UI smoke assertions.
- **Symptom:** The successful UI smoke artifact [12476801555](https://github.com/Prav1525/Padippupal/actions/runs/39894585249) showed the lesson paused at “LET'S CHECK YOUR UNDERSTANDING”, with “Does that make sense so far?”, response buttons, a segment counter, and the “WATCH THE PATTERN” animation. This contradicted the requested continuous explanation, even though the workflow passed.
- **Root cause:** The smoke assertions explicitly required a checkpoint and a visible animation, so the test treated the old behaviour as the expected result instead of detecting the product requirement regression.
- **Why it escaped:** The workflow was green but its acceptance assertions encoded the previous UX; a passing test was mistaken for proof of the requested experience.
- **Corrective action:** The tutor now joins validated source-grounded segments into one continuous spoken caption, disables checkpoint pauses, uses no visual action, and asks the smoke test to reject checkpoint/animation labels and require a long complete caption.
- **Regression protection:** The UI smoke flow now waits for the full caption, checks for checkpoint/animation regressions, and retains pause/resume and moving word-highlight checks. The frame-capture window is shortened so playback controls can be tested while speech is active.
- **Evidence:** Source artifact [12476801555](https://github.com/Prav1525/Padippupal/actions/runs/39894585249); combined fix commits on `feature/grade-aware-chat-tutor` beginning at `ce59974def7f657f8bb58022d88877741b1b744b`. Validation of the updated harness and app is pending.
- **Status:** **Fix implemented; not yet tested.** The prior green run does not satisfy the new acceptance criteria. Do not merge until updated backend, Android, emulator, screenshot, and highlight checks pass.


### TE-013 — Replacing checkpoint assertions removed explicit voice-failure detection
- **Date discovered:** 2026-10-23
- **Area:** Emulator smoke-test diagnostics.
- **Symptom:** The combined PR's script-preflight suite failed in `test_tutor_handles_tts_binding_security_exception_without_crashing` because the smoke shell no longer contained the explicit voice-engine failure strings.
- **Root cause:** While removing the obsolete checkpoint-wait loop, its TTS failure detection was removed with it and was not moved to the new complete-caption wait.
- **Why it escaped:** The script was edited before running the required helper tests; the helper suite correctly caught the lost diagnostic before emulator allocation.
- **Corrective action:** Restored all known TTS startup/playback error patterns to the live-lesson wait's explicit failure check.
- **Regression protection:** Keep `test_tutor_handles_tts_binding_security_exception_without_crashing` and `test_live_smoke_reports_missing_tts_before_pause_stop_control_error`; rerun script preflight before emulator allocation.
- **Evidence:** Combined PR #17 workflow run [39901962065](https://github.com/Prav1525/Padippupal/actions/runs/39901962065), job `emulator-smoke`, preflight failed before emulator startup. Corrective commit pending workflow rerun.
- **Status:** **Corrective change implemented; verification pending.**


### TE-014 — Complete-lesson smoke fixture self-test used stale wording
- **Date discovered:** 2026-10-23
- **Area:** Deterministic emulator API fixture.
- **Symptom:** The smoke preflight passed all 16 UI helper tests but failed `tutor_smoke_api.py --self-test` because the updated example said “repeat the same number” while the existing fixture assertion specifically required “repeats”.
- **Root cause:** Fixture wording changed without updating its semantic self-test expectation.
- **Why it escaped:** The helper suite did not run the fixture's own `--self-test`; the workflow runs that as a separate required preflight step and caught it before emulator allocation.
- **Corrective action:** Adjusted the fixture wording to state “the rule repeats the same number each time,” preserving the same teaching meaning and the existing check.
- **Regression protection:** Keep `python3 .github/scripts/tutor_smoke_api.py --self-test` in the pre-emulator validation sequence.
- **Evidence:** Combined PR #17 UI smoke run [39902140454](https://github.com/Prav1525/Padippupal/actions/runs/39902140454), `Validate smoke-test scripts` failed before emulator startup; correction commit recorded in branch history.
- **Status:** **Corrective change implemented; verification pending.**


### TE-015 — Lesson smoke wait claimed a 150-second limit without enforcing one
- **Date discovered:** 2026-10-23
- **Area:** Emulator smoke harness / ADB timeout guarantees.
- **Symptom:** Code review found the lesson wait loop could spend up to 20 seconds in each of 50 attempts, and its `adb pull` had no timeout, despite logging “up to 150s”. This could leave a failed UI journey running much longer than its stated deadline.
- **Root cause:** The loop bounded individual UI dumps but did not enforce a wall-clock deadline and left a related pull unbounded.
- **Why it escaped:** The stated timeout was trusted without calculating the worst-case time across all attempts and commands.
- **Corrective action:** Added a hard `SECONDS` deadline, shorter per-command timeouts, and moved frame capture until after the complete caption is detected so captured frames cover actual speech.
- **Regression protection:** Keep the bounded-wait rule in this checklist and test the complete-caption wait before emulator allocation.
- **Evidence:** Combined PR #17 UI smoke run [39902333735](https://github.com/Prav1525/Padippupal/actions/runs/39902333735) was still running the emulator step at last inspection; the fix is in the next combined commit.
- **Status:** **Corrective change implemented; verification pending.**


### TE-016 — Smoke fixture self-test still expected three segments after expanding the lesson
- **Date discovered:** 2026-10-23
- **Area:** Deterministic lesson fixture self-test.
- **Symptom:** The updated script preflight passed all 17 UI helper tests but failed `tutor_smoke_api.py --self-test` because the fixture now contains four segments while a separate assertion still required exactly three.
- **Root cause:** The fixture was expanded to provide a complete, sufficiently long spoken lesson, but its segment-count assertion was not updated with the fixture.
- **Why it escaped:** The self-test checks the segment count separately from its content and word-count assertions; the helper suite does not execute this self-test itself.
- **Corrective action:** Updated the self-test to require four fixture segments, matching the actual complete lesson.
- **Regression protection:** Keep the fixture self-test in the pre-emulator workflow and retain its minimum lesson word-count assertion.
- **Evidence:** Combined PR #17 UI smoke run [39902997631](https://github.com/Prav1525/Padippupal/actions/runs/39902997631), preflight failed before emulator allocation.
- **Status:** **Corrective change implemented; verification pending.**


### TE-017 — Removing the in-tutor Change button exposed a missing pre-tutor selection route
- **Date discovered:** 2026-10-23
- **Area:** Main navigation, lesson selection, and emulator smoke flow.
- **Symptom:** The tutor screen no longer exposed the Change button, but the smoke journey still attempted to tap it. More importantly, the app did not yet provide a dedicated pre-tutor screen for subject/chapter/topic/language selection, so simply removing the button would strand first-time learners without a selection path.
- **Root cause:** Selection controls were embedded in the tutor screen, and the navigation flow had not been refactored when the product requirement moved selection to the previous screen.
- **Why it escaped:** The UX requirement and the existing smoke journey disagreed about where selection occurs; the test was still coupled to the old in-tutor Change action.
- **Corrective action:** Added a dedicated `LESSON_SETUP` route that reuses the existing selection panel, routes Home's Begin lesson card to that screen, and navigates to the clean Tutor screen after Done. Updated the smoke journey to validate selection before tutor entry.
- **Regression protection:** Keep the `PreviousScreenSelectionTests` assertions and the emulator sequence `settings.xml -> ready-to-teach.xml -> Teach`; reject a Change control on the tutor screen.
- **Evidence:** Combined PR #17 emulator run [39903215063](https://github.com/Prav1525/Padippupal/actions/runs/39903215063) was exercising the previous navigation at last inspection; this change replaces that path.
- **Status:** **Navigation fix implemented; verification pending.**


### TE-018 — Retry-isolation test still expected the removed tutor.xml artifact
- **Date discovered:** 2026-10-23
- **Area:** Emulator smoke retry isolation and artifact list.
- **Symptom:** The script-preflight suite failed in `test_each_retry_clears_old_xml_and_screenshot_evidence` because it still expected the old `tutor.xml` file after the journey moved lesson selection to `settings.xml` and the ready tutor state to `ready-to-teach.xml`.
- **Root cause:** The smoke flow and cleanup script were updated, but the test expectation, retry evidence list, and workflow artifact list were not all updated together.
- **Why it escaped:** These related path lists are maintained in separate files and the helper test asserted the old literal filename.
- **Corrective action:** Updated the retry-isolation expectation and removed the obsolete `tutor.xml` artifact reference; refreshed the lesson-selection assertion message.
- **Regression protection:** Keep the retry-isolation test and the previous-screen selection test; run script preflight before emulator allocation.
- **Evidence:** Combined PR #17 UI smoke run [39904323005](https://github.com/Prav1525/Padippupal/actions/runs/39904323005), `Validate smoke-test scripts` failed before emulator allocation.
- **Status:** **Corrective change implemented; verification pending.**

## Update protocol

- Add a new numbered incident instead of overwriting history.
- If one incident has multiple separate root causes, split them into separate entries.
- Link exact GitHub Actions runs and record the tested commit SHA.
- After a fix, update the incident's corrective-action and status fields, but preserve the original failure description.
- Before running tests, turn relevant open incidents into a short preflight checklist and ensure each has a regression test or explicit safeguard.
- Never call a test suite green based on an older SHA, a build-only run, or a run that did not exercise the failing path.


### TE-005 — Emulator smoke test exercised a stale production backend instead of the PR backend
- **Date discovered:** 2026-10-23
- **Area:** Android/backend integration, Render deployment configuration, UI smoke workflow.
- **Symptom/failure:** UI smoke run [39886914058](https://github.com/Prav1525/Padippupal/actions/runs/39886914058) built and launched the app, selected CBSE Class 6 Mathematics → Patterns in Mathematics → All 1s, then failed with “The lesson content did not stay on All 1s. Please try again; no incorrect lesson was started.”
- **Confirmed root cause:** The UI smoke workflow calls the production URL `https://padippupal-curriculum-api.onrender.com`. Render service `srv-dbauc7brjlhs73anp7v0` is configured to deploy branch `main`, and PR previews are disabled. Its live deployment `dep-dbcg8vjrjlhs73bc3gvg` runs commit `22270b5333a5c692b0a1d6206eb86f4fc4ed4e48`. Inspecting `backend/app.py` at that exact deployed commit confirms it lacks the PR's `_lesson_segments_match_topic` gate and topic-filtered textbook fallback, both present at PR head `f30806fbe42a85a108234a58aacbe415a6c53ebe`. Therefore the UI test does not exercise the backend fixes in PR #13.
- **Still unknown:** The failing artifact does not contain the raw rejected segment text, so we cannot conclusively determine whether the model's exact sentence was off-topic or whether Android's validator rejected a valid natural-language explanation. Do not loosen the Android guard without a reproducible test case.
- **Why it escaped:** Android APK build and backend unit tests run independently; the UI smoke workflow only checked that the production API health endpoint answered, not which backend revision served the lesson request.
- **Corrective action:** Keep the Android topic guard fail-closed. Before accepting the tutor PR, run end-to-end smoke against a backend built from the same tested commit, or a dedicated PR/staging deployment explicitly pinned to that commit. Do not point production at an unreviewed branch or change production deployment settings without explicit authorization. Add a backend revision/build identifier to health diagnostics and assert that the UI smoke target matches the expected revision.
- **Regression protection:** Verify API revision before emulator interaction; preserve the raw validation reason and a privacy-safe, bounded diagnostic for rejected segments (never log learner-identifying data); add natural-language positive and unrelated-sequence negative validator cases; require a successful live-lesson screenshot and actual progression before marking UI smoke green.
- **Evidence:** UI run [39886914058](https://github.com/Prav1525/Padippupal/actions/runs/39886914058), APK build run [39886914053](https://github.com/Prav1525/Padippupal/actions/runs/39886914053), artifact [12473380655](https://github.com/Prav1525/Padippupal/actions/runs/39886914053/artifacts/12473380655), Render deployment `dep-dbcg8vjrjlhs73bc3gvg`, deployed commit `22270b5333a5c692b0a1d6206eb86f4fc4ed4e48`, PR head `f30806fbe42a85a108234a58aacbe415a6c53ebe`.
- **Status:** **Root cause of test-environment mismatch confirmed; production/runtime remediation blocked pending authorization for a staging or production deployment.** APK build passed, but the live tutor journey remains unverified and PR #13 must not be merged yet.

### TE-006 — UI smoke used mutable production services instead of deterministic test dependencies
- **Date discovered:** 2026-10-23
- **Area:** Emulator end-to-end test isolation and API contract.
- **Symptom/failure:** Repeated UI smoke runs reach the live tutor, then reject the All 1s lesson. The workflow calls the production Render service, which runs `main`, not the PR's backend revision.
- **Root cause:** Confirmed test-environment defect: the test combines a PR APK with a mutable, separately deployed production backend. A passing health check only proves the host responds; it does not prove the tested backend contract matches the app/PR.
- **Why it escaped:** The workflow had no revision assertion and did not isolate API responses. Backend unit tests and Android build checks therefore passed independently while the end-to-end path remained non-reproducible.
- **Corrective action:** Replace the smoke workflow's production API dependency with a deterministic local HTTP fixture reachable from the emulator. Keep the production URL as the normal app default; permit the fixture URL only in debug builds and enable cleartext traffic only in the debug manifest.
- **Regression protection:** Assert the fixture health endpoint before emulator launch; serve an explicitly topic-valid All 1s lesson with stable chapter/topic data; include a negative test ensuring unrelated All 1s segments remain rejected by the Android guard; never use production data as the smoke-test oracle.
- **Evidence:** Reproduced on UI smoke run [39888602289](https://github.com/Prav1525/Padippupal/actions/runs/39888602289), PR head `ce0d3127f58b8213a9fc8338c278fd3664adccfd`. Implementation and verification status will be updated after the affected workflow runs.
- **Status:** **Fix in progress; not verified.** Keep PR #13 unmerged until the new deterministic emulator path and required regression checks pass.

### TE-007 — Duplicated caption text could invalidate a short neutral transition
- **Date discovered:** 2026-10-23
- **Area:** Android All 1s topic validator.
- **Symptom/failure:** During code review of the deterministic smoke fixture, the accepted transition phrase `Now look at the sequence.` would be concatenated with an identical caption and fail the anchored neutral-transition regex.
- **Root cause:** The guard combined spoken text and caption text unconditionally, even when the caption duplicated the spoken text exactly. This duplicated a valid short transition and made it appear to contain extra words.
- **Why it escaped:** Existing tests did not cover a valid neutral transition with identical speech and caption.
- **Corrective action:** Avoid concatenating a caption when it is blank or identical to the spoken text; still inspect both fields when they differ.
- **Regression protection:** Added a unit test for duplicated speech/caption transition text while retaining the negative generic-later-segment and forbidden-content cases.
- **Evidence:** Validator/test commits `a90fbbf6959b04360b107f9298cc0f3e2b7787af` and `abd8d17eb3662152ca502e4568aae5551ecc5b56`; final CI run evidence pending.
- **Status:** **Implemented; verification pending.**


### TE-008 — Supporting language was incorrectly counted as an explicit topic signal
- **Date discovered:** 2026-10-23
- **Area:** Android All 1s topic validator and pre-emulator JVM gate.
- **Symptom/failure:** UI smoke run [39891634599](https://github.com/Prav1525/Padippupal/actions/runs/39891634599) failed in `AllOnesTopicValidatorTest.rejectsAnOtherwiseSupportingSequenceWithoutAnExplicitTopicSignal` before allocating/starting the emulator. The assertion expected a supporting-only lesson to be rejected for lacking an explicit topic signal.
- **Root cause:** The Android `relevant` regex included broad explanatory phrases such as `stays the same` and `same number`. In particular, “A pattern can stay the same without increasing” matched both the supporting-expression rule and the explicit-topic rule, so the validator incorrectly treated a generic supporting explanation as proof that the lesson was specifically about All 1s.
- **Why it escaped:** The test checked the expected failure reason, but the topic-signal regex was not reviewed independently from the supporting-language regex. The APK compilation could pass despite this semantic validation bug.
- **Corrective action:** Removed generic sameness phrases from the explicit-topic regex; they remain eligible as supporting explanations but cannot establish topic identity on their own.
- **Regression protection:** Strengthened the test to cover both “stay the same without increasing” and “repeat without increasing or decreasing” as supporting-only text that must not satisfy the explicit-topic requirement. Preserve the valid All 1s positive case and generic/off-topic rejection cases.
- **Evidence:** Failing run [39891634599](https://github.com/Prav1525/Padippupal/actions/runs/39891634599), initial fix commit `49dac4ca02e6e0b6486fef609470458fc6992802`, regression test commit `928aad86a79f224f97a251d7d2ec63dd90002e37`. Verification on the latest PR head is pending.
- **Status:** **Root cause confirmed; code and regression test committed; verification pending.** Keep PR #13 unmerged until the JVM tests and full emulator flow pass on the latest commit.


### TE-009 — UI smoke preflight assertions drifted from the deterministic test design
- **Date discovered:** 2026-10-23
- **Area:** Android UI smoke helper regression tests and topic-guard contract.
- **Symptom/failure:** UI smoke run [39894074738](https://github.com/Prav1525/Padippupal/actions/runs/39894074738) failed during `Validate smoke-test scripts`, before emulator allocation. Two helper tests failed.
- **Confirmed root cause:** (1) `BackendWarmupRegressionTests` still required a Render production warm-up step even though the workflow had intentionally switched to the deterministic local fixture at `127.0.0.1:8765` / emulator host `10.0.2.2:8765`. The test was asserting obsolete architecture, not the current safety contract. (2) `ExactSelectorTests` looked for the validator's failure reason inside `TutorScreen.kt`, but the reason is owned by `AllOnesTopicValidator.kt`; the test was checking the wrong source file.
- **Why it escaped:** The workflow implementation and helper tests were changed at different times, and the helper test did not assert the actual fixture contract. The source-string assertion also failed to follow the code's ownership boundary.
- **Corrective action:** Update the workflow regression test to require the local fixture health check, emulator-reachable base URL, readiness gate, and absence of the production Render URL. Update the topic-validator contract test to read `AllOnesTopicValidator.kt` for the validator's rejection reason.
- **Regression protection:** Keep both checks in `.github/scripts/test_ui_smoke_helpers.py`; run `python3 .github/scripts/test_ui_smoke_helpers.py` and the full UI workflow preflight before emulator allocation.
- **Evidence:** Failed run [39894074738](https://github.com/Prav1525/Padippupal/actions/runs/39894074738); correction commit `bb738972d939c68b5bc8f5392cb2e875835fa2ef`. Verification on this correction commit is pending.
- **Status:** **Root cause confirmed and test corrections committed; full verification pending.** Do not merge PR #13 until helper tests, APK build, emulator journey, and screenshot review pass on the same latest commit.


### TE-010 — Tutor prompt and UI contradicted the requested complete chat-first lesson
- **Date discovered:** 2026-10-23
- **Area:** Backend lesson-generation instructions and Android tutor rendering.
- **Symptom:** The prompt forced a short, single-step reply and check question, while the app rendered generated visual lessons/animation labs and displayed feedback after each latest assistant reply. This encouraged chopped-up teaching and unrelated visuals.
- **Root cause:** Older conversational-learning and visual-first requirements remained higher priority than the desired complete-topic, chat-like lesson experience; visual widgets and feedback were attached to individual assistant messages rather than the end of a complete lesson.
- **Corrective action:** Add an explicit overriding chat-first prompt contract: complete age-aware topic explanation, simple worked examples/text diagrams, question only after teaching, and no animation in the current mode. Disable current Android animation/lab composables and remove per-reply feedback prompts for now.
- **Regression protection:** Add a backend prompt-contract test. Before every test run, read this document and .github/testing-regression-checklist.md; verify selected-topic explanation, follow-up answers, no visual overlays, and no per-reply feedback in emulator screenshots.
- **Evidence:** Branch feature/grade-aware-chat-tutor; implementation is awaiting test execution and emulator/screenshot verification.
- **Status:** **Changes drafted; not verified.** Do not merge PR #13 or this follow-up until backend tests, Android build, emulator chat journey, and screenshot review pass.


### TE-012 — Continuous lesson caption looked fragmented because every sentence became a paragraph
- **Date discovered:** 2026-10-23
- **Area:** Android word-by-word caption formatting / visual acceptance.
- **Symptom:** Screenshot review of the combined UI smoke run [39904633845](https://github.com/Prav1525/Padippupal/actions/runs/39904633845) showed excessive blank space between every spoken sentence. Although the caption was one continuous lesson, the presentation looked like a series of disconnected blocks and pushed later text below the viewport.
- **Root cause:** `WordByWordCaption` inserted a blank paragraph after every sentence-ending word rather than grouping sentences into natural teaching paragraphs.
- **Why it escaped:** The UI smoke checked that the lesson was continuous, unclipped in the viewport, and free of separate cards, but did not check sentence grouping or paragraph density.
- **Corrective action:** Group three sentences per paragraph and keep the word-offset calculation aligned with the inserted separators so inline highlighting continues to point at the correct spoken word.
- **Regression protection:** Add a source-level helper regression test for paragraph grouping and retain screenshot-based moving-highlight/layout checks.
- **Evidence:** Screenshot artifact from run [39904633845](https://github.com/Prav1525/Padippupal/actions/runs/39904633845); correction commits `9953bff2abd2c38cb4af61935be8640fd2113fe9` and `dee6541daa24aac1907edbbc343404efca0f40c0`. Verification on the latest combined head is pending.
- **Status:** **Implemented; not yet verified.** Keep PR #17 open until helper tests, Android build, emulator flow, screenshot review, and follow-up chat behavior pass on the same head.
