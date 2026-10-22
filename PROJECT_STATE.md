# PadippuPal Project State

> **Living handoff document.** Update this file whenever the active objective changes, a meaningful implementation/test result is obtained, or a task is blocked. Distinguish verified facts from historical snapshots.

## Product identity and stable constraints

- Repository: `Prav1525/Padippupal`
- Platform: Android Kotlin/Jetpack Compose; FastAPI backend; Neon PostgreSQL; Gemini; Render; GitHub Actions.
- Product: PadippuPal, a curriculum-grounded tutor for Classes 6–10, CBSE and Tamil Nadu State Board.
- Student profile includes name, class/standard, medium, and board; app language choices include English and Tanglish.
- Learning content must be grounded in the app's approved curriculum/library. Do not silently substitute web content or unrelated chapter content when a matching approved source is missing.
- Tutor experience: short teacher-like segments; topic overview and key concepts first; relevant live concept animation; inline spoken-word highlighting; natural pacing; a clear understand/re-explain/question pause loop.
- User expects the assistant to perform repository/build/test work without requiring the user to code locally.
- Follow `DEVELOPMENT_PROTOCOL.md` for every change.

## Current objective at the time this file was created

**Do not resume feature coding until the development protocol and handoff process are established.** The immediate process task is to make the protocol and regression records durable in the repository. After this process task, resume the existing open tutor-flow task rather than starting unrelated features.

## Known active engineering work — revalidate before acting

- Open PR #13: https://github.com/Prav1525/Padippupal/pull/13
- Branch: `fix/live-lesson-coordinated-flow`
- Latest failure evidence previously recorded against commit `51c681a237da0497aa328e2a9e7285c3035d62fe`:
  - Android APK build run `39716143962`: PASS at that time.
  - Curriculum engine tests run `39716143930`: PASS at that time.
  - Android UI smoke run `39716143925`: FAIL at that time.
  - UI smoke evidence showed an All 1s lesson displaying an unrelated counting-up/down explanation and visual action `1 + 2 + 1 = 4`, while the animation showed five repeated 1s. This is a product/content-coordination failure, not merely a test-label issue.
- These results are a **historical snapshot**, not a claim about current CI. On every new session, inspect the PR head and fetch fresh workflow results before reporting status.
- Prior patches attempted to address caption initialization and chapter/topic picker smoke-test selectors. Those changes did not prove the content-to-animation mismatch was fixed.
- Do not declare this task complete until the runtime lesson content, speech/highlighting, visual animation, and checkpoint are all bound to the selected approved topic and the relevant end-to-end smoke test passes.

## Next task after protocol is established

1. Revalidate PR #13 head, current diff, and latest workflow runs.
2. Reproduce the exact All 1s mismatch and trace where lesson segments, visual action, animation and checkpoint content are selected.
3. Confirm the root cause from code/data/log evidence before editing.
4. Define regression tests that fail if unrelated counting-up/down or square-number content is paired with All 1s.
5. Implement a topic-bound lesson flow with fail-closed behavior when matching approved lesson content is unavailable.
6. Run backend tests, Android build, UI smoke, and relevant regression checks; report each against the exact tested commit.
7. Update this file with actual results and next action.

## Current truth rules

- Never infer a current branch/head, passing CI, merged PR, deployed backend, or generated APK from a prior chat statement. Re-fetch it.
- Keep a distinction between: planned, implemented, committed, build-passed, unit/integration-tested, emulator-verified, and released/deployed.
- Record the exact commit SHA for every verification claim.
- If unable to run a check, mark it UNVERIFIED or BLOCKED and explain why.
- If a newly discovered issue is unrelated to the current objective, add it to the backlog instead of scope-switching.

## Session handoff template

Update this section at the end of each work session:

- Date/time:
- Active objective:
- Branch / head SHA:
- Changes made:
- Tests run and results (with commit SHA and links):
- Open failures / root-cause confidence:
- Blockers:
- Next single action:


## Process protocol implementation status

- Protocol documents created on branch `process/development-protocol`.
- Pull request: https://github.com/Prav1525/Padippupal/pull/14
- PR state at handoff: OPEN, not merged. Do not assume the protocol is on `main` until merge is verified.
- This process-only PR changes no app code and does not resolve the open tutor-flow defect in PR #13.
- Next process action: review and merge PR #14; then confirm the four documents are present on `main`. In each future chat, read the protocol/state files and fetch fresh CI before any feature changes.
