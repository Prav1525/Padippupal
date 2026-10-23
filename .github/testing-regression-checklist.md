# PadippuPal test regression checklist

Run this checklist for every tutor-screen change; do not mark the release green from a build-only result.

1. **Backend contract first**: run the curriculum/tutor pytest suite; preserve chapter counts, unique lesson IDs, source references, minimum step counts, and challenge answer/options/hint integrity.
2. **Chapter 1 curriculum coverage**: verify every required concept label exists and lesson text explicitly contains counting, odd/even, triangular, square, cube, Virahanka, powers of 2/3, hexagonal, regular polygon, complete graph, stacked squares/triangles, Koch snowflake and the 192-edge stage.
3. **API against deployed service**: confirm CBSE Class 6 Mathematics outline returns 10 chapters, Chapter 1 is Patterns in Mathematics, and its topic list is non-empty. Keep API success separate from UI success.
4. **Fast Android checks before emulator**: run Kotlin/JVM tests, assemble the debug APK, and compile/run smoke-test helper unit tests before allocating the emulator.
5. **UI flow, not just screen presence**: verify profile -> home -> lesson selection -> Mathematics -> Chapter 1 -> select a numbered concept -> Done -> clean tutor screen with Teach and no Change control -> Teach -> complete explanation -> spoken caption -> highlight in captured frames; no per-reply feedback prompt.
6. **Accessibility selector resilience**: Android XML may omit clickable/enabled flags for Compose rows. Select only visible numbered rows with valid non-zero bounds; prefer clickable nodes when present, but verify the tap by observing the next state. Never interpret a visible option as proof selection succeeded.
7. **Failure diagnosis**: preserve XML/screenshots/logs; classify failure as app behavior, test harness, API/data, emulator/ADB, or timing. Fix the cause before rerun; do not simply loosen assertions or skip the failed step.
8. **Bounded waits**: every emulator/ADB action has a timeout; detect emulator/ADB unavailability and fail with a diagnostic rather than waiting indefinitely.
9. **Release gate**: report each layer independently (backend tests, deployed API, JVM tests, APK build, emulator flow, inline highlight). Any required layer failing means overall status is not passed.

## Working agreement: finish before switching

- Keep exactly one active implementation objective at a time, with explicit scope and acceptance criteria.
- Diagnose the root cause before changing code. Avoid speculative patches and repeated fixes to the same symptom.
- Implement the fix and add/strengthen regression tests without weakening assertions just to get a green run.
- Verify actual behavior, not only compilation or widget presence. Preserve logs, screenshots, and recordings where relevant.
- Report status precisely as **Implemented**, **Tested**, **Verified**, or **Blocked**; these labels are not interchangeable.
- Put unrelated discoveries in a backlog. Switch immediately only if the issue blocks the active objective or presents a security/data-integrity risk.
- Do not start the next phase until all acceptance criteria for the current phase pass. If a required test fails, stay on the current objective, diagnose, fix, and rerun.
- At handoff, record what changed, what passed, what remains unverified, and the single next objective.

## Active objective: Combined release — complete tutor lesson flow

**Scope (single integrated release):**
1. Ensure the selected chapter/topic reaches the correct backend and all spoken content passes topic/source validation; fail safely on off-topic content.
2. Teach the complete selected topic in one coherent, grade-appropriate explanation with a definition, worked example, key rule, and recap; combine transport segments into one caption/audio flow.
3. Remove mid-lesson understanding checkpoints, per-reply feedback prompts, animation/interactive overlays, and faded upcoming text.
4. Preserve synchronized inline word highlighting, pause/resume/stop, truthful loading states, and follow-up questions after the explanation.
5. Keep the tutor screen uncluttered and ensure controls, content, system bars, and keyboard do not overlap.

**Acceptance criteria:**
- The complete topic appears as one continuous teaching caption/audio flow; no per-segment checkpoint, feedback prompt, animation, or visual overlay appears.
- The selected topic is validated end-to-end; unrelated lesson content is rejected and safe source-grounded recovery is verified.
- Inline word highlighting visibly advances with speech; pause, resume, stop, back navigation, and follow-up input work.
- Loading status is truthful and the complete caption fits the supported viewport without hidden controls, clipping, or overlap.
- Backend tests, JVM/helper tests, APK build, deployed-API contract checks, emulator journey, and screenshot review pass on the same tested commit.
- Any failing or unverified acceptance item keeps the combined release open.

## Mandatory pre-test mistake-prevention gate

**Before every test run, read `docs/TESTING_ERRORS.md` and this checklist. Do not start testing until the known-failure checks relevant to the current change have been mapped to explicit tests or verification steps.** If a known mistake has no regression test or practical safeguard yet, add one before proceeding whenever feasible; otherwise document the blocker and do not claim the risk is covered.

- [ ] Read the testing-error log and identify prior failures related to the files, behavior, test harness, APIs, emulator, or workflow being changed.
- [ ] State the active objective, acceptance criteria, affected system layers, and exact commands/checks before running tests.
- [ ] Trace the expected path end to end (data/source -> backend validation/API -> Android parsing/state -> playback/UI -> observable user outcome) where applicable.
- [ ] For each prior failure that could recur, confirm a regression test or explicit preflight catches it; do not assume a test exists without locating it.
- [ ] Follow-up chat: inspect the composer and send control accessibility XML; selectors must support `content-desc` as well as `text`. After tapping Send, assert the submitted learner question appears in chat history before accepting a tutor answer; never infer submission from text remaining in the composer.
- [ ] Tutor prompt contract: confirm one complete selected-topic explanation (definition, why/how, worked example, key rule, relevant common mistake, recap) with no legacy single-step, 20–45-word, or forced per-segment checkpoint instruction.
- [ ] Keep tests meaningful: never delete, weaken, skip, or rewrite a valid failing assertion merely to obtain a green run. If a test expectation is wrong, prove that independently and document why.
- [ ] When a test fails, preserve the failing assertion, logs/screenshots, commit SHA, and environment; classify the cause before editing.
- [ ] Fix the root cause, add a regression test/safeguard, and rerun the failed test plus affected neighboring tests. Then rerun all required release-gate checks on the latest commit.
- [ ] Check for interactions/regressions across backend, Android, CI scripts, and deployed API. A build passing is not proof that the user journey works.
- [ ] Update `docs/TESTING_ERRORS.md` in the same workstream for every meaningful mistake/failure: symptom, root cause, why it escaped, corrective action, regression protection, affected commit/run, and current status.
- [ ] Report each result accurately as **passed**, **failed**, **blocked**, or **not run**. Never say fixed/verified until the relevant rerun passes. Keep the PR unmerged while required checks or acceptance criteria fail.

### Required test-run order

1. Read this checklist and `docs/TESTING_ERRORS.md`.
2. Inspect current branch/commit and relevant existing tests; identify the previous failure modes that apply.
3. Define the fix and regression coverage before executing the test suite.
4. Run the narrowest relevant test first; diagnose any failure before proceeding.
5. Run neighboring/regression tests, then full required CI and end-to-end checks.
6. Inspect actual outputs (logs, screenshots, UI state), confirm they correspond to the latest tested SHA, and update the error log.
7. For tutor UX changes, verify a complete grade-appropriate explanation, text-only examples (no animation/lab overlays), natural follow-up answers, and no feedback prompt after each assistant reply. If the UI lacks a reliable end-of-lesson state, do not reintroduce per-reply feedback.
8. Only then provide a status report or consider release/merge readiness.
