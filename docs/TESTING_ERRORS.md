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


### TE-025 — Tutor header sizing and checkpoint actions wasted vertical space

- **Date discovered:** 2026-10-23
- **Area:** Android live tutor layout / viewport usage.
- **Symptom:** The emulator screenshot showed a tall command header and a large unused area below the understanding actions, despite the header's earlier padding reduction and a passing visibility smoke test.
- **Root cause:** The header row was still sized by its largest interactive children and used oversized title/icon styling. Separately, checkpoint actions were children of the scrollable transcript, so when the lesson content was shorter than the viewport the actions remained near the top and left empty space below them.
- **Why it escaped:** The previous header regression checked styling constants but not the command bar's bounded height. Checkpoint tests verified that controls existed and were visible, but did not require them to occupy the bottom of the available tutor screen.
- **Corrective action:** Bound the command bar to 48–52dp, reduced the icon and title/subtitle sizing while preserving accessible action controls, and moved checkpoint feedback into a fixed in-flow section below the independently scrollable transcript. This keeps controls on the same screen without an overlay and lets the lesson transcript use the remaining height.
- **Regression protection:** Helper tests now assert the bounded header contract and that checkpoint controls are outside the scrollable transcript but remain within the live lesson screen. Build and emulator checks must pass, and fresh live-lesson and live-checkpoint screenshots from the exact tested head must be inspected for touch-target usability, no clipping, and no blank area below the checkpoint actions.
- **Affected commits:** Header 229aa08afdebfb66ceba5166182a8bcf81857212; pinned checkpoint layout a2b3b1ea0d55cefb7d4971da4d0063441618c810; regression assertions pending CI verification.
- **Status:** **Implemented; regression/build/emulator verification pending.** Keep PR #13 open until exact-head screenshots and all acceptance checks pass.


