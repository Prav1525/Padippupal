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
- **Confirmed immediate cause:** The lesson-plan endpoint returned a response that passed the API's grounded and non-empty-segment checks, but the Android All 1s topic guard rejected at least one segment or found no explicit repeated-one topic signal. The captured smoke evidence does not expose which segment triggered the guard, so the exact offending wording / whether the hosted backend was stale remains unconfirmed.
- **Why it escaped:** The Android request prompt named the selected topic but did not explicitly require every generated segment to stay within the All 1s concept. The rejection message also hid the failed validator condition, preventing the smoke report from identifying the precise mismatch.
- **Corrective action:** Add an All 1s-specific generation guardrail requiring every segment to explain repeated ones or the invariant that each value stays the same; prohibit square-number/counting-up-and-down drift; fail closed when source grounding is insufficient. Improve the rejection message to report the rejected segment indices and reason categories without logging lesson text.
- **Regression protection:** Add a static helper test verifying the topic guardrail and actionable rejection diagnostics remain in the Android request path. Continue requiring the real emulator flow, backend tests, APK build, and screenshot/log review; do not weaken the per-segment validator.
- **Evidence:** Failed UI run [39882430428](https://github.com/Prav1525/Padippupal/actions/runs/39882430428), artifact [12471073829](https://github.com/Prav1525/Padippupal/actions/runs/39882430428/artifacts/12471073829); fix commits d86174adfe5450bc77bced0e26ff9c37702b30e1 and 02f278b283eb8dcbd4e4092657d2a0bfa7fb838b.
- **Status:** **Fix committed; verification pending.** Do not mark the tutor flow fixed until the current head passes the UI smoke test and the captured live-lesson screenshots are reviewed.

## Update protocol

- Add a new numbered incident instead of overwriting history.
- If one incident has multiple separate root causes, split them into separate entries.
- Link exact GitHub Actions runs and record the tested commit SHA.
- After a fix, update the incident's corrective-action and status fields, but preserve the original failure description.
- Before running tests, turn relevant open incidents into a short preflight checklist and ensure each has a regression test or explicit safeguard.
- Never call a test suite green based on an older SHA, a build-only run, or a run that did not exercise the failing path.
