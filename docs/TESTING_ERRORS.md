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


### TE-018 — Live lesson status stayed on a generic startup message during hosted voice preparation

- **Date discovered:** 2026-10-23
- **Area:** Android live tutor playback status / hosted TTS lifecycle.
- **Symptom:** When a lesson segment was handed to hosted natural voice, the UI could keep showing “Your lesson is starting…” while the app waited for the speech service response. That status did not distinguish voice preparation from playback.
- **Root cause:** `playLiveSegment` set a generic startup status immediately before `speak`, and the hosted-TTS path did not set its own preparation status before starting the network request. The device-TTS fallback already had preparation/failure states; the hosted path was missing the matching state.
- **Why it escaped:** The emulator fixture focuses on successful playback, highlighting, pause/resume, and checkpoint progression. It did not assert the transient status during a delayed hosted voice request.
- **Corrective action:** Set “Preparing natural voice…” immediately before the hosted speech request. Existing callbacks then transition the status to speaking after audio starts, or to the explicit fallback/error status if hosted voice fails.
- **Regression protection:** Added `VoicePreparationStatusRegressionTests.test_hosted_voice_request_sets_preparation_status_before_network_work` to assert the preparation state is set before the hosted request and that speaking/fallback states remain present.
- **Evidence:** Initial implementation commit `e48081dd784d30fbbb12833049fddef4096e31dd`; helper regression commit `aac937ef8daa9697807701853f2240f6b84ca6c1`. Latest-head tests and screenshot verification are pending.
- **Status:** **Fix and regression assertion committed; verification pending.** Phase 1 remains open until the complete layout acceptance criteria pass.



### TE-019 — New voice-status regression assertion matched the wrong source-code shape

