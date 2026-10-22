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
- Latest code head at this handoff: `e64de303148761c57e8be638afdadfa57baf8062`.
- Changes: topic-relevance filtering for retrieved passages; retrieval query built from selected topic/chapter rather than the long teacher-instruction prompt; increase retrieval candidate limit to 10 before filtering; All 1s semantic guard against the known counting-up/down and square-number drift; one retry for semantically off-topic generated segments; regression coverage for unrelated retrieval and generated drift.
- Fresh verification: the earlier head `c46f24faf759727f86d0e09db89b85c99d547dcd` had Curriculum Engine Tests **PASS** (run [39724140252](https://github.com/Prav1525/Padippupal/actions/runs/39724140252)) and Android APK build **PASS** (run [39724140247](https://github.com/Prav1525/Padippupal/actions/runs/39724140247)). These are not current-head verification. On latest head `e64de303148761c57e8be638afdadfa57baf8062`, Curriculum Engine Tests are **IN PROGRESS** (run [39724371618](https://github.com/Prav1525/Padippupal/actions/runs/39724371618)), Android APK build **IN PROGRESS** (run [39724371654](https://github.com/Prav1525/Padippupal/actions/runs/39724371654)), and Android UI smoke **IN PROGRESS** (run [39724371689](https://github.com/Prav1525/Padippupal/actions/runs/39724371689)).
- Historical baseline: UI smoke run [39716143925](https://github.com/Prav1525/Padippupal/actions/runs/39716143925) failed because All 1s narration/visual action drifted to counting-up/down content. Do not report it as a current run.
- Remaining acceptance: review fresh APK/UI smoke results and screenshots; verify correct All 1s lesson reaches the checkpoint and advances only after student response; review final diff; update this handoff with final exact-SHA results.
- Blockers: no local repository clone is possible in the current execution environment because outbound DNS/network access to GitHub is unavailable; GitHub Actions is the available build/emulator test environment. Render service `padippupal-curriculum-api` auto-deploys from `main` only, preview deployments are disabled, and the current live deploy is commit `22270b5333a5c692b0a1d6206eb86f4fc4ed4e48`. Therefore the existing emulator smoke workflow calls the deployed backend, not the backend code on this PR branch. Do not merge or deploy the branch without explicit user approval; report this end-to-end verification gap honestly.
- Next single action: inspect the running APK and emulator workflows, then diagnose any new failure before another patch.

## Verification refresh — 2026-10-22

- Code head checked: `e64de303148761c57e8be638afdadfa57baf8062` on PR #13.
- Curriculum Engine Tests: **PASS**, run https://github.com/Prav1525/Padippupal/actions/runs/39724371618.
- Android APK build: **PASS**, run https://github.com/Prav1525/Padippupal/actions/runs/39724371654.
- Android UI smoke: **FAIL**, run https://github.com/Prav1525/Padippupal/actions/runs/39724371689. Home, ready screen, chapter/topic selection, teaching viewport and passive All 1s animation assertions passed. Failure: across 35 captured frames, the inline highlight appeared at only one distinct position; the test requires it to move across at least two words. The displayed opening sentence is still generic for All 1s and needs topic-specific content validation.
- Live backend limitation remains: Render deploys from `main`, not this PR branch, so emulator smoke cannot validate the branch's backend changes end-to-end until an approved deployment path exists.
- Next single action: trace Android TTS range callbacks, fallback timing, Compose state and frame capture to determine why the highlight stays visually stationary; do not patch the assertion to hide the failure.


## Latest session handoff — 2026-10-22 (word-highlighting follow-up)

- Active objective: fix inline spoken-word highlighting in Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s; no unrelated scope.
- Code branch: `fix/live-lesson-coordinated-flow`; latest head `0f648fe9159a9ac856d5b780c29fbb4820b9eb16`.
- Confirmed failure evidence from prior UI smoke at `e64de303148761c57e8be638afdadfa57baf8062`: 35 captured frames, highlight detected but only one distinct position. The caption is rendered inline; the failure is movement during speech.
- Code change in commit `0f648fe9159a9ac856d5b780c29fbb4820b9eb16`: replaced the permanent `nativeWordTiming` switch with a last-native-range timestamp. Weighted elapsed/playback fallback continues running and takes over when native range callbacks stop for 900 ms; fresh native range callbacks remain authoritative. This targets Android TTS engines that emit only one initial range callback.
- Fresh verification for the new commit: Curriculum Engine Tests **PASS** ([run 39727229972](https://github.com/Prav1525/Padippupal/actions/runs/39727229972)). Android APK build **IN PROGRESS** ([run 39727230014](https://github.com/Prav1525/Padippupal/actions/runs/39727230014)). Android UI smoke **IN PROGRESS** ([run 39727230104](https://github.com/Prav1525/Padippupal/actions/runs/39727230104)). Do not claim the highlight defect fixed until the fresh UI smoke reports multiple distinct highlight positions and the remaining tutor-flow assertions pass.
- PR #13 remains open and unmerged. Do not merge or deploy without explicit approval. Render backend is still deployed from `main`; the PR branch's backend changes are not yet live, so content correctness against the changed backend remains unverified in live E2E.
- Next single action: inspect the fresh APK and emulator UI smoke results for this exact SHA; if highlighting still fails, use its captured frames/logs to diagnose before another patch.


## Failure automation follow-up — 2026-10-22

- Open PR #15: https://github.com/Prav1525/Padippupal/pull/15, branch `automation/failure-triage`, latest reviewed head `de9f137802123bd62dfe5490acad2656fcdb2550`.
- Added `.github/workflows/auto-repair.yml` alongside the read-only `failure-triage.yml`. The repair workflow is designed to collect the failed run logs at the exact SHA, ask Codex for one evidence-based fix, rerun Android unit tests/APK build and backend tests where applicable, and open a repair PR followed by dispatched CI retests. It never merges or deploys.
- Guardrails: same-repository failures only; no write token in the Codex job; no patch when no safe fix is justified; maximum two repair generations to avoid an infinite loop.
- **Not operational yet:** PR #15 is still draft/open and unmerged, so the `workflow_run` automation is not active on the default branch. Automatic code repair also requires a repository Actions secret `OPENAI_API_KEY`; the workflow skips Codex when absent. OpenAI API usage is separately billed and is not guaranteed free. No secret was added.
- Fresh workflow validation: GitHub accepted and ran the new `Bounded CI auto-repair` workflow on PR head `de9f137802123bd62dfe5490acad2656fcdb2550`; the jobs were correctly skipped for the `pull_request` event. Android APK and emulator UI smoke runs for that SHA were still in progress at the last check: https://github.com/Prav1525/Padippupal/actions/runs/39729227102 and https://github.com/Prav1525/Padippupal/actions/runs/39729227046.
- The controlled injected-failure acceptance test has **not** been run. Do not describe the full loop as complete until a failure produces a focused repair proposal and fresh retest results.
- Next action: inspect the current PR #15 CI results, then decide whether to request the required API secret/setup and run a controlled failure test. Do not merge any PR without explicit approval.


## Latest handoff — 2026-10-22 (resume tutor flow; automation parked)

- User explicitly paused the CI auto-repair automation work. PR #15 remains open/draft and unmerged; do not continue setup or spend time on that objective unless asked.
- Active objective remains Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s live tutor flow. Keep PR #13 open/unmerged; do not merge or deploy without explicit approval.
- Latest PR #13 code head: `159dc8c9902e992b53e55388303ab9f8d18d00eb` on `fix/live-lesson-coordinated-flow`.
- Fresh UI smoke failure evidence: [run 39727230104](https://github.com/Prav1525/Padippupal/actions/runs/39727230104) failed while expecting a “Choose chapter” control, but the hierarchy already showed selected `Patterns in Mathematics` and `All 1s`. A second recent smoke run on PR #14's branch similarly failed settings validation because the topic was already selected.
- Confirmed cause for this selector failure: `TutorScreen` restores same-day subject/chapter/topic from `padippupal_tutor_sessions.xml`, while the smoke setup deleted only `padippupal_profile.xml`. The test therefore was not starting from a clean tutor-selection state; this is a test-fixture isolation defect, distinct from the still-unverified inline-highlight behavior.
- Focused change committed to PR #13: smoke setup now clears both the profile and saved tutor-session preferences before seeding the CBSE Class 6 profile; a regression test asserts both files are reset before profile setup. Commits: `1172469ab8551fa72ba1fd9a12a46a8b2402df43` (smoke script), then `159dc8c9902e992b53e55388303ab9f8d18d00eb` (helper regression test).
- Verification: **UNVERIFIED** for the new commit at handoff time. The GitHub connector had not returned any workflow runs/status checks for `159dc8c9902e992b53e55388303ab9f8d18d00eb` yet. Do not infer a pass from the earlier APK/backend successes. The 35-frame inline-highlight movement requirement remains **OPEN** until fresh emulator evidence shows at least two distinct inline highlight positions during speech.
- Next single action: fetch fresh CI for `159dc8c9902e992b53e55388303ab9f8d18d00eb`; inspect the next smoke result first, then continue the All 1s live-highlight diagnosis only after the selector flow passes.
