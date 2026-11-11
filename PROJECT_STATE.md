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
- Fresh verification for `159dc8c9902e992b53e55388303ab9f8d18d00eb`: Curriculum Engine Tests **PASS** ([run 39731013253](https://github.com/Prav1525/Padippupal/actions/runs/39731013253)); Android APK build **PASS** ([run 39731013259](https://github.com/Prav1525/Padippupal/actions/runs/39731013259)); Android UI smoke **IN PROGRESS** ([run 39731013247](https://github.com/Prav1525/Padippupal/actions/runs/39731013247)). At last inspection, the smoke job was still running its fast JVM tests before emulator allocation. Do not infer a UI pass from the APK/backend successes. The 35-frame inline-highlight movement requirement remains **OPEN** until fresh emulator evidence shows at least two distinct inline highlight positions during speech.
- Next single action: fetch fresh CI for `159dc8c9902e992b53e55388303ab9f8d18d00eb`; inspect the next smoke result first, then continue the All 1s live-highlight diagnosis only after the selector flow passes.


## Latest handoff — 2026-10-22 (checkpoint continuation)

- Active objective remains Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s live tutor flow. Automation PR #15 remains parked; do not resume it unless asked. PR #13 remains open/unmerged.
- Latest code head on `fix/live-lesson-coordinated-flow`: `5051b68715ea01cd5cea9bef6550fed6aff863ee`.
- Fresh smoke failure on previous head `159dc8c9902e992b53e55388303ab9f8d18d00eb`: [UI run 39731013247](https://github.com/Prav1525/Padippupal/actions/runs/39731013247). The selected topic, repeated-ones animation, full teaching viewport, and inline highlight all passed in this run; the frame scan detected **2 distinct highlight positions across 35 frames**. Pause/resume passed. The run failed at checkpoint continuation: tapping “I understand” did not advance from segment 2/5 within 30 seconds and the checkpoint remained visible.
- Focused patch in `5051b68715ea01cd5cea9bef6550fed6aff863ee`: the “I understand” handler now captures the next segment index, clears checkpoint state synchronously, resets paused state, and posts segment progression to the main handler without the previous 350 ms delay. The suspected callback timing/state race is **not yet confirmed**; fresh emulator verification must determine whether this is sufficient.
- Fresh CI for `5051b68715ea01cd5cea9bef6550fed6aff863ee`: Android APK run [39732280733](https://github.com/Prav1525/Padippupal/actions/runs/39732280733), curriculum tests [39732280662](https://github.com/Prav1525/Padippupal/actions/runs/39732280662), and UI smoke [39732280667](https://github.com/Prav1525/Padippupal/actions/runs/39732280667) were all **IN PROGRESS** at handoff update time. Do not claim the checkpoint fix passed until the UI run finishes and verifies segment 3/5 after the answer. Highlight acceptance is provisionally met on the previous commit only; recheck on the new commit.
- Next single action: inspect all three fresh CI runs for `5051b68715ea01cd5cea9bef6550fed6aff863ee`; if checkpoint progression still fails, inspect the new event/state evidence before another patch.


## Latest handoff — 2026-10-22 (empty speech and voice fallback)

- Active objective remains Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s live tutor flow. PR #13 remains open and unmerged; no deployment or merge was performed.
- Latest PR #13 code head at this handoff: `4998d55e6f243879a0b7bdbd31b6e1af1175261b` on `fix/live-lesson-coordinated-flow`.
- New evidence from UI run [39732280667](https://github.com/Prav1525/Padippupal/actions/runs/39732280667): one attempt showed no compatible English voice, so the lesson did not reach its checkpoint. Another attempt reached the checkpoint at 2/5 but later appeared at 4/5 after “I understand”; the next-segment assertion did not observe 3/5.
- Confirmed code path: `playLiveSegment` immediately called itself with the next index when a segment had blank `spoken_text`. Backend `_validate_lesson_plan` accepted blank narration, so an unplayable segment could cause the UI to jump from 2/5 to 4/5. The backend validator now rejects empty spoken segments, using the existing one-retry path; a regression test verifies that a blank first response is retried and a valid segment is returned.
- Confirmed voice-fallback defect: when hosted speech failed and the device TTS engine lacked the selected language, `speakWithDeviceTts` called `finishSpeechSegment()`, which treated unavailable audio as completed narration and could auto-advance. Android now pauses the live lesson and retains a recovery message instead of skipping the segment. TTS utterance errors also pause the live lesson rather than silently leaving completion state unresolved.
- The UI smoke progression poll now checks every 250 ms to avoid missing the short-lived 3/5 state. This is a test observation fix, not evidence that progression has passed.
- Fresh CI for code head `4998d55e6f243879a0b7bdbd31b6e1af1175261b`: Curriculum Engine Tests **PASS** (44 passed; [run 39735164521](https://github.com/Prav1525/Padippupal/actions/runs/39735164521)); Android APK build **PASS** ([run 39735164510](https://github.com/Prav1525/Padippupal/actions/runs/39735164510)); Android UI smoke **IN PROGRESS** at handoff update time ([run 39735164537](https://github.com/Prav1525/Padippupal/actions/runs/39735164537)). The UI run has passed script validation and reached the emulator execution step, but its end-to-end result is not yet available.
- Important environment boundary: the emulator smoke APK defaults to the deployed Render API URL. Backend changes in PR #13 are not live on Render because deployment/merge was not approved. Backend unit tests verify the new validation, but end-to-end against the changed backend remains unverified until the UI run supplies evidence or a separately approved test deployment is used.
- Next single action: inspect run 39735164537 and its screenshots/logs. If it fails, identify whether the cause is current deployed API/TTS availability, a remaining segment-state bug, or stale smoke evidence before editing again.


## Live tutor voice investigation update — 2026-10-22

- Active code branch: `fix/live-lesson-coordinated-flow`; PR #13 remains open and unmerged.
- Latest code change: commit `6c711eeed23087d4caa8ab9db6fe882c8e2f4aec` broadens Android TTS locale selection to prefer installed British English, then Indian/US English, and to discover other installed locales for the selected language.
- Fresh baseline on the prior head: Android build PASS, curriculum tests PASS, UI smoke FAIL. The lesson reaches the correct All 1s content but cannot reach speech/checkpoint UI.
- **Confirmed external TTS failure from Render logs at 2026-10-22 06:43 UTC:** `POST /tutor/speech` returned 503 after Gemini TTS returned HTTP 429 and Sarvam fallback returned HTTP 402. The app then fell back to Android TTS, whose emulator image reported no compatible English voice. This is a provider quota/billing plus CI-emulator voice-availability blocker, not evidence that the checkpoint handler failed.
- The new locale-selection change is a limited compatibility improvement; it does not resolve provider quotas and must not be described as having fixed the voice failure unless fresh CI/device evidence proves it.
- CI runs for commit `6c711eeed23087d4caa8ab9db6fe882c8e2f4aec` were started: Android APK run `39736279734`, curriculum tests `39736279835`, UI smoke `39736279720`. Re-fetch final results before updating status.
- Acceptance still open: prove real speech or a valid installed-device voice, moving inline highlight, pause/resume, and checkpoint progression 2/5 → 3/5. The checkpoint fix remains UNVERIFIED until the UI reaches and passes the checkpoint.
- Next single action: inspect the three fresh CI results, then address the remaining voice blocker based on the evidence; do not change checkpoint logic again without a checkpoint-specific reproduction.


## Follow-up CI environment correction — 2026-10-22

- Latest PR #13 head: `8fe4a4b35cef0acaca18c1d6fa1c7cc83bcd9ca1`.
- In addition to installed-locale discovery, the Android UI smoke workflow now uses the Google Play Store emulator image to provide a better chance of having a usable Android TTS engine when cloud providers are unavailable.
- The smoke checkpoint poll now stops early and records the explicit voice error if neither hosted speech nor device TTS can start; it no longer waits the full 150-second checkpoint timeout in that known failure state. This is diagnostic-only and does not relax acceptance assertions.
- Fresh runs for the latest head: curriculum engine tests `39736614807` PASS; Android APK `39736614748` and Android UI smoke `39736614754` were still running at the time of this update. Re-fetch before reporting final status.
- Cloud TTS remains externally blocked at last observed backend logs: Gemini 429 and Sarvam 402. Do not modify billing/secrets or imply provider quota has been repaired. Next action: inspect latest build and emulator results; if speech still cannot start, capture the explicit reason and leave voice/checkpoint acceptance open rather than weakening tests.


## Screenshot-check performance correction — 2026-10-22

- Latest code head on PR #13: `01cbd5185a531c7c0ce220438d4603f0be8a3a92`.
- **PASS:** Android APK build `39737297227` — https://github.com/Prav1525/Padippupal/actions/runs/39737297227
- **PASS:** Curriculum engine tests `39737297178` — https://github.com/Prav1525/Padippupal/actions/runs/39737297178
- **IN PROGRESS at last check:** Android UI smoke `39737297301` — https://github.com/Prav1525/Padippupal/actions/runs/39737297301
- Screenshot inspection no longer scans every image pixel in Python; exact RGB masks and bounding boxes use Pillow operations. A synthetic-image regression test checks exact-color pixel count and bounds. The app's inline-highlight movement assertion remains required.
- Render logs still show cloud TTS failures (Gemini 429 and Sarvam 402) on the latest emulator attempt. The Play Store emulator fallback test has not yet provided a final checkpoint result. Keep speech/highlight/pause-resume/checkpoint acceptance open until the UI run finishes and its artifact is inspected.
- Next single action: fetch the final UI smoke result and inspect its failure artifact if it fails; do not claim the checkpoint fix passed without observing the 2/5 → 3/5 transition.


## Speech completion recovery follow-up — 2026-10-22

- Active objective remains the Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s live tutor journey; PR #13 remains open/unmerged.
- Latest verified failing run for prior head `01cbd5185a531c7c0ce220438d4603f0be8a3a92`: Android APK PASS (`39737297227`), curriculum tests PASS (`39737297178`), UI smoke FAIL (`39737297301`).
- UI evidence: lesson content and repeated-ones animation PASS; inline spoken-word highlight moved through 13 distinct positions; pause/resume controls PASS. After resume the lesson remained at 1/5 and did not reach the understanding checkpoint within 150 seconds. Artifact: https://github.com/Prav1525/Padippupal/actions/runs/39737297301/artifacts/12408052680
- Logcat shows a MediaPlayer/NuPlayer playback session was paused/resumed and later reset, but the UI remained on segment 1. The precise missing callback was not directly logged; treat the callback failure as a strong hypothesis, not a proven underlying Android engine defect.
- Implemented on PR #13 head `73a930a6a4be661c6413690dd387380774c67f0c`: per-utterance watchdog detects playback that was observed and then stopped without delivering the completion callback. It respects pause state, checks MediaPlayer end position to avoid treating a temporary stall as completion, and fails safely if playback never starts. Fresh curriculum tests PASS; APK build and UI smoke are pending.
- **Next single action:** inspect fresh build and full emulator results for `73a930a6a4be661c6413690dd387380774c67f0c`; require the explicit checkpoint and 2/5 → 3/5 assertion before closing the issue.


### Fresh CI update — 2026-10-22

- PR #13 head under test: `73a930a6a4be661c6413690dd387380774c67f0c`.
- **PASS:** Android APK build — https://github.com/Prav1525/Padippupal/actions/runs/39739236650
- **PASS:** Curriculum Engine Tests — https://github.com/Prav1525/Padippupal/actions/runs/39739236589
- **IN PROGRESS:** Android UI smoke — https://github.com/Prav1525/Padippupal/actions/runs/39739236756 (runner was still in Gradle setup at last poll).
- The completion-watchdog change compiles successfully. End-to-end progression remains UNVERIFIED until this UI run reaches and passes the understanding checkpoint assertion.


## Live tutor smoke assertion correction — 2026-10-22

- Active objective remains the complete Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s live lesson; PR #13 remains open and unmerged.
- New PR #13 head: `8d6e9304ed459a4efeb29b434dd72cf6eeef06b1`.
- Confirmed test-harness defect: `.github/scripts/ui_smoke.py::assert_live` required the literal text `teacher is speaking`, but the app does not render that label. Its real accessible lesson progress is `1 / 5` and the app status values are `Playing segment N of M` / `Live lesson · segment N of M`. The stale assertion caused the smoke to exit before pause/resume and checkpoint checks.
- Corrected the assertion to require actual segment progress and recognizable inline lesson content, while retaining separate highlight-motion, playback, voice-error, checkpoint, animation, and 2/5 → 3/5 checks. This is not a relaxation of acceptance criteria; it removes an assertion for UI text that does not exist.
- **PASS:** Android APK build at new head, run [39741609797](https://github.com/Prav1525/Padippupal/actions/runs/39741609797).
- **PASS:** Curriculum Engine Tests at new head, run [39741609927](https://github.com/Prav1525/Padippupal/actions/runs/39741609927).
- **IN PROGRESS at last check:** Android UI smoke run [39741609782](https://github.com/Prav1525/Padippupal/actions/runs/39741609782). The corrected test has not yet provided fresh evidence for speech/highlight completion or the understanding checkpoint.
- **Status:** The assertion defect is corrected; the live speech/checkpoint acceptance remains UNVERIFIED. Do not mark the tutor-flow issue fixed unless the smoke confirms narration/highlight movement, pause/resume, checkpoint appearance, and the 2/5 → 3/5 transition.
- Next single action: fetch the final UI smoke result and inspect its artifact/logs; if it fails after the corrected assertion, diagnose the actual playback or checkpoint failure rather than adding more speculative watchdog logic.


### Fresh successful end-to-end verification — 2026-10-22

- **Exact tested PR #13 head:** `8d6e9304ed459a4efeb29b434dd72cf6eeef06b1`.
- **PASS — Android APK:** [run 39741609797](https://github.com/Prav1525/Padippupal/actions/runs/39741609797).
- **PASS — Curriculum Engine Tests:** [run 39741609927](https://github.com/Prav1525/Padippupal/actions/runs/39741609927).
- **PASS — Android UI smoke:** [run 39741609782](https://github.com/Prav1525/Padippupal/actions/runs/39741609782), completed successfully on retry attempt 2. Artifact: [emulator screenshots and UI hierarchy](https://github.com/Prav1525/Padippupal/actions/runs/39741609782/artifacts/12409322712).
- Emulator evidence from the job log: the All 1s topic displayed its repeated-ones passive animation and approved-topic teaching text; 16 distinct inline highlight positions were detected; pause and resume controls changed state correctly; the understanding checkpoint appeared at `2 / 5`; tapping “I understand” dismissed it and advanced to `3 / 5`; Stop and Android Back returned to Home.
- The checkpoint path that previously remained at `1 / 5` now passes in this run. The original voice/provider availability issue is not fully generalized across all physical devices: this run proves the CI Play Store emulator path, not every phone's installed TTS configuration. Hosted TTS provider quota/billing remains an external concern when that service is unavailable.
- **Current status:** the targeted All 1s end-to-end acceptance passes on this commit. PR #13 remains open and unmerged. Do not claim all-device voice behavior is verified. Next action: inspect the final diff and captured screenshots for unintended changes before considering PR #13 ready for review; keep unrelated feature work out of scope.


## Current verification update — 2026-10-22 (supersedes the earlier PR #13 PASS summary)

- **Active objective:** finish review and verification of PR #13 only; do not merge PR #14 (process) or PR #15 (automation).
- **PR #13:** https://github.com/Prav1525/Padippupal/pull/13 remains OPEN and unmerged. Current branch `fix/live-lesson-coordinated-flow`, head `cdd5094c48231cdeeafc788c045691d4d37a730c`.
- **Root cause found during final review:** the All 1s validator previously accepted a lesson when *any* segment mentioned the selected topic, allowing a later generic chapter introduction to be played as an All 1s segment. The validator now checks each segment individually, and a regression test verifies that a generic later segment triggers the one allowed retry. Changes are committed on PR #13.
- **PASS — Curriculum Engine Tests** on `cdd5094c48231cdeeafc788c045691d4d37a730c`: https://github.com/Prav1525/Padippupal/actions/runs/39745719285.
- **PASS — Android APK build** on the same SHA: https://github.com/Prav1525/Padippupal/actions/runs/39745719299.
- **FAIL — Android UI smoke** on the same SHA: https://github.com/Prav1525/Padippupal/actions/runs/39745719279. Attempt 1 saw an empty chapter list; attempt 2 loaded the chapter/topic but the live lesson could not start speech because cloud TTS returned HTTP 429 and Sarvam fallback returned HTTP 402, then the emulator's selected device TTS reported no compatible English voice. The app paused safely rather than skipping speech. Render logs confirmed the provider errors at 2026-10-22T08:15:32Z. Artifact: https://github.com/Prav1525/Padippupal/actions/runs/39745719279/artifacts/12411502837.
- **Merge decision:** do not merge yet. Required UI end-to-end check is FAIL; do not weaken the assertion or claim speech/checkpoint/highlight acceptance on this head. The earlier successful smoke at SHA `8d6e9304ed459a4efeb29b434dd72cf6eeef06b1` is historical and does not override this fresh failure.
- **External/runtime limitation:** Render service `padippupal-curriculum-api` auto-deploys from `main`, not the PR branch. Therefore the emulator smoke did not exercise the new backend validator before merge. Backend unit tests cover the validator change; deployed end-to-end verification is still required after an approved merge.
- **Next single action:** resolve or explicitly classify the CI voice dependency (cloud TTS quota exhaustion plus missing English voice in the emulator), then rerun the full smoke on the latest PR #13 head. Keep PR #13 unmerged until the required UI check passes; do not merge PR #14 or #15.


## Follow-up diagnosis — Android TTS fallback (2026-10-22)

- New PR #13 head: `a67c135dde7ba4807f7bb0e2d99177c4b5a35bad`.
- Inspection of artifact `12411502837` logcat confirmed the fallback failure was not just a missing language pack: Android logged `TextToSpeech: getAvailableLanguages failed: not bound to TTS engine` and `isLanguageAvailable failed: not bound to TTS engine` at 2026-10-22 08:15:32Z.
- **Confirmed manifest defect:** `app/src/main/AndroidManifest.xml` did not declare the Android 11+ package-visibility query for `android.intent.action.TTS_SERVICE`. The TextToSpeech API requires this query for apps targeting Android 11+ to discover the system engine. The declaration is now added.
- The device fallback now waits up to 8 seconds for the asynchronous TextToSpeech engine to bind before querying available languages. On timeout it pauses safely and invalidates the speech watchdog rather than advancing without speech. Added a regression test requiring the manifest query.
- **PASS:** Curriculum Engine Tests on `a67c135dde7ba4807f7bb0e2d99177c4b5a35bad`: https://github.com/Prav1525/Padippupal/actions/runs/39747425162.
- **PASS:** Android APK build on the same SHA: https://github.com/Prav1525/Padippupal/actions/runs/39747425181.
- **IN PROGRESS:** Android UI smoke on the same SHA: https://github.com/Prav1525/Padippupal/actions/runs/39747425136.
- PR #13 remains unmerged pending the fresh smoke result. PR #14 and PR #15 remain open and must not be merged without a separate approval.


## Follow-up CI investigation — 2026-10-22

- **Current PR #13 head:** `ccf7f18519ef154791ad47f1b356ba5ca378bd0b`, still OPEN and unmerged.
- **Latest failure root cause confirmed from logs:** the Android UI smoke run at `6322d34f0af37366ec63fa008b41edbe02319182` failed before app navigation because the test-only offline TTS fixture download exited with `curl: (3) URL rejected: Bad hostname`. It was a workflow command/setup failure, not a tutor-flow assertion failure. No screenshot artifacts were uploaded from that attempt.
- **Correction:** changed the workflow fixture download to a single-line `curl --url "$TTS_URL" --output "$TTS_APK"` command on the PR branch. This is a targeted CI setup fix; checksum validation and package verification remain enabled.
- **Fresh CI on `ccf7f18519ef154791ad47f1b356ba5ca378bd0b`:** Android APK, Curriculum Engine Tests, and Android UI smoke were all `in_progress` at the last repository poll. Do not treat any as passed until the run completes.
- **Merge gate:** CLOSED pending fresh UI smoke completion and review of its artifacts/logs. Earlier run on `6322d34` did not test the lesson because setup failed.
- **Next single action:** inspect the three fresh runs for the exact current head, then diagnose any remaining smoke failure from logs/artifacts. Do not merge PR #13 until required checks pass; do not merge PR #14 or #15.