- **Date discovered:** 2026-10-23
- **Area:** UI helper regression tests.
- **Symptom/failure:** Android UI workflow run [39980790041](https://github.com/Prav1525/Padippupal/actions/runs/39980790041) failed during script validation before allocating the emulator. Sixteen helper tests passed; the new voice preparation test failed on its fallback-status assertion.
- **Root cause:** The production fallback text is inside an `if/else` expression assigned to `status`, rather than a standalone `status = "…"` statement. The test asserted a source-code formatting shape instead of the actual fallback string.
- **Why it escaped:** The new regression test had not run locally before the workflow was launched.
- **Corrective action:** Assert the fallback text itself, independent of whether it is assigned directly or within an expression. No production behavior or valid existing assertion was weakened.
- **Regression protection:** Re-run the complete helper test file and all workflow checks on the corrected latest commit before attempting emulator execution again.
- **Evidence:** Failing run [39980790041](https://github.com/Prav1525/Padippupal/actions/runs/39980790041), tested commit `870836844db253fcc33c51b176b4a716169a9c3a`; assertion correction commit `747c0573d6da9010749a336b8600f83f574a31d5`.
- **Status:** **Test-harness defect corrected; verification pending.**


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


### TE-010 — Understanding checkpoint reserved the whole viewport and created excessive blank space
- **Date discovered:** 2026-10-23
- **Area:** Android Compose live tutor layout / screenshot acceptance.
- **Symptom/failure:** The successful emulator screenshot for the understanding checkpoint showed the spoken explanation and inline All 1s animation at the top, followed by a very large unexplained blank region before the checkpoint question and response controls. The interaction passed, but the visual acceptance requirement did not.
- **Root cause:** The inner teaching-content `Column` always used `Modifier.weight(1f)`, even when `awaitingUnderstanding` was true and the caption already had a bounded height. The checkpoint layout therefore reserved the remaining viewport instead of sizing to the actual teaching content.
- **Why it escaped:** Previous smoke assertions verified lesson opening, caption/progression and checkpoint actions, but did not assert or review the vertical distribution of the final checkpoint screenshot as a release gate.
- **Corrective action:** On understanding checkpoints, remove the inner content column's flexible weight so the caption and compact concept animation occupy only the height they need; retain the flexible weight during normal speech so the lesson still uses available screen space.
- **Regression protection:** Re-run the full Android UI smoke flow and inspect `live-lesson.png` and `live-checkpoint.png` from the exact tested head SHA. Confirm no large unexplained blank gap, clipping, overlap, or hidden controls; confirm the animation remains inline and the understand/explain-again/question actions still work.
- **Evidence:** Screenshot artifact from UI smoke run [39894585249](https://github.com/Prav1525/Padippupal/actions/runs/39894585249), tested before this fix on `fa1760f9569658f1ec44040974cdac33ecf5f653`; fix commit `e83e9a4e62892561826fc2de2e5976ba1547bccc`.
- **Status:** **Fix committed; verification pending.** Do not merge PR #13 until all required checks pass and the new checkpoint screenshots are reviewed.


#### TE-010 follow-up — first fix was incomplete
- **Observed on:** Emulator smoke run [39940987650](https://github.com/Prav1525/Padippupal/actions/runs/39940987650), commit `c6c29826be12a0a3310b6a084a99e78d5046bd51`.
- **Result:** Screenshot review still showed the blank gap. The first fix removed weight from the inner teaching-content column, but the *outer* live-lesson column still had `Modifier.weight(1f)`, so it continued to occupy all remaining height and push the checkpoint controls down.
- **Correction:** On checkpoint state, remove the flexible weight from the outer live-lesson column too; preserve it during normal teaching. Commit `9944dedd2aabb7c95157b096cde6c808eb3dbf52`.
- **Regression rule:** Treat the screenshot review—not just a passing smoke test—as mandatory. Review fresh `live-checkpoint.png` and `live-lesson.png` from the exact same tested SHA. Do not close TE-010 until the gap is gone and controls/animation are visible without clipping or overlap.
- **Status:** Second, parent-level correction committed; verification pending.


### TE-011 — Checkpoint caption viewport inflated spacing despite parent-weight correction
- **Date discovered:** 2026-10-23
- **Area:** Android Compose caption measurement / checkpoint visual acceptance.
- **Symptom/failure:** Emulator screenshot artifact from UI smoke run [39944090457](https://github.com/Prav1525/Padippupal/actions/runs/39944090457) still showed a large gap after a one-line spoken explanation and another large unused region below the checkpoint controls, despite the parent-column weight correction.
- **Root-cause analysis:** The checkpoint caption was constrained with `heightIn(min = 64.dp, max = 108.dp)`; the shared caption component also applied a vertically scrollable viewport capped at 150.dp when not expanding. The screenshot showed the one-line caption occupying a much taller region than its rendered text required. The separate “Visual focus · …” debug-style metadata added another non-teaching row between the explanation and animation. The screenshot demonstrates the spacing symptom; the exact Compose measurement contribution of each modifier must be confirmed by the next screenshot.
- **Why it escaped:** The smoke test asserted interaction/progression and visible controls, not content-to-content spacing. The previous fix removed flexible weights but did not remove the checkpoint caption's bounded scroll viewport or the metadata row.
- **Corrective action:** Remove the checkpoint's forced minimum/maximum caption height; allow checkpoint text to wrap naturally rather than creating a scroll viewport. Remove the technical “Visual focus” line so the explanation flows directly into the inline animation.
- **Regression protection:** Before rerunning, re-read this log and `.github/testing-regression-checklist.md`. Inspect both screenshots from the same latest SHA; confirm the one-line caption uses natural height, the animation follows closely, all checkpoint controls remain visible, and no content is clipped or overlapped. Confirm active-speech word auto-scroll remains unchanged.
- **Evidence:** Screenshot artifact from run [39944090457](https://github.com/Prav1525/Padippupal/actions/runs/39944090457); code changes commits `1ecedcd9dffdb2832920a9c0be747466a42b7260` and `2736e84d400ea6dcc9eec5301558673e39a8cc64`; source-contract regression test commit `d2ec3fcd8ec51168d90093f40c92ffb825759744`. Verification on the final head is pending.
- **Status:** **Code correction committed; visual verification pending.** Do not merge PR #13 until the latest screenshot demonstrates the gap is resolved and all regression gates pass.


### TE-012 — Centered checkpoint group recreated large blank bands

- **Date discovered:** 2026-10-23
- **Area:** Android Compose live tutor layout / screenshot acceptance / regression assertions.
- **Symptom/failure:** Fresh emulator screenshot from UI smoke run [39954229853](https://github.com/Prav1525/Padippupal/actions/runs/39954229853), commit `cc4f46a7c473c4702de78ced2d67cbd3609a9ba3`, showed the checkpoint content vertically centered in the available body: a large blank band between the fixed header and the teaching label, and another large blank band below the question control.
- **Confirmed root cause:** The outer weighted live-lesson `Column` explicitly used `Arrangement.Center` while `awaitingUnderstanding` was true. Because the compact checkpoint content is much shorter than the available viewport, Compose centered that short group, creating exactly the two blank bands visible in the screenshot. The prior correction grouped controls with the animation but retained vertical centering; the test incorrectly asserted that centering was desired.
- **Why it escaped:** The source-contract test positively required `Arrangement.Center`, encoding the mistaken layout decision as expected behavior. The smoke test passed because it checked interaction and visibility, while screenshot review had not yet been converted into a testable layout contract.
- **Corrective action:** Keep the outer teaching canvas weighted to fill available space, but use `Arrangement.spacedBy(8.dp)` in both speaking and checkpoint states so the short content stays top-aligned and flows directly below the header.
- **Regression protection:** Change the helper contract to require top-aligned `Arrangement.spacedBy(8.dp)`, reject `Arrangement.Center` in the live teaching section, and retain checks for natural caption height, inline animation/checkpoint controls, and active-speech auto-scroll. Rerun the complete UI flow and inspect both `live-lesson.png` and `live-checkpoint.png` from the exact new head SHA.
- **Evidence:** UI screenshot artifact [12502270996](https://github.com/Prav1525/Padippupal/actions/runs/39954229853/artifacts/12502270996); offending commit `cc4f46a7c473c4702de78ced2d67cbd3609a9ba3`. Corrective commit and verification pending.
- **Status:** **Root cause confirmed; correction and regression assertion prepared; not yet verified.** Keep PR #13 open until the latest screenshot and all release gates pass.

### TE-013 — Topic lesson replaced its previous explanation and displayed page-style progress

- **Date discovered:** 2026-10-23
- **Area:** Android tutor lesson progression / lesson completeness / continuous scrolling.
- **Symptom:** During live teaching, the spoken caption was replaced for every module and the UI displayed an n / total counter. This made one topic feel like a sequence of pages and left earlier explanations unavailable in the current lesson flow. The lesson request was also capped at five segments, which could truncate a topic before it was fully taught.
- **Root cause:** liveCaption was the only rendered teaching text; playLiveSegment replaced it on every module. The live UI displayed the current segment index as page progress, and the Android request explicitly asked for only five segments.
- **Why it escaped:** Previous acceptance checks concentrated on synchronized highlighting, checkpoint actions, and spacing. They did not assert that completed modules remain visible in one scrollable transcript or reject page-style progress counters.
- **Corrective action:** Render all earlier spoken modules followed by the active highlighted module in one vertically scrollable lesson flow; auto-scroll to newly appended modules; remove the page counter and segment-number status text; request the backend-supported maximum of eight modules and explicitly instruct the planner to cover the selected topic from start to recap. The inline concept animation and checkpoint actions remain in the same flow.
- **Regression protection:** The helper contract asserts a scrollable transcript, retained earlier modules, active word highlighting, absence of page counters, the eight-module request, and the complete-topic prompt. Before release, inspect fresh lesson/checkpoint screenshots and verify the entire topic can be followed by scrolling without a page transition.
- **Affected commits:** UI 4c4ec21111c7d9ac1f8093c59287c13a94fbca0c; helper regression 17428f8401fd7539c58976fcd4531be6f7e3ab5a.
- **Status:** **Implemented; verification pending.** Run the required pre-test checklist and inspect latest-head emulator evidence before calling this verified.

- **Test harness safeguard added during review:** The new regression class was initially placed after the script's `unittest.main()` call, which can cause direct script execution to start discovery before that class is defined. Moved the runner to the end of the file so the continuous-transcript assertions are included in the actual run. Helper correction commit: 9436309582fdba72dc39d8afe2672530cf043d6f.

### TE-014 — Continuous-lesson regression test still required the removed page counter

- **Date discovered:** 2026-10-23
- **Area:** Android emulator continuation smoke test, topic completion, checkpoint feedback UI.
- **Symptom:** The latest APK built and the emulator reached the checkpoint, but the smoke test failed immediately after tapping “I understand.” The log showed the tap occurred; the continuation loop then timed out.
- **Root cause:** The shell smoke test still required a numeric segment counter to change, and ui_smoke.py still asserted that the lesson had advanced beyond a numbered page. Those expectations directly contradicted the approved continuous-screen design, so a valid continuation could never satisfy the old gate. Separately, playLiveSegment marked the live lesson inactive after the final module, hiding the transcript and making the topic feel like it had exited the lesson screen.
- **Why it escaped:** The UI tests were not updated end-to-end when page-style progress was removed. They checked for visible checkpoint controls but retained the obsolete progress-counter assertion. Completion behavior was not tested as part of the continuous transcript contract.
- **Corrective action:** Changed continuation checks to require the fixture's next sentence (“Now look at the sequence.”) and retention of the earlier explanation, with no counter. A completed topic now stays in the same scrollable lesson screen, shows “TOPIC COMPLETE,” and keeps prior teaching available for review. Refined checkpoint feedback into consistently rounded controls with aligned heights and a full-width question action.
- **Regression protection:** Helper tests now assert that completion preserves the lesson screen, feedback buttons share the expected rounded sizing, and continuation is verified by actual lesson content rather than page counters. Required pre-test checklist and this error log were read before starting the next test run.
- **Additional safeguards:** Lesson-start detection and the live-state assertion now recognize the actual teaching/checkpoint/completion labels rather than requiring page progress. Pause is hidden after completion so the finished lesson cannot misleadingly replay the final module; Stop remains available.
- **Affected commits:** UI 70d724e83e2d76eeb4538601701848f44d3b8e36; continuation shell f179b38b03f75804a3310d86e55e590da01dd843 and 2808349b0703a74efc7884dfe69bb669324a80a4; continuation assertion 601022b0577a31c317c075df3631a4837d495716 and 044af93063d246bc6a9f56324175556d0ba860a1; regression tests cc00584eb63f4b1fa051087879bd3f4c507ac155; completion label 2ffdb2934c14ee68d0143828cf3a6a456270786c; final header behavior 7abf186da0233e475f9fdb93bcc26793872953d2.
- **Status:** **Fixes committed; latest-head build, tests, and screenshot verification pending.**

### TE-015 — Feedback-button test coupled the label to Kotlin argument formatting

- **Date discovered:** 2026-10-23
- **Area:** Android tutor checkpoint UI helper regression tests / CI pre-emulator gate.
- **Symptom:** UI smoke run [39965295414](https://github.com/Prav1525/Padippupal/actions/runs/39965295414) built the APK successfully, then failed in `test_checkpoint_caption_wraps_naturally_without_debug_visual_focus_row` before emulator startup. The assertion expected the exact source string `Text("I have a question", color = TutorGreen)`, while the refined button legitimately supplied additional styling arguments.
- **Confirmed root cause:** The test used whole-expression string equality to verify a user-visible label. A visual styling change changed argument structure without changing the label or intended control behavior. This is the same class of brittle test-harness defect as the earlier stale page-counter assumptions: the assertion encoded implementation details rather than the contract.
- **Why it escaped:** The helper suite checked UI source by exact snippets and did not separate semantic label checks from layout/style checks. The helper suite itself was not rerun against the final UI styling change before the emulator workflow was started.
- **Corrective action:** Replace the exact expression assertion with a whitespace-tolerant label assertion; separately assert the actual control contract (full-width 48dp action and outlined border). This keeps the test strict about user-visible layout while allowing harmless Kotlin argument additions/order changes.
- **Prevention against recurrence:** For UI source-contract tests, assert labels, modifiers, accessibility semantics, and behavior independently. Avoid exact full-call strings when style arguments can evolve. Before every workflow run, execute `python3 .github/scripts/test_ui_smoke_helpers.py` after reviewing this log/checklist; require that test to pass before emulator allocation. Add a focused regression test whenever a test-harness assertion fails due to a source-formatting-only change.
- **Evidence:** Failed run [39965295414](https://github.com/Prav1525/Padippupal/actions/runs/39965295414), commit `5c08868d80b8ddac2bf39e2ff2d6d704e4124a72`; corrective test commit `373ee801db9e338be9a7e5950a4c0bb7be0825ea`.
- **Status:** **Corrective assertion committed; helper and full emulator verification pending.**


### TE-016 — Understanding checkpoint screenshot clipped the question action
- **Date discovered:** 2026-10-23
- **Area:** Android live tutor transcript auto-scroll and visual acceptance capture.
- **Symptom/failure:** The UI smoke run [39966569063](https://github.com/Prav1525/Padippupal/actions/runs/39966569063) passed functional checkpoint assertions, but the captured `live-checkpoint.png` showed the full-width “I have a question” button partly below the visible viewport.
- **Root cause:** The transcript auto-scrolled when the segment index changed, but the checkpoint state appeared after speech completion without a dedicated scroll-to-end pass after the checkpoint controls were composed. The screenshot was captured immediately after the accessibility tree exposed the checkpoint, before any such visual settling.
- **Why it escaped:** Existing assertions checked that the button existed in the accessibility tree and had the intended full-width/height contract, but did not ensure the viewport was scrolled to show the complete control.
- **Corrective action:** Add a checkpoint/completion-state effect that scrolls to the transcript end after layout, and allow the smoke screenshot one second for the UI state to settle.
- **Regression protection:** Add source-contract assertions for checkpoint auto-scroll and screenshot settling; inspect the screenshot from the exact tested SHA and verify the question button is fully visible above system navigation.
- **Evidence:** Initial screenshot artifact `padippupal-emulator-ui`, run [39966569063](https://github.com/Prav1525/Padippupal/actions/runs/39966569063), commit `5575ff3a99901a355419382412a2b743b31e98ae`. Fix verification pending.
- **Status:** **Fix implemented; verification pending.**


### TE-017 — Live smoke assertion rejected the actual understanding checkpoint label

- **Date discovered:** 2026-10-23
- **Area:** Android UI smoke harness / live lesson state detection.
- **Symptom/failure:** UI smoke run [39971641146](https://github.com/Prav1525/Padippupal/actions/runs/39971641146) reached the All 1s lesson checkpoint and displayed all three feedback actions, but failed with “Live lesson is missing its teaching, checkpoint, or completion state.”
- **Confirmed root cause:** `.github/scripts/ui_smoke.py::assert_live()` accepted several state labels but omitted the actual Compose checkpoint wording, “Does that make sense so far?”. The lesson state was present; the test harness did not recognize it.
- **Why it escaped:** Helper tests did not exercise `assert_live()` with the exact checkpoint wording produced by the real UI.
- **Corrective action:** Add the actual checkpoint label to the accepted state labels and add a focused regression test using an accessibility XML fixture with the real checkpoint and its teaching/animation/control labels.
- **Regression protection:** Run `python3 .github/scripts/test_ui_smoke_helpers.py` before emulator tests; then rerun the full emulator flow and inspect screenshot evidence from the same commit.
- **Evidence:** Failing workflow run [39971641146](https://github.com/Prav1525/Padippupal/actions/runs/39971641146), prior tested commit `48df77095823aed1b99ab3629df280a01d1acc5f`. Corrective commit and rerun evidence to be added after verification.
- **Status:** **Correction prepared; verification pending.**


### TE-020 — Live word highlight advanced before speech playback began

- **Date discovered:** 2026-10-23
- **Area:** Android live tutor caption / audio synchronization.
- **Symptom:** Word highlighting could begin while the natural-voice request was still being generated or while Android TextToSpeech was still initializing; the fallback timer could also drift from actual speech.
- **Root cause:** The live caption effect treated `speechActive` as proof of audible playback. That flag is set before network generation and TTS startup complete. The timed caption path used a fixed 24-second word loop, independent of audio position.
- **Corrective action:** Keep the first word unhighlighted (`liveWordIndex = -1`) during preparation; gate caption highlighting and the live elapsed-time fallback on `speechPlaybackObserved`; use the actual hosted player position/word timings or Android TTS range callbacks after playback begins.
- **Regression protection:** `.github/scripts/test_ui_smoke_helpers.py::SpeechHighlightSynchronizationRegressionTests` asserts the playback-observed gate, initial no-highlight state, and removal of the independent 24-second caption timer. Run helper tests before emulator allocation, then inspect live-caption screenshots and playback logs from the same commit.
- **Status:** **Fix and regression assertion committed; test and emulator verification pending.**


### TE-021 — First word highlight led audible playback onset
- **Date discovered:** 2026-10-23
- **Area:** Android live tutor speech/highlight synchronization.
- **Symptom:** The first highlighted word could appear slightly before the first audible samples even though the app had received a speech-start callback.
- **Root cause:** Android TTS `onStart` and MediaPlayer `start()` can report start before audio output is perceptible; the UI enabled word highlighting immediately on those signals.
- **Corrective action:** Delay enabling the visual playback gate by 160 ms after the platform start signal, guarded by the active utterance/generation and current MediaPlayer identity. Word progression after the gate continues to use native TTS range callbacks or hosted audio playback position/timing data.
- **Regression protection:** `.github/scripts/test_ui_smoke_helpers.py::SpeechPlaybackLeadRegressionTests` checks both playback paths have the guarded delayed gate. Run the helper suite, Android JVM tests, APK build, and emulator screenshot/voice regression on this exact revision.
- **Status:** **Patch prepared; verification pending.**


### TE-022 — Regression helper syntax error blocked emulator validation
- **Date discovered:** 2026-10-23
- **Area:** Python UI smoke helper tests / speech-highlight regression coverage.
- **Symptom:** Android UI smoke run [39981519885](https://github.com/Prav1525/Padippupal/actions/runs/39981519885) built the APK and passed fast JVM tests, but script validation failed with a Python `SyntaxError: unterminated string literal` in the natural-voice fallback assertion. Emulator allocation and UI checks were skipped.
- **Root cause:** The apostrophe in `phone's` was escaped incorrectly inside a single-quoted Python literal, leaving the test file syntactically invalid.
- **Why it escaped:** The workflow ran the helper script after committing the new assertion, but the syntax error itself prevented any helper regression tests from executing.
- **Corrective action:** Use a double-quoted Python literal for the fallback text assertion; this changes only test quoting, not the production speech/highlight logic.
- **Regression protection:** Keep script validation before emulator allocation. Run `python3 .github/scripts/test_ui_smoke_helpers.py` on the latest commit before relying on emulator results.
- **Evidence:** Failed run [39981519885](https://github.com/Prav1525/Padippupal/actions/runs/39981519885), job `120509746200`; test correction commit `7eac81305e4d402fb092700613a8f146f0969cfb`.
- **Status:** **Test syntax corrected; helper suite and emulator verification pending.**


### TE-023 — Playback-gate regression tests were stale and an unused timer implementation remained

- **Date discovered:** 2026-10-23
- **Area:** Tutor caption source-contract tests / legacy speech-caption implementation.
- **Symptom:** UI smoke workflow `39983540041` passed JVM tests and APK build, but pre-emulator helper tests failed in two places: the checkpoint-layout test expected the old ungated `WordByWordCaption(liveCaption, speechActive, ...)` call, and the synchronization test rejected the fixed 24-second timer string anywhere in the file.
- **Confirmed root cause:** The production live caption correctly used `speechActive && speechPlaybackObserved`, but one layout assertion had not been updated to that intended contract. Separately, the old private `SpeakingCaption` composable was no longer used by the live lesson, but it still contained the obsolete independent 24-second timer; the global test was correctly detecting leftover unsafe implementation.
- **Corrective action:** Updated the layout regression assertion to require the playback-observed gate and removed the unused timer-based `SpeakingCaption` implementation rather than weakening the no-fixed-timer assertion.
- **Regression protection:** Keep the helper assertion requiring `speechActive && speechPlaybackObserved`; keep the prohibition on the fixed 24-second timer. Run helper tests first, then JVM tests, APK build, and a fresh emulator flow with screenshot review on the final head SHA.
- **Evidence:** Failed run [39983540041](https://github.com/Prav1525/Padippupal/actions/runs/39983540041), job `120517388448`; assertion update commit `b870a0803d85fd7ea922bb17e74402f2480e7242`; obsolete implementation removal commit `7cd36c01025ad2cecd5d4493cfb328a1f6a86363`.
- **Status:** **Correction committed; latest-head helper and emulator verification pending.**


### TE-024 — Tutor header consumed excessive vertical space
- **Date discovered:** 2026-10-23
- **Area:** Android tutor-screen visual layout.
- **Symptom:** The current-head emulator screenshot showed a tall dark header with oversized branding/icon, reducing the vertical space available to the lesson transcript and checkpoint.
- **Root cause:** Header used 18dp combined vertical padding, a 38dp icon container, 18sp title text, and 10sp subtitle text; the combination was disproportionate on the tested viewport.
- **Why it escaped:** Prior screenshot review focused on checkpoint visibility and lesson progression, but did not explicitly evaluate header height relative to the viewport.
- **Corrective action:** Reduced combined header vertical padding to 5dp, icon container to 30dp, title to 16sp, subtitle to 9sp, and tightened horizontal/line spacing.
- **Regression protection:** Added `.github/scripts/test_ui_smoke_helpers.py::TutorHeaderLayoutRegressionTests` to assert compact dimensions while preserving Back, Teach, Pause/Resume, and Stop actions. Inspect fresh emulator screenshots from the exact tested SHA for clipping, touch-target usability, and overall header/body balance.
- **Evidence:** Implementation commit `cf69ae360b28e89a9c03bf207fedc92b5098713f`; regression test commit `030a4ba08e83d468474d93f6d125761b2dac5958`. Fresh CI and screenshot verification pending.
- **Status:** **Implemented; verification pending.** Do not merge PR #13 until latest-head build, helper tests, emulator flow, and screenshot review pass.
