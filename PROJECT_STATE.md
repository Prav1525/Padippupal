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
- Follow `DEVELOPMENT_PROTOCOL.md` and `docs/ENGINEERING_BEHAVIOR_CHECKLIST.md` for every change.

## Current active objective

**Finish the existing Class 6 CBSE Mathematics live-tutor flow for Patterns in Mathematics → All 1s.** Do not start unrelated features.

The development protocol and handoff documents now exist on branch `process/development-protocol` in open PR #14, but that PR is not merged. The tutor-flow fix remains in open PR #13. Keep both PRs unmerged unless the user explicitly approves a merge.

Current investigation found a confirmed content-coordination failure: the emulator reached the selected All 1s topic and displayed the repeated-ones animation and moving inline highlight, but a later segment spoke about counting numbers up and then down and exposed `1 + 2 + 1 = 4`. The database contains the approved textbook chapter chunks, including the All 1s sequence on page 3, but has no approved `chapter_lessons` row for Class 6 CBSE Mathematics → Patterns in Mathematics at the time checked. Retrieval can therefore mix adjacent chapter concepts.

The fix is being made on `fix/live-lesson-coordinated-flow`: filter retrieved passages for the selected topic, reject known All 1s cross-topic speech/visual output, retry one semantically off-topic Gemini response once, and fail closed if the second response is still unrelated. Do not treat fail-closed behavior alone as full completion; the end-to-end flow must still teach the correct concept when matching approved source passages exist.

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
- PR state at last refresh: OPEN, not merged. Do not assume the protocol is on `main` until merge is verified.
- The process-only PR changes no app code and does not resolve the open tutor-flow defect in PR #13.
- The engineering behavior checklist is now included in this PR as `docs/ENGINEERING_BEHAVIOR_CHECKLIST.md`; the protocol and CI guard reference it.
- Next process action: refresh CI on the latest PR head and review PR #14. Do not merge without explicit user approval. After merge, confirm the files are present on `main` and resume PR #13.

## Persistent-context safeguards

- New-chat recovery prompt: `.github/NEW_CHAT_STARTER.md`.
- Automated record/PR-metadata check: `.github/scripts/check_project_process.py`, run by `.github/workflows/project-process-guard.yml`.
- Process PR: https://github.com/Prav1525/Padippupal/pull/14.
- The guard validates required documents/sections and PR description headings. It does **not** prove that an assistant read them, does not guarantee perfect compliance, and does not replace product tests. New chats still need the starter prompt or explicit startup instruction.
- Older head SHAs and workflow results in prior snapshots are historical; always fetch the current PR head and CI before relying on them.

## Latest session handoff — 2026-10-22

- Active objective: repair topic-to-lesson grounding for Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s.
- Active code branch: `fix/live-lesson-coordinated-flow`.
- Latest code head at this handoff: `c46f24faf759727f86d0e09db89b85c99d547dcd`.
- Changes: topic-relevance filtering for retrieved passages; All 1s semantic guard against the known counting-up/down and square-number drift; one retry for semantically off-topic generated segments; regression coverage for unrelated retrieval and generated drift.
- Fresh verification at this point: Curriculum Engine Tests **PASS** on the latest head (workflow run [39724140252](https://github.com/Prav1525/Padippupal/actions/runs/39724140252)); Android APK build **IN PROGRESS** (run [39724140247](https://github.com/Prav1525/Padippupal/actions/runs/39724140247)); Android UI smoke **IN PROGRESS** (run [39724140297](https://github.com/Prav1525/Padippupal/actions/runs/39724140297)).
- Historical baseline: UI smoke run [39716143925](https://github.com/Prav1525/Padippupal/actions/runs/39716143925) failed because All 1s narration/visual action drifted to counting-up/down content. Do not report it as a current run.
- Remaining acceptance: review fresh APK/UI smoke results and screenshots; verify correct All 1s lesson reaches the checkpoint and advances only after student response; review final diff; update this handoff with final exact-SHA results.
- Blockers: no local repository clone is possible in the current execution environment because outbound DNS/network access to GitHub is unavailable; GitHub Actions is the available build/emulator test environment.
- Next single action: inspect the running APK and emulator workflows, then diagnose any new failure before another patch.
