# PadippuPal test regression checklist

Run this checklist for every tutor-screen change; do not mark the release green from a build-only result.

1. **Backend contract first**: run the curriculum/tutor pytest suite; preserve chapter counts, unique lesson IDs, source references, minimum step counts, and challenge answer/options/hint integrity.
2. **Chapter 1 curriculum coverage**: verify every required concept label exists and lesson text explicitly contains counting, odd/even, triangular, square, cube, Virahanka, powers of 2/3, hexagonal, regular polygon, complete graph, stacked squares/triangles, Koch snowflake and the 192-edge stage.
3. **API against deployed service**: confirm CBSE Class 6 Mathematics outline returns 10 chapters, Chapter 1 is Patterns in Mathematics, and its topic list is non-empty. Keep API success separate from UI success.
4. **Fast Android checks before emulator**: run Kotlin/JVM tests, assemble the debug APK, and compile/run smoke-test helper unit tests before allocating the emulator.
5. **UI flow, not just screen presence**: verify profile -> tutor -> feedback action -> settings -> Mathematics -> Chapter 1 -> select a numbered concept -> lesson actually opens -> spoken caption visible -> highlight appears in captured frames.
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


## Phase plan and whole-system recovery protocol (project working memory)

This is the standing workflow for PadippuPal. Follow it across chats/builds; do not revert to symptom-by-symptom patching.

### Phase order (one active phase only)

- **Phase 1 — Tutor screen and live-lesson reliability (ACTIVE; do not close yet):** layout/viewport, truthful loading and playback states, clean active-segment display, reliable speech start/fallback, pause/resume/stop, student input and back navigation. Treat failures in the lesson-plan contract, segment validation, speech callbacks, or smoke-test state isolation as blocking dependencies when they prevent Phase 1 acceptance.
- **Phase 2 — Speech/highlight synchronization:** word-level highlighting stays inline with the currently spoken caption; timing, pause/resume, scrolling and completion remain aligned.
- **Phase 3 — Curriculum-grounded teaching quality:** complete and validate Class 6 Mathematics Chapter 1 concept teaching (beginning with the selected “All 1s” concept), examples, accurate concept-matched visuals, short teacher-like segments and source grounding.
- **Phase 4 — Child understanding/response loop:** reliable checkpoints, “I understand”, “Explain again”, student questions and appropriate continuation.
- **Phase 5 — Hardening and regression:** broader device/viewport/language/network/error-path coverage, performance, accessibility and release readiness.

A later phase may be investigated only when a dependency blocks the active phase; record it as a blocking dependency, make the smallest safe fix, and return to the active phase. Do not use a blocker as permission to expand feature scope.

### Required recovery loop for every failure

1. **Reproduce and preserve evidence first.** Save the exact commit SHA, workflow/run/job IDs, test report, accessibility XML, screenshots/frame captures, relevant logcat and backend response/error. Do not overwrite evidence from a failed attempt.
2. **Classify the failure** as app/UI state, lesson-plan API/data contract, hosted audio/TTS, emulator/ADB infrastructure, or test-harness/state-isolation/timing. A run can have more than one cause; distinguish the primary failure from follow-on symptoms.
3. **Trace the full path, not just the visible symptom.** For lesson playback follow: selected board/class/subject/chapter/concept -> lesson-plan request/response -> segment validation -> selected visual action -> speech request or device TTS -> confirmed playback-start callback -> UI state/caption/highlight -> completion/checkpoint. Inspect the actual captured screen and XML before changing assertions or UI code.
4. **State a causal hypothesis and proof test before editing.** Identify the evidence supporting it and the smallest test that would prove or disprove it. Avoid speculative code changes. Never weaken or delete an assertion just to make CI green.
5. **Fix the owning layer and add regression coverage.** Validate malformed/empty segments, error and timeout paths, audio preparation failure and fallback, callback races/stale callbacks, and concept-to-visual mismatch where relevant. Keep app fixes and test-harness fixes separate when they have separate causes.
6. **Make each emulator attempt independent.** Clear app state using a verified mechanism (not only deleting XML/screenshots or force-stopping), relaunch, verify the expected initial screen/profile and selected concept, then run the flow. If reset cannot be verified, classify the attempt as a harness failure and do not treat its app assertions as valid. Preserve each attempt's artifacts separately.
7. **Run tests in layers:** relevant backend/contract tests; Kotlin/JVM and helper tests; APK build; deployed API/data checks when relevant; clean emulator end-to-end flow; visual/log evidence review. Report every layer separately.
8. **Verify user-visible behavior.** Build success is only “Built”; passing isolated tests is only “Tested”; use “Verified” only after all Phase 1 acceptance criteria pass on the target emulator and evidence has been inspected.
9. **Close or continue.** If any required check fails or remains unverified, keep Phase 1 open, document root cause and next diagnostic action, and repeat this loop. Do not merge the PR or begin Phase 2 until Phase 1 is verified.
10. **Prevent drift.** Keep one active objective and explicit acceptance criteria. Add unrelated discoveries to a backlog unless they block the objective or threaten security/data integrity. At handoff, record the active phase, exact commit, passed/failed/unverified checks, evidence links, and one next action.

### Current Phase 1 blocking investigation

- Previous hosted-audio asynchronous preparation change built successfully, but the emulator still did not expose a usable Pause/Resume control. Do not assume that change fixed playback.
- A retry showed stale lesson state and missing student feedback controls; the harness reset screenshots and force-stopped the app, but did not prove a clean app state before retry.
- Captured evidence also showed a lesson-planner/segment error while the selected concept was “All 1s”, alongside a square-number visual. Treat the exact on-screen error and concept/visual mismatch as evidence to inspect, not as proof of a specific root cause.
- Current working branch: `fix/tutor-phase1-layout-state`; draft PR #7 must remain unmerged until Phase 1 acceptance passes.