### TE-026 — Checkpoint pinning fixed bottom gap but left a large gap above controls
- **Date discovered:** 2026-10-23
- **Area:** Android live tutor viewport distribution.
- **Symptom:** Fresh emulator screenshot from commit `cf42777ee9cc605cd82cf5824cb82fd80d598406` confirmed the header was compact and the checkpoint controls were pinned above system navigation, but a large blank block remained between the inline All 1s animation and the checkpoint prompt.
- **Root cause:** The transcript occupied the weighted viewport with `Arrangement.spacedBy(12.dp)`, which kept all short lesson content top-aligned while the checkpoint controls were correctly outside the scrollable transcript at the bottom.
- **First attempted correction:** `Arrangement.SpaceEvenly` was added, but deeper Compose constraint review showed that `verticalScroll` measures its child with unbounded height, so arrangement alone cannot distribute extra viewport space. This attempt was insufficient and is not accepted as the final fix.
- **Corrective action:** Wrap the weighted lesson area in `BoxWithConstraints`; when checkpoint controls are visible, give the scroll-content column a minimum height equal to the available viewport minus its vertical padding. `Arrangement.SpaceEvenly` can then distribute the short content across the viewport. Longer lessons still scroll naturally; speaking state retains compact 12dp spacing.
- **Regression protection:** Extend `.github/scripts/test_ui_smoke_helpers.py::CheckpointLayoutRegressionTests` to require the conditional arrangement and verify checkpoint controls remain outside the scrollable transcript. Review the exact-head emulator checkpoint screenshot for balanced spacing, intact touch targets, and no clipping; run helper tests before the APK/emulator workflow.
- **Evidence:** Baseline screenshot artifact `padippupal-emulator-ui`, run [39989220068](https://github.com/Prav1525/Padippupal/actions/runs/39989220068), tested SHA `cf42777ee9cc605cd82cf5824cb82fd80d598406`. Viewport-bound correction and regression verification pending.
- **Status:** **Fix and regression guard committed; verification pending.**


### TE-027 — UI smoke preflight failed on a stale source anchor
- **Date discovered:** 2026-10-23
- **Area:** Checkpoint layout regression helper.
- **Symptom:** Android build passed, but the UI workflow stopped before emulator launch because `CheckpointLayoutRegressionTests` searched for the old comment `// One continuous, scrollable lesson transcript`; the implementation had evolved to a viewport-constrained wrapper, so the source marker no longer existed.
- **Root cause:** The test used a presentation comment as its code-region boundary, making it brittle to a legitimate layout refactor.
- **Corrective action:** Anchor the test to the stable weighted scrollable-column declaration rather than the obsolete comment.
- **Regression protection:** Run `python3 .github/scripts/test_ui_smoke_helpers.py` in the required pre-emulator validation step; only continue to emulator allocation after all helper tests pass.
- **Evidence:** UI smoke run [39992103654](https://github.com/Prav1525/Padippupal/actions/runs/39992103654), PR merge SHA `55067e2244e4cabbea3c9b64ab8bdc0ce59d7d12`; code fix commit `14d73941dff71a827ea4b331729087b5f2f06e3a`.
- **Status:** **Test anchor corrected; helper rerun and screenshot verification pending.**


### TE-028 — Checkpoint layout helper failed before emulator allocation on stale selector
- **Date discovered:** 2026-10-23
- **Area:** Android UI regression helper.
- **Symptom:** UI smoke workflow [39993092646](https://github.com/Prav1525/Padippupal/actions/runs/39993092646) passed JVM tests and built the debug APK, then stopped during script validation with `ValueError: substring not found` in `CheckpointLayoutRegressionTests`.
- **Root cause:** The test sliced the lesson layout using the previous direct `Column(...verticalScroll...)` declaration after production correctly introduced a `BoxWithConstraints` viewport wrapper. The layout assertion itself never ran.
- **Corrective action:** Anchor the lesson layout slice to the stable `BoxWithConstraints(Modifier.weight(1f).fillMaxWidth())` wrapper and keep all subsequent layout assertions intact.
- **Regression protection:** Run `python3 -m py_compile .github/scripts/ui_smoke.py .github/scripts/test_ui_smoke_helpers.py .github/scripts/tutor_smoke_api.py` and `python3 .github/scripts/test_ui_smoke_helpers.py` before emulator allocation; do not treat an APK build as a UI pass.
- **Evidence:** Failure log from run [39993092646](https://github.com/Prav1525/Padippupal/actions/runs/39993092646), job `120550208202`, head `6b3cc51e0a890c5b37e0fb23900b8b7a060596d1`. Anchor correction committed; rerun pending.
- **Status:** **Test anchor corrected; verification pending.**


### TE-029 — Disabled Teach action rendered with insufficient contrast

- **Date discovered:** 2026-10-24
- **Area:** Android tutor header / initial lesson-selection state.
- **Symptom:** The emulator tutor screenshot shows the Teach action almost invisible before a chapter or topic is selected.
- **Root cause:** The button is correctly disabled until lesson selection, but its disabled Material button colors were not explicitly set; the theme's default disabled styling reduced text and background contrast.
- **Corrective action:** Explicitly set disabled container and content colors so Teach remains legible while still disabled.
- **Regression protection:** Rebuild and inspect the tutor screenshot at the exact tested commit; confirm Teach is legible before selection and remains disabled until a chapter/topic is chosen.
- **Evidence:** Fix commit `b0cb214f6cc0a9d4e5fe18c40f65e0690895d407`; CI and screenshot verification pending.
- **Status:** **Implemented; verification pending.** The separate-screen lesson-selection flow and large blank area on the pre-lesson tutor screen remain open acceptance issues.

### TE-030 — Unselected tutor opened into a greeting chat with unused viewport space

- **Date discovered:** 2026-10-24
- **Area:** Android tutor ready/idle state.
- **Symptom:** Before a lesson was selected, the tutor screen showed a generic greeting bubble and an empty question composer, leaving a large blank area and making the page look unfinished.
- **Root cause:** The default chat transcript and composer were rendered even when both chapter and topic were blank; there was no intentional empty state for lesson selection.
- **Why it escaped:** Existing smoke checks only required recognizable tutor labels plus Change and Teach controls. They did not assert the unselected-state content or prevent an empty chat composer from appearing.
- **Corrective action:** Render a centered, compact lesson-selection invitation with a clear “Choose a lesson” action when no chapter/topic is selected; hide the general chat composer until selection exists. Keep the actual teaching experience on the tutor screen.
- **Regression protection:** Added `.github/scripts/test_ui_smoke_helpers.py::TutorIdleStateRegressionTests` to require the empty state and guard the composer condition. Latest-head helper/JVM/build/emulator checks and screenshot review are required before verification.
- **Evidence:** Implementation commit `f2f8cb570855c3129dd58dbbd2dfa1ad475f55ab`; regression test commit pending.
- **Status:** **Implemented; regression and screenshot verification pending.**

### TE-031 — Tutor idle-screen icon broke Kotlin compilation

- **Date discovered:** 2026-10-24
- **Area:** Android build / tutor idle-state UI.
- **Symptom:** Android APK build and emulator smoke test both failed at Kotlin compilation with `Unresolved reference 'MenuBook'` in `TutorScreen.kt`.
- **Root cause:** The new idle-state UI used a Material icon that is not included in the project's available icon set/imports.
- **Why it escaped:** The UI change was committed before a build was run against the exact resulting commit.
- **Corrective action:** Replaced the unavailable icon with a text-based book symbol; no dependency or icon-pack change needed.
- **Regression protection:** Re-run APK build and UI smoke tests on the corrected commit; inspect emulator screenshot before claiming verified.
- **Evidence:** Failure on commit `4bee813bb37ab33edb6a57192a02e3f96ff9e31e`; fix commit pending.
- **Status:** **Fix committed; rerun checks pending.**


### TE-032 — Checkpoint spacing created an oversized gap below the tutor header

- **Date discovered:** 2026-10-24
- **Area:** Android live tutor checkpoint layout.
- **Symptom:** The exact-head emulator checkpoint screenshot showed a large blank gap between the compact header and the checkpoint heading, making the teaching flow feel disconnected.
- **Root cause:** `Arrangement.SpaceEvenly` distributed a short transcript's spare viewport height across every child gap, including the gap immediately below the header.
- **Corrective action:** Replace space-distributed placement with fixed, readable 16dp spacing during the checkpoint; retain 12dp spacing while speaking. The transcript remains independently scrollable and checkpoint actions stay in-flow below it.
- **Regression protection:** Update `.github/scripts/test_ui_smoke_helpers.py::CheckpointLayoutRegressionTests` to assert the bounded spacing policy and rerun helper tests, JVM tests, APK build, emulator flow, and inspect a fresh checkpoint screenshot.
- **Evidence:** Baseline emulator run [40038927517](https://github.com/Prav1525/Padippupal/actions/runs/40038927517), screenshot artifact [12538666569](https://github.com/Prav1525/Padippupal/actions/runs/40038927517/artifacts/12538666569). Fix commit and verification pending.
- **Status:** **Fix implemented; exact-head verification pending.**


### TE-033 — Tutor header and checkpoint spacing drifted from the design contract

- **Date discovered:** 2026-10-24
- **Area:** Tutor header typography; checkpoint transcript spacing; UI smoke helper assertions.
- **Symptom:** Android UI smoke run [40043958637](https://github.com/Prav1525/Padippupal/actions/runs/40043958637) passed JVM tests and APK build, but failed script validation on two helper tests. The header title was 16sp while the compact-header contract expected 14sp. The checkpoint transcript used 10dp spacing while the previously documented layout contract required 16dp when awaiting understanding.
- **Root cause:** UI spacing/type values drifted from the documented design contract, and the helper suite also retained a stale 8sp metadata expectation that contradicted the design guide's minimum 11sp for dense metadata.
- **Why it escaped:** The last run stopped before emulator allocation, so the source-level regression assertions were the first checks to catch the drift. Earlier APK compilation could not catch these visual-contract mismatches.
- **Corrective action:** Set the brand title to 14sp; restore 16dp vertical spacing at the understanding checkpoint while retaining 12dp during speech; update the stale metadata assertion to 11sp rather than shrinking meaningful context to 8sp.
- **Regression protection:** Keep the compact header bounds/icon/action assertions; assert 14sp brand title and 11sp context metadata; keep the 16dp checkpoint/12dp speaking spacing assertion. Run helper tests, JVM tests, APK build, emulator navigation/checkpoint flow, and inspect exact-head screenshots before claiming completion.
- **Evidence:** Failure run [40043958637](https://github.com/Prav1525/Padippupal/actions/runs/40043958637), commit before fix `99f6cd91348e3b4129cafb72f1a5641460a98732`. Corrective commits: source `584cf72632dab3d8d9b5e61bb3f127cf92503a64`; regression assertion `7315120c2120f61fd89827f541b1d1fc0962306a`. Verification pending.
- **Status:** **Fix implemented; exact-head verification pending.**

### TE-034 — Highlight pixel detector searched for a retired color

- **Date discovered:** 2026-10-24
- **Area:** Android UI smoke screenshot analysis / speech-highlight regression gate.
- **Symptom/failure:** UI smoke run [40045309104](https://github.com/Prav1525/Padippupal/actions/runs/40045309104) reached the live All 1s lesson, but the screenshot scan reported zero highlight pixels across 100 frames and failed the job.
- **Confirmed root cause:** The screenshot detector searched for RGB `(220, 231, 255)` / `#DCE7FF`, a retired blue highlight. The current `WordByWordCaption` production style applies mint `Color(0xFFCDE9E2)` (RGB `(205, 233, 226)`). Manual inspection of artifact `12541317032`, `ui-screenshots/live-frames/frame-10.png`, shows the final word in the active spoken sentence visibly highlighted in that mint color while the speaking status is present.
- **Why it escaped:** The UI palette changed, but the screenshot detector's hard-coded expected RGB value was not updated alongside the production style. Build and source-contract tests do not compare the detector color to the rendered caption color.
- **Corrective action:** Changed the detector to search for the actual mint RGB and added a regression test asserting that the detector target matches the production `WordByWordCaption` background and rejects the stale RGB.
- **Regression protection:** `SpeechHighlightSynchronizationRegressionTests.test_screenshot_detector_matches_production_word_highlight_color`; rerun helper tests, JVM tests, APK build, and full emulator smoke on the latest SHA. Confirm the pixel detector sees at least 12 pixels and two distinct word positions, and inspect fresh live-lesson/checkpoint screenshots.
- **Evidence:** Failed baseline run [40045309104](https://github.com/Prav1525/Padippupal/actions/runs/40045309104), tested SHA `e6417f14443f6e3bf474972c4f6e6889d8a0bcac`, artifact `12541317032`; detector fix commit `2ea7f0e4c06ae397973eb8bd7786406152d121c0`; regression test commit `bc4a2fb5aeb7dc16a8154adbf2c796a3278ad5e3`.
- **Status:** **Root cause confirmed; detector/test fix implemented; exact-head verification pending.** Do not weaken the pixel threshold or merge PR #13 until the corrected detector and full release gate pass.



### TE-035 — Checkpoint animation visibility detector still searched for retired blue tiles

- **Date discovered:** 2026-10-24
- **Area:** Android checkpoint screenshot acceptance / repeated-ones animation progression.
- **Symptom/failure:** UI smoke run [40047675587](https://github.com/Prav1525/Padippupal/actions/runs/40047675587), tested SHA `eb4a8baef93038395e360ae127a08d332c469c0e`, reached the understanding checkpoint with the All 1s animation labels present but reported zero repeated-ones tile pixels in the teaching viewport.
- **Root cause:** The prior TE-034 correction updated the word-highlight detector to mint but missed a separate checkpoint-tile detector in `.github/scripts/ui_smoke.py`, which still counted retired blue RGB `(220, 231, 255)`. Production repeated-ones tiles use mint `#CDE9E2` / RGB `(205, 233, 226)`. Source inspection also confirmed the animation stage wrapped modulo 4 despite rendering five tiles, so the fifth tile could never enter the highlighted state.
- **Why it escaped:** The TE-034 regression test only compared the word-highlight detector with `WordByWordCaption`; it did not cover the independent checkpoint screenshot detector or the animation's five-stage progression.
- **Corrective action:** Update the checkpoint detector to count the production mint fill without changing its 350-pixel visibility threshold; give the repeated-ones scene five animation stages while leaving other scenes at four.
- **Regression protection:** Add helper tests that compare the checkpoint detector RGB to the production tile fill and assert the repeated-ones stage count wraps across five stages. Run the helper suite, JVM tests, APK build, and full emulator smoke; inspect live-lesson and checkpoint screenshots from the resulting exact SHA.
- **Evidence:** Failing run [40047675587](https://github.com/Prav1525/Padippupal/actions/runs/40047675587), job `120733340635`, checkpoint pixel count 0; the same run's word-highlight scan passed with 100 frames and 14 distinct positions.
- **Status:** **Fix prepared in this batch; exact-head verification pending.** Keep PR #13 open and unmerged until the full release gate passes.


### TE-036 — Checkpoint transcript viewport constraint was applied outside the scroll content

- **Date discovered:** 2026-10-24
- **Area:** Live tutor vertical layout / checkpoint screenshot acceptance.
- **Symptom:** Exact-head screenshots from UI smoke run [40050844427](https://github.com/Prav1525/Padippupal/actions/runs/40050844427), SHA `25f601b330990e0185d45595a60868536654426e`, show the lesson text and repeated-ones animation at the top, a large unused vertical block, and checkpoint actions at the bottom. The live-lesson capture also shows the checkpoint heading, so visual state needs review after the layout correction.
- **Root cause:** The minimum-height constraint was chained before `.verticalScroll()`, constraining the scroll viewport rather than ensuring the scroll content fills the available height. The checkpoint used fixed spacing, so the short content did not distribute through the viewport.
- **Why it escaped:** Existing source tests checked that a height constraint and spacing policy existed, while screenshot automation only asserted visibility/pixel thresholds. Neither checked modifier ordering or the vertical distribution in the actual rendered checkpoint.
- **Corrective action:** Move the conditional minimum-height modifier after `.verticalScroll()` so it applies to the scroll content, and use `Arrangement.SpaceEvenly` only at the understanding checkpoint; preserve compact fixed spacing while speaking.
- **Regression protection:** Strengthen `CheckpointLayoutRegressionTests` to assert modifier order, the conditional minimum height on the scroll content, and checkpoint-only vertical distribution. Re-run helper/JVM tests, APK build, full emulator smoke, and inspect fresh screenshots from the resulting exact SHA.
- **Evidence:** Screenshots `ui-screenshots/live-lesson.png` and `ui-screenshots/live-checkpoint.png` from artifact `12543432314`; automated checks passed on the baseline SHA but screenshot inspection found the layout defect.
- **Status:** **Fix prepared; exact-head verification pending.** Keep PR #13 open and unmerged.

### TE-037 — Live viewport fix did not cover the speaking state
- **Date discovered:** 2026-10-24
- **Area:** Tutor Compose layout and screenshot-based acceptance.
- **Symptom/failure:** Screenshot from run [40052525877](https://github.com/Prav1525/Padippupal/actions/runs/40052525877), artifact `12543358886`, showed the live lesson's explanation and animation clustered near the top with a large blank region below. The checkpoint screenshot looked better, so checking only that state missed the repeated UI defect.
- **Root cause:** The minimum content height and distributed vertical spacing were conditional on `awaitingUnderstanding`; they did not apply during active speech.
- **Why it escaped:** Existing visual acceptance focused on the checkpoint and source assertions did not require the live-speaking state to fill the viewport.
- **Corrective action:** Apply the viewport minimum-height rule in all live states and use distributed spacing during speech as well as at checkpoints. Add a source regression assertion and capture the exact-head live screen.
- **Regression protection:** UI smoke must inspect both active speaking and checkpoint screenshots. The latest smoke run [40053691110](https://github.com/Prav1525/Padippupal/actions/runs/40053691110) exposed a stale test expectation before emulator launch; that harness failure is tracked separately below.
- **Evidence:** Layout commit `e1ed82d6c74e7e0e073297d76763691ab68ca200`; regression-test commit `946df6259940ddcf717bfe91366e3326a2298a2a`; screenshot evidence from run `40052525877`.
- **Status:** **Layout fix implemented; visual verification pending.** Do not claim the dead zone is fixed until screenshots from a successful emulator run confirm it.

### TE-038 — A source regression test still required the superseded checkpoint-only layout rule
- **Date discovered:** 2026-10-24
- **Area:** UI smoke helper validation.
- **Symptom/failure:** UI smoke run [40053691110](https://github.com/Prav1525/Padippupal/actions/runs/40053691110) failed in `test_checkpoint_caption_wraps_naturally_without_debug_visual_focus_row` before emulator allocation.
- **Root cause:** The test asserted the old conditional `.heightIn(min = if (awaitingUnderstanding) maxHeight - 16.dp else 0.dp)` even after the implementation correctly changed to a viewport minimum for all live states.
- **Why it escaped:** The new focused regression test was added without updating the pre-existing source assertion that encoded the old behavior.
- **Corrective action:** Update the assertion to require the new unconditional minimum-height rule and `SpaceEvenly` during speech/checkpoint states. Extend the emulator flow to capture and validate the final topic-completion screen, not only an intermediate checkpoint.
- **Regression protection:** Script syntax/compile checks and the full helper test suite must pass before emulator allocation; final-topic screenshot and accessibility checks are required for visual acceptance.
- **Evidence:** Failed run [40053691110](https://github.com/Prav1525/Padippupal/actions/runs/40053691110), commit `946df6259940ddcf717bfe91366e3326a2298a2a`; harness corrections are being tested on the subsequent branch head.
- **Status:** **Harness corrections implemented; verification pending.**



### TE-039 — Live lesson used excessive vertical gaps and an oversized stacked header
- **Date discovered:** 2026-10-24
- **Area:** Android tutor live-lesson composition and screenshot acceptance.
- **Symptom/failure:** Fresh screenshot from UI smoke run [40054398708](https://github.com/Prav1525/Padippupal/actions/runs/40054398708), exact SHA `541b356ee09609ae15753ac545f9aa01ff88db85`, showed a tall header with stacked branding/context and `Arrangement.SpaceEvenly` distributing the introduction, spoken segments, and animation far apart. The resulting screen looked fragmented rather than like one continuous lesson.
- **Root cause:** The live lesson filled its viewport by distributing every child across all available height. The header also used two text rows plus a logo, consuming more vertical space than the lesson needed.
- **Why it escaped:** Earlier assertions checked that the viewport filled available height and that the header was present, but did not reject the screenshot-visible gaps or enforce a single-line live header.
- **Corrective action:** Keep the minimum-height scroll content, center the lesson cluster as a unit with consistent 14dp spacing, and replace the stacked header with a fixed 56dp single-line concept header while retaining Back and playback controls.
- **Regression protection:** Update source-level tests to forbid `Arrangement.SpaceEvenly` in the live viewport and require the compact header. Keep screenshot checks for live speech and checkpoint states, and drive every distinct checkpoint in the smoke journey before asserting topic completion.
- **Evidence:** Screenshot and report from artifact [12544783462](https://github.com/Prav1525/Padippupal/actions/runs/40054398708/artifacts/12544783462); UI smoke currently fails at the final completion assertion because the script does not advance a subsequent checkpoint.
- **Status:** Fix and regression updates prepared in the current tutor PR batch; exact-head CI and screenshot review pending.


### TE-040 — UI smoke reopened an already-selected concept picker and expected numbered rows
- **Date discovered:** 2026-10-24
- **Area:** Android UI smoke test navigation / setup screen.
- **Symptom/failure:** UI smoke run [40056364712](https://github.com/Prav1525/Padippupal/actions/runs/40056364712) failed after selecting Chapter 1: the accessibility tree showed `Topic / concept | All 1s` and `Done`, but no numbered concept row existed for the helper to tap.
- **Root cause:** The setup screen automatically selected the fixture's first concept (`All 1s`) when the chapter was selected. The smoke script redundantly reopened the topic picker and assumed options would have numbered labels.
- **Why it escaped:** The script's chapter assertion checked the chapter but did not assert the resulting selected concept or model the setup screen's default-selection behavior.
- **Corrective action:** Assert that `All 1s` is visibly selected in the chapter-selected accessibility snapshot and continue directly to `Done`; retain a hard app-failure if the expected concept is missing.
- **Regression protection:** The UI smoke flow must verify chapter selection, default concept selection, setup completion, and then Teach. Do not weaken selection checks or depend on a numbered label that is not part of the UI contract.
- **Evidence:** Failed UI smoke run [40056364712](https://github.com/Prav1525/Padippupal/actions/runs/40056364712), SHA `49fcf79150ebedc46ea885598fe3855498a9ac6a`.
- **Status:** Root cause confirmed from accessibility output; correction committed in the current batch, exact-head workflow and screenshot verification pending.

### TE-041 — Live lesson still has excessive vertical gaps on real emulator screenshot
- **Date discovered:** 2026-10-24
- **Area:** Tutor live lesson layout / visual regression.
- **Symptom:** Actual emulator screenshot showed too much unused vertical space between the spoken explanation, inline pattern animation, and understanding controls.
- **Root cause:** The live lesson content used 14dp spacing between every child plus 6dp vertical viewport padding. Even though the cluster was centered as a unit, this compounded spacing made the lesson feel fragmented on a phone screen.
- **Corrective action:** Reduced live lesson child spacing from 14dp to 8dp and vertical padding from 6dp to 2dp. Kept the animation inline and preserved the scrollable full-topic lesson flow.
- **Regression protection:** Run the Android emulator smoke flow and inspect fresh screenshots for active speech, checkpoint, continued lesson, and completed topic. Build/test success alone does not satisfy visual acceptance; compare content gaps and confirm the lesson remains readable from top to bottom.
- **Evidence:** Actual emulator screenshot from the UI smoke artifact for run [40057379049](https://github.com/Prav1525/Padippupal/actions/runs/40057379049).
- **Status:** Spacing correction committed in d3ab0916e86608870c60fa3f11ab91e54897655e; new emulator verification pending.

### TE-042 — UI helper tests retained the pre-compaction 14dp spacing assertion

- **Date discovered:** 2026-10-24
- **Area:** UI smoke helper validation / live lesson spacing.
- **Symptom/failure:** UI smoke run [40058216858](https://github.com/Prav1525/Padippupal/actions/runs/40058216858) failed in script validation before emulator allocation. Two helper tests still expected `Arrangement.spacedBy(14.dp, Alignment.CenterVertically)` after the intended spacing change to 8dp.
- **Root cause:** The production layout was updated, but two source-contract assertions in `.github/scripts/test_ui_smoke_helpers.py` were not updated to match the new intended spacing contract.
- **Why it escaped:** The helper suite was not run successfully on the exact post-spacing commit before launching the UI workflow.
- **Corrective action:** Updated both viewport and checkpoint-layout assertions to require 8dp spacing; did not remove the assertions or change production code to satisfy stale tests.
- **Regression protection:** Run the full helper validation before emulator allocation, then require a successful emulator run and inspect real screenshots for speaking, checkpoint, continued lesson, and topic completion. Ensure screenshot artifacts are actually uploaded; do not treat a source-only pass as visual acceptance.
- **Evidence:** Failure run [40058216858](https://github.com/Prav1525/Padippupal/actions/runs/40058216858), tested merge SHA `4234f3f502587b99f945b48624911cb28474f08f`; helper assertion correction commit `3cd42dd5f0b0ff5cd0e7f07293e3ef20f81c8693`.
- **Status:** **Stale assertions corrected; rerun and screenshot verification pending.**



### TE-043 — Checkpoint controls detached from the live lesson scroll flow

- **Date discovered:** 2026-10-24
- **Area:** Tutor live lesson layout / checkpoint state.
- **Symptom:** The lesson transcript occupied a weighted, centered viewport while the checkpoint prompt and action buttons rendered as a separate sibling below it. On phone-sized screens this produced a conspicuous blank vertical region between lesson content and actions, even after child spacing was reduced.
- **Root cause:** The transcript viewport and checkpoint footer were laid out as separate vertical regions. Padding-only changes could not fix the structural gap.
- **Corrective action:** Move the checkpoint prompt and actions into the same scrollable lesson column as the transcript and inline animation, so the complete lesson flow is measured and scrolled as one unit.
- **Regression protection:** Source-contract tests must assert that checkpoint prompt and all three actions occur inside the live scroll layout. Run the helper tests and Android emulator smoke; inspect fresh active-speech and checkpoint screenshots. A green build alone is not visual acceptance.
- **Evidence:** Follow-up verification for this correction is pending; do not mark the tutor UI accepted until a fresh emulator artifact is inspected.
- **Status:** Structural correction submitted for validation.


### TE-044 — Kotlin scope closure missing after moving checkpoint controls

- **Date discovered:** 2026-10-24
- **Area:** Tutor live lesson layout / Kotlin compilation.
- **Symptom:** Android APK compilation failed with `TutorScreen.kt:2288:2 Syntax error: Expecting '}'` after the checkpoint controls were moved into the live lesson column.
- **Root cause:** The automated text edit inserted the checkpoint block before closing the `liveLessonComplete` conditional, leaving that conditional unclosed.
- **Corrective action:** Add the missing closing brace before the checkpoint conditional; verify the exact source excerpt and require a successful Kotlin/Android build before further visual acceptance.
- **Regression protection:** Do not treat a successful source-layout assertion as proof of Kotlin validity. Require the APK build and UI smoke on the exact resulting head SHA, then inspect fresh screenshots.
- **Evidence:** Android APK run [40059913798](https://github.com/Prav1525/Padippupal/actions/runs/40059913798) failed compilation at line 2288. Syntax correction commit: `733f4a2267e9c5461672a2b4962208ea243132b7`.
- **Status:** Syntax correction committed; rebuild and emulator verification pending.


### TE-045 — Completion smoke loop stopped advancing a checkpoint after one unsuccessful tap

- **Date discovered:** 2026-10-24
- **Area:** Android UI smoke / multiple understanding checkpoints.
- **Symptom:** UI smoke run [40054398708](https://github.com/Prav1525/Padippupal/actions/runs/40054398708) passed lesson startup, pause/resume, moving word highlight, first checkpoint, and continuation to “Now look at the sequence.” It then timed out waiting for “TOPIC COMPLETE”; the final accessibility dump still showed “Does that make sense so far?” and the three checkpoint actions.
- **Root cause:** The completion loop tapped “I understand” once for a distinct accessibility snapshot, then never retried if the same checkpoint remained visible. The loop treated an attempted tap as if it had necessarily advanced Compose state, and spent the rest of its timeout polling the unchanged checkpoint.
- **Why it escaped:** Earlier smoke coverage checked the first checkpoint and the next teaching segment, but the final completion loop did not explicitly handle a response tap that failed to register or a delayed state transition.
- **Corrective action:** Add a bounded retry for a checkpoint that remains visible after the initial tap, while preserving the hard requirement that the actual “TOPIC COMPLETE” state must appear. This is a test-harness correction, not evidence that the app's completion state has already passed.
- **Regression protection:** Re-run helper/script validation and the full emulator flow; require a real completed-topic accessibility snapshot and screenshot, then inspect that screenshot top-to-bottom. Do not loosen the completion assertion or treat a retry log as success.
- **Evidence:** Failed emulator run [40054398708](https://github.com/Prav1525/Padippupal/actions/runs/40054398708); correction commit pending exact-head workflow results.
- **Status:** Retry added; emulator rerun and screenshot verification pending.


### TE-046 — Viewport regression tests contradicted the top-aligned production layout

- **Date discovered:** 2026-10-24
- **Area:** Android UI helper preflight / tutor lesson layout.
- **Symptom:** UI smoke run [40061682447](https://github.com/Prav1525/Padippupal/actions/runs/40061682447) on SHA `3141cd04281702b1fcfe86731cc1685be2574062` failed before emulator launch in two helper tests. Both required `.heightIn(min = (maxHeight - 16.dp).coerceAtLeast(0.dp))`, but the current production layout intentionally removed that forced minimum-height modifier and uses `verticalArrangement = Arrangement.spacedBy(8.dp)` to avoid an artificial blank band above short lessons.
- **Root cause:** The layout had evolved from vertically distributing content to natural top-aligned scrolling, but two regression assertions still encoded the previous implementation. The tests disagreed with the actual current source contract and prevented the emulator test from running.
- **Corrective action:** Updated both assertions to require the scrollable lesson column, natural 8.dp spacing, and absence of forced minimum height, `Arrangement.SpaceEvenly`, and vertical centering. Kept checkpoint-in-scroll-flow and all-three-action assertions intact.
- **Regression protection:** Helper tests must pass before emulator allocation; then the emulator smoke must still verify real live speech/highlight, checkpoint actions, completed topic, and back navigation. Do not count helper-test success as visual acceptance.
- **Evidence:** Failure run [40061682447](https://github.com/Prav1525/Padippupal/actions/runs/40061682447); assertion correction commit `daccab059e3507b71a2aeeb459ebe42641b2e371`.
- **Status:** Assertions corrected; automatic exact-head workflows and screenshot review pending.


### TE-047 — UI helper asserted obsolete lesson wording against the shell smoke script

- **Date discovered:** 2026-10-24
- **Area:** Android UI helper preflight / deterministic tutor fixture.
- **Symptom:** UI smoke run [40067982703](https://github.com/Prav1525/Padippupal/actions/runs/40067982703) on commit `f7173090a90b5c673eb7fc3643ebff1cb42627cc` built the APK and passed the other helper checks, but failed `CheckpointLayoutRegressionTests.test_checkpoint_caption_wraps_naturally_without_debug_visual_focus_row` at `self.assertIn('Now look at the sequence.', smoke)`. The emulator was skipped and no screenshot artifact was uploaded.
- **Root cause:** The assertion expected wording from an older lesson-fixture revision in `.github/scripts/android-ui-smoke.sh`, although the deterministic five-segment lesson wording is defined in `.github/scripts/tutor_smoke_api.py`. The test checked the wrong source of truth.
- **Why it escaped:** The fixture wording and smoke assertions evolved independently, and the required pre-emulator helper suite was not green on the earlier exact commit. Build success was incorrectly easy to mistake for overall validation.
- **Corrective action:** Changed the regression test to assert the intro and recap phrases against the deterministic API fixture, while separately asserting that the smoke script retains the All 1s concept and five-segment completion gate. Added mandatory guide steps to trace expected lesson wording to the current fixture and log validation failures before rerunning.
- **Regression protection:** `.github/testing-regression-checklist.md` now requires fixture/script wording alignment, helper and fixture self-tests on the exact commit, a `docs/TESTING_ERRORS.md` entry for pre-emulator failures, and inline display of visually inspected screenshots from the exact successful run/SHA.
- **Evidence:** Failure run [40067982703](https://github.com/Prav1525/Padippupal/actions/runs/40067982703); fix and guide update commits are being validated by the next exact-head workflow.
- **Status:** Assertion and guide updated; required CI rerun and emulator screenshot verification pending.

### TE-048 — Fixture wording drift exposed a deeper false-positive for mid-topic feedback

- **Date discovered:** 2026-10-24
- **Area:** Android UI smoke assertions / lesson-completion contract.
- **Symptom:** UI smoke run [40068386712](https://github.com/Prav1525/Padippupal/actions/runs/40068386712) on SHA `8787da59f427c74185d5f7b49589f7f54d42cf73` passed the APK build and 24 helper tests but failed fixture self-test because it expected `repeats` in segment 2, whose real wording is “Every term is one, so the number stays the same each time.” Emulator launch was skipped.
- **Deeper root cause:** The stale fixture assertion was only the immediate failure. More seriously, `ui_smoke.py::assert_live` and its regression test explicitly accepted “Does that make sense so far?” and the three feedback actions as a valid live lesson state. This could normalize the exact mid-topic interruption the product must prevent.
- **Corrective action:** Align the fixture self-test with the actual rule segment and recap segment. Tighten `assert_live` so feedback/checkpoint labels fail unless “TOPIC COMPLETE” is present, and replace the old checkpoint-acceptance test with negative and post-completion cases.
- **Regression protection:** Require fixture self-test, helper tests, and the full emulator flow on the exact commit. The live-lesson assertion must reject premature feedback; completion assertion and fresh screenshot inspection remain mandatory.
- **Evidence:** Failed run [40068386712](https://github.com/Prav1525/Padippupal/actions/runs/40068386712); fix commits: `b50b901cf3d2fc9ca01d5611042a548d71e76793`, `f59191b90286a72f7bcdaa6f158f3f0b922babe4`, `bddf472aac62d64fe76c69fa3d8c308e8aacf47a`.
- **Status:** Fixes committed; exact-head CI and emulator screenshot verification pending.
