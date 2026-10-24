# PadippuPal Project Status

> Working source of truth for the active implementation batch. Keep this concise and update it at meaningful milestones. CI results must always be checked against the exact commit SHA shown in the run.

## Active objective

**Finish and verify the live tutor experience** in PR #13: [Fix live tutor layout and concept-matched animation](https://github.com/Prav1525/Padippupal/pull/13).

Do not add unrelated features to this batch. Do not merge until the PR's acceptance criteria and required regression checks pass.

## Batch checklist

| Task / acceptance area | Status | Evidence / next action |
|---|---|---|
| Compact tutor header and typography | Implemented; visual verification pending | Confirm on fresh emulator screenshot |
| Checkpoint spacing and transcript readability | Implemented; visual verification pending | Inspect checkpoint screenshot; ensure no giant blank gap |
| Bounded live lesson layout and scroll behavior | In PR; emulator verification pending | Confirm lesson fits and scrolls correctly |
| Concept-matched repeated-ones animation | In PR; emulator verification pending | Confirm no square-number animation for All 1s |
| Pre-teaching selection/navigation | Not yet confirmed | Check PR acceptance coverage and emulator flow |
| Speech/highlight timing synchronization | Not yet confirmed | Verify highlight begins with speech, not before it |
| Pause/resume/stop/back and student input | Not yet confirmed | Exercise controls in live lesson and checkpoint states |
| English and Tamil tutor experience | Not yet confirmed | Verify supported language paths and screenshots |
| Testing-error log and regression checklist | Updated previously; review before each new test run | Read `docs/TESTING_ERRORS.md` and `.github/testing-regression-checklist.md` |
| Final screenshot review and release decision | Blocked pending UI smoke artifacts | Inspect evidence from the exact latest tested commit |

## Latest known CI snapshot

Last confirmed run set for commit `761ac3f51a3342b9586c2938c3c4f606f52884e3`:

