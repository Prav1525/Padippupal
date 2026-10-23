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
