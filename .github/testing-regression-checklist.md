# PadippuPal test regression checklist

Run this checklist for every tutor-screen change; do not mark the release green from a build-only result.

1. **Backend contract first**: run the curriculum/tutor pytest suite; preserve chapter counts, unique lesson IDs, source references, minimum step counts, and challenge answer/options/hint integrity.
2. **Chapter 1 curriculum coverage**: verify every required concept label exists and lesson text explicitly contains counting, odd/even, triangular, square, cube, Virahanka, powers of 2/3, hexagonal, regular polygon, complete graph, stacked squares/triangles, Koch snowflake and the 192-edge stage.
3. **API against deployed service**: confirm CBSE Class 6 Mathematics outline returns 10 chapters, Chapter 1 is Patterns in Mathematics, and its topic list is non-empty. Keep API success separate from UI success.
4. **Fast Android checks before emulator**: run Kotlin/JVM tests, assemble the debug APK, and compile/run smoke-test helper unit tests before allocating the emulator.
5. **UI flow, not just screen presence**: verify profile -> tutor -> feedback action -> settings -> Mathematics -> Chapter 1 -> select a numbered concept -> lesson actually opens -> spoken caption visible -> highlight appears in captured frames.
- [ ] At the understanding checkpoint, wait for checkpoint auto-scroll and inspect the captured screenshot; the full-width “I have a question” control must be completely visible above system navigation, not merely present in the accessibility tree.
- [ ] Inspect the tutor header on the same final emulator screenshots: branding must be compact, Back/Teach/Pause/Resume/Stop remain visible and usable, and the header must not consume disproportionate viewport height.
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

## Active objective: Phase 1 — tutor-screen layout cleanup

**Scope (do not expand without a blocking dependency):**
1. Remove the "Tap any word to hear its pronunciation again" prompt and its unnecessary tap interaction from the current tutor screen, while preserving speech and inline highlighting.
2. Make the lesson body use available vertical space without hiding bottom controls or overlapping system bars/keyboard.
3. Remove faded previews of upcoming lesson text; present the active teaching segment clearly.
4. Fix playback/loading status so "Preparing segment..." appears only while genuinely preparing, then transitions to the correct speaking/paused/finished/error state.
5. Simplify visual hierarchy and controls without breaking pause/stop, student input, or navigation.

**Acceptance criteria:**
- Prompt and tap-to-pronounce affordance are absent from the tutor lesson UI; speech and inline highlight still work.
- On the supported emulator viewport, the lesson content uses available space appropriately with no unexplained large blank region, clipping, overlap, or hidden controls.
- Only the active lesson segment is shown; no faded upcoming paragraph is visible.
- Loading status is truthful and does not remain stuck while playback is active.
- Back navigation, pause/stop, and student input remain functional.
- Backend tests, JVM/helper tests, APK build, and relevant emulator regression tests pass; inspect screenshots and logs from the final run.
- If any criterion fails, Phase 1 remains open. Do not start Phase 2 (speech/highlight synchronization) until Phase 1 is verified.

## Mandatory pre-test mistake-prevention gate

**Before every test run, read `docs/TESTING_ERRORS.md` and this checklist. Do not start testing until the known-failure checks relevant to the current change have been mapped to explicit tests or verification steps.** If a known mistake has no regression test or practical safeguard yet, add one before proceeding whenever feasible; otherwise document the blocker and do not claim the risk is covered.

- [ ] Read the testing-error log and identify prior failures related to the files, behavior, test harness, APIs, emulator, or workflow being changed.
- [ ] State the active objective, acceptance criteria, affected system layers, and exact commands/checks before running tests.
- [ ] Trace the expected path end to end (data/source -> backend validation/API -> Android parsing/state -> playback/UI -> observable user outcome) where applicable.
- [ ] For each prior failure that could recur, confirm a regression test or explicit preflight catches it; do not assume a test exists without locating it.
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
7. Only then provide a status report or consider release/merge readiness.


### Tutor vertical-layout regression gate

- [ ] Command bar is bounded to 48–52dp; Back/Pause/Resume/Stop remain usable and not clipped.
- [ ] The lesson transcript scrolls independently and fills the flexible space; checkpoint controls are in-flow below it, pinned to the bottom of the tutor screen rather than inside the transcript scroll container.
- [ ] Fresh screenshots from the exact tested SHA show all three checkpoint actions above system navigation with no large unused region beneath them.
- [ ] Helper tests, JVM tests, APK build, and emulator flow pass after any layout change; inspect both live lesson and checkpoint screenshots before marking verified.