- Curriculum Engine Tests: **Passed** — [run](https://github.com/Prav1525/Padippupal/actions/runs/40044521753)
- Android APK: **Passed** — [run](https://github.com/Prav1525/Padippupal/actions/runs/40044521754)
- Android UI smoke test: **In progress at last check** — [run](https://github.com/Prav1525/Padippupal/actions/runs/40044521755)
- Screenshot artifacts: **Not available at last check**
- PR #13: **Open, unmerged**

This is a historical snapshot, not a live dashboard. After any new commit, re-check the workflows for the new head SHA. Never assume an earlier SHA's passing checks verify a later commit.

## Batch workflow

1. Keep one active objective per PR and normally plan **5–10 related tasks** per batch. Treat this as a target, not a quota; do not bundle unrelated work.
2. Define observable acceptance criteria before implementation.
3. Read this guide, `docs/TESTING_ERRORS.md`, and `.github/testing-regression-checklist.md` before starting each test run.
4. Implement the coherent batch and regression coverage before running the planned full verification cycle.
5. Review the complete diff, then run the appropriate tests, build, emulator flow, and screenshot inspection.
6. If a test fails, capture evidence, identify the root cause, record meaningful incidents, fix it, and rerun the affected checks. Do not weaken tests to make a build green.
7. Report each layer as **Implemented**, **Built**, **Tested**, or **Verified** accurately. Passing CI alone is not visual acceptance.
8. Keep this file current at meaningful milestones; link to CI evidence and identify the exact commit.

## Automation expectations

GitHub Actions already runs the configured CI workflow steps automatically after relevant pushes/PR updates; the UI smoke workflow includes JVM tests, APK build, script checks, emulator navigation, and artifact upload in one job. Use those workflows rather than asking the user to manually start each test.

CI does **not** automatically mean an assistant is awake to inspect the results, fix failures, or start the next implementation batch. Until a persistent agent/runner is explicitly configured and verified, do not promise unattended coding or autonomous recovery. When working in an active session, poll the existing run, inspect logs/artifacts, fix issues, and continue through the planned verification cycle without asking the user for a new command at each step.

## Current verification snapshot — 2026-10-24

- Branch head at the start of this verification pass: `946df6259940ddcf717bfe91366e3326a2298a2a`.
- Curriculum Engine Tests: **Passed** on that SHA.
- Android APK: **Passed** on that SHA.
- Android UI smoke: **Failed before emulator launch** because an existing helper assertion still expected the superseded checkpoint-only height rule; see TE-038 in `docs/TESTING_ERRORS.md`.
- Corrective harness changes: update the obsolete assertion and extend the smoke flow to capture the **completed topic** screen from the exact tested APK, including the retained transcript and lower viewport.
- Latest fixes to scripts/docs are committed separately after the above SHA; re-check all workflows against the new head before declaring any screenshot verified.
- PR #13 remains **open and unmerged**.

## Next action

Poll the current UI smoke run; once complete, inspect its logs and screenshot artifacts against the checklist. If the run failed, diagnose and fix the root cause. Keep PR #13 unmerged until all required acceptance criteria are verified.


## Speech-highlight detector correction — 2026-10-24

- **Objective:** Resolve the latest UI smoke failure without weakening the speech/highlight acceptance gate.
- **Finding:** Artifact `12541317032` from run [40045309104](https://github.com/Prav1525/Padippupal/actions/runs/40045309104) contains a visible mint word highlight in `frame-10.png`. The smoke detector was still searching for the retired blue value `#DCE7FF`, while `WordByWordCaption` uses `#CDE9E2`.
- **Implemented on tutor branch:** Updated `.github/scripts/ui_smoke.py` to scan the actual mint highlight; added a helper regression test that compares the detector color with the production caption color. Commits: `2ea7f0e4c06ae397973eb8bd7786406152d121c0`, `bc4a2fb5aeb7dc16a8154adbf2c796a3278ad5e3`.
- **Verification:** Not yet run on these commits. The prior run's APK build and JVM/helper preflight passed, but its final pixel scan failed due to the stale detector color. The corrected detector, new regression assertion, emulator progression, and fresh screenshots must pass on the latest head before the tutor PR is accepted.
- **Next:** Inspect latest-head workflow results and review live-lesson/checkpoint screenshots. Keep PR #13 open and unmerged.


## Checkpoint tile detector and repeated-ones progression — 2026-10-24

- **Objective:** Fix the actual latest-head emulator failure without weakening visual acceptance.
- **Failure evidence:** UI smoke run [40047675587](https://github.com/Prav1525/Padippupal/actions/runs/40047675587), SHA `eb4a8baef93038395e360ae127a08d332c469c0e`. The word-highlight scan passed (100 frames, 14 distinct positions); the checkpoint screenshot detector failed with 0 tile pixels because it still searched for retired blue `#DCE7FF`.
- **Implementation in this batch:** Change the checkpoint tile detector to production mint `#CDE9E2` while preserving the 350-pixel threshold; advance the repeated-ones animation through five stages so all five tiles can highlight; add regression tests for both.
- **Verification:** Pending automatic GitHub Actions on the new exact head. Inspect the live lesson and checkpoint screenshots before marking visually verified.
- **Release:** PR #13 remains open and unmerged.


## Screenshot review and checkpoint spacing follow-up — 2026-10-24

- **Finding:** Inspected fresh emulator screenshots from artifact [12543432314](https://github.com/Prav1525/Padippupal/actions/runs/40050844427/artifacts/12543432314), exact SHA `25f601b330990e0185d45595a60868536654426e`. Both live lesson and checkpoint show a large unused vertical region; the checkpoint controls remain visible above system navigation, but the content is not balanced through the viewport.
- **Root cause:** The minimum-height modifier was applied outside `verticalScroll`, so it did not make the scroll content occupy the viewport. The existing helper test checked presence rather than modifier ordering and the screenshot assertions did not detect the vertical gap.
- **Fix in this batch:** Move the min-height constraint inside the scroll content and distribute short content evenly only at the understanding checkpoint; keep the speaking transcript top-aligned with compact spacing.
- **Verification:** Pending new exact-head CI and screenshot inspection. Do not mark Phase 1 visually verified or merge PR #13 until fresh screenshots confirm the correction.
