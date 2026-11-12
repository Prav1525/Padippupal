# Active work handoff

**Last updated:** 2026-11-12
**Rule:** Live GitHub evidence supersedes historical notes. One canonical trigger and one shared state; no parallel agents or ledgers.

## Repair generation state

This block is the durable, machine-readable repair counter for the active work handoff. Keep exactly one block. Carry it forward across commits/branches for the same failure chain; do not reset an open chain.

<!-- padippupal-repair-state:start -->
{"schema_version":1,"max_generations":5,"chains":[]}
<!-- padippupal-repair-state:end -->

## Local Termux listener end-to-end smoke — current objective

- **State:** IN PROGRESS — draft PR [#398](https://github.com/Prav1525/Padippupal/pull/398), branch `feat/local-codex-executor`. Listener source, tests and CI integration are implemented; target-device round trip remains unverified.
- **Approval:** Founder approved the no-edit Codex smoke (2026-11-12). Ledger task: `LOCAL-CODEX-EXECUTOR-SMOKE`.
- **Purpose:** Verify that a fresh ChatGPT-originated GitHub `/proceed` comment is detected by the Termux listener, starts the existing Codex executor in an isolated worktree, and returns a result comment without source changes.
- **One-command setup/start:** Run `python tools/padippupal_proceed_listener.py start`. If no token is configured, it prompts for the fine-grained token with hidden input, validates read access, saves it with owner-only permissions and starts polling. Required token permissions: Issues read/write; Pull requests read.
- **Current verification:** AutoPilot run [43147137406](https://github.com/Prav1525/Padippupal/actions/runs/43147137406), job 130947484201, **PASS** on exact head `45cda9d37623833d6dc2fec1d1fdaceba879a4c7`: 15 policy tests, 13 controller tests, 14 executor tests, 7 listener tests, Python compilation, policy validation and diff check. Investigation Guidance Gate [43147137197](https://github.com/Prav1525/Padippupal/actions/runs/43147137197), job 130947477933, **PASS** on the same SHA.
- **Latest refinement:** Added the combined `start` command so token configuration and listener startup require one local command; exact-head CI for this refinement is pending.
- **Safety:** Smoke task is no-edit. No commit, push, merge, deployment, production write, release or destructive operation. Codex remains workspace-write with on-request approvals.
- **Limit:** If Termux stops or Android kills the process, local execution pauses; GitHub Actions CI remains independent.
- **Next:** Verify the latest PR head's CI, then start the listener once on Termux and post a fresh `/proceed` comment to complete the end-to-end smoke.

## Local ChatGPT-to-Termux listener implementation — code complete, runtime pending

- **Ledger task:** `LOCAL-CHAT-TERMUX-BRIDGE` is APPROVED.
- **Implementation:** `tools/padippupal_proceed_listener.py` polls the existing GitHub comment bridge, filters exact owner-authored `/proceed` comments, validates open same-repository owner-authored PRs, checks the fetched SHA, creates a detached worktree, invokes the existing executor and posts a result comment.
- **Security:** Fine-grained token stored with owner-only file permissions; token environment variables are removed from the Codex child process; comments are deduplicated and historical comments are not replayed on first launch.
- **Verification:** Listener's 7 unit tests and the existing engineering suites passed on exact head `45cda9d37623833d6dc2fec1d1fdaceba879a4c7`. The final one-command startup refinement still needs fresh CI and device testing.

## Main-push Proceed monitoring — paused work item

- **State:** PAUSED — defer this work item until the founder-approved local Codex executor objective is completed; do not run two implementation objectives in parallel.
- **Root cause:** Confirmed. The five-minute controller was only invoked for PR and manual full-cycle events. Main-push test runs were not coordinated; the `workflow_run` handler only records completed evidence.
- **Change:** Route every `main` push through the existing AutoPilot coordinator. Ensure all five existing test workflows start on every `main` push, then have the coordinator reuse only runs matching the exact push SHA. It waits up to five minutes for GitHub run discovery and refuses duplicate dispatch if a push run is missing.
- **Safety:** The deployed API smoke is read-only; APK release remains disabled. No merge, deployment, production DB write, or public release.
- **Verification target:** AutoPilot policy/tests, controller unit tests (including exact-push reuse and no-fallback dispatch), investigation gate, YAML/workflow checks, and the full coordinated five-workflow matrix on the PR SHA. Merge requires separate founder approval.

## Unified engineering agent — PR #186
- **PR:** https://github.com/Prav1525/Padippupal/pull/186
- **Branch:** `chore/closed-loop-agent-contract`
- **Latest trigger-contract correction:** `fcc8dc6086e1aa915c58157186c5d86309139793`
- **Intent:** one integrated PadippuPal engineering agent, one trigger (`Proceed`), one operating contract, one active-work handoff and one approved-work ledger.
- **Canonical responsibilities:** `AGENTS.md` owns agent behavior and authority; `TESTING_GUIDANCE.md` owns test/build-specific rules; `docs/AUTOPILOT_TRIGGER_PROMPT.md` is the only reusable trigger and delegates to those two sources; `.engineering/README.md` is an index only.
- **Redundancy removed:** condensed the trigger to one entry point; removed duplicated operating-model prose from test guidance; converted Engineering OS README to an index; deleted the redundant `docs/ENGINEERING_AUTOPILOT.md` architecture guide.
- **AutoPilot:** existing `.github/workflows/autopilot.yml` and `tools/padippupal_autopilot.py` remain the CI/policy/evidence subsystem. `tools/padippupal_proceed_controller.py` coordinates existing checks. They are components of the same cycle, not separate triggers.
- **Exact-head failure found:** AutoPilot run [41624396298](https://github.com/Prav1525/Padippupal/actions/runs/41624396298), job 125877965532, checked out exact SHA `df6e48e38b5f48dfe35cb79fe9b340392a543c44` and failed because its drift validator expected five legacy phrases absent from the shortened trigger. This is a validator/contract wording mismatch, not a product or runtime failure.
- **Targeted correction:** added a concise “Same-invocation operating contract” section to the sole trigger with the required Engineering OS, AutoPilot and shared-state markers. Commit `fcc8dc6086e1aa915c58157186c5d86309139793`. No test assertions were weakened.
- **Other checks on prior exact SHA `df6e48e...`:** Investigation Guidance Gate run 41624396320 PASS; Android APK run 41624396290 was IN PROGRESS; Android UI smoke run 41624396302 was PENDING. These do not verify the corrected SHA.
- **Latest exact-head verification:** AutoPilot run [41625909732](https://github.com/Prav1525/Padippupal/actions/runs/41625909732), job 125883069158, **PASS** on `7cb0c125fba8195e66f9a03297db721a903d28a9`: policy validator PASS; 14 AutoPilot tests PASS; 8 Proceed-controller tests PASS; `py_compile` and `git diff --check` PASS. Investigation Guidance Gate run [41625910029](https://github.com/Prav1525/Padippupal/actions/runs/41625910029), job 125883069697, **PASS**. Android APK run [41625909740](https://github.com/Prav1525/Padippupal/actions/runs/41625909740), job 125883068735, **PASS**; debug APK artifact [13226125802](https://github.com/Prav1525/Padippupal/actions/runs/41625909740/artifacts/13226125802), 16,296,932 bytes, matches the same branch/SHA. Public APK release job was skipped as required.
- **UI/emulator:** **NOT RUN / NOT REQUIRED** for this workflow/controller-only change; no Android app behavior changed. This is not feature-specific tutor UI evidence.
- **Live GitHub bridge:** active on main; PR #186 is merged. The issue_comment workflow dispatches CI for an owner-authored /proceed comment. It does not itself invoke local Termux Codex; that requires the local polling listener tracked in PR #398.
- **Next:** validate the local Termux listener in PR #398. PR #186 is already merged; do not merge PR #398 without separate founder approval.
- **Chat trigger bridge:** the AutoPilot workflow on main accepts owner-authored `/proceed` comments on open same-repository owner-authored PRs and runs the CI controller. PR #186 is merged, so this GitHub-to-CI bridge is active. The local listener is a separate transport component that must be running on Termux to invoke Codex.
- **Repair-generation state:** the five-generation counter now lives in the machine-readable block above; AutoPilot validates its schema, approved task linkage, sequential numbering, and hard maximum. The agent must update this shared block for every distinct repair hypothesis and carry it across branches. CI validation does not independently infer whether a hypothesis is genuinely distinct.
- **Capability boundary:** GitHub Actions executes and observes tests; the Termux listener can invoke the already authenticated local Codex CLI while it is running. It cannot wake a stopped phone/process. No cloud model worker or paid API integration is used.
- **Safety:** no merge, production deployment, production DB mutation or public release.

## Concurrent user-requested acceptance: Beyond Earth original PDF images
- **Feature PR:** https://github.com/Prav1525/Padippupal/pull/168
- **Acceptance harness PR:** https://github.com/Prav1525/Padippupal/pull/182
- **Last known live run:** https://github.com/Prav1525/Padippupal/actions/runs/41622028202
- **Required acceptance:** retrieve and inspect the actual Beyond Earth tutor screenshot and diagnostic hierarchy; generic Mathematics smoke is not a substitute.
- **Safety:** no merge, production deployment, production DB mutation or public release.

## Historical handoff notes

## Previous Phase 1 / older visual work notes
- **PR:** [#59](https://github.com/Prav1525/Padippupal/pull/59)
- **Head at last check:** `0383b1fe9690ff3c97dcc901c64710be04ddba14`
- **Scope:** CBSE Class 6 Science, Beyond Earth; native Compose Canvas visuals; no SVG; labelled diagrams; progressive reveal; inline tutor flow.
- **Latest checks on that head:** Android APK run 40989118308 PASS; Curriculum tests run 40989118292 PASS; Investigation guidance run 40989118330 PASS; Android UI smoke run 40989118437 FAIL before emulator startup. Runtime behavior remains UNVERIFIED.
- **Next action:** inspect failing smoke-step logs, fix only the evidence-backed harness issue, rerun emulator validation and inspect screenshots/UI hierarchy for all eight stages.
- **Release boundary:** do not merge PR #59, deploy or write production DB without explicit founder approval.

## Resume checklist
- Re-fetch main and working branch heads; do not assume this handoff is current.
- Re-fetch active PR state and latest checks for its exact head SHA.
- Re-read `AGENTS.md` and `TESTING_GUIDANCE.md` before edits/tests/builds/deploys.
- For tutor/UI tests, re-read `.github/testing-regression-checklist.md` and `docs/TESTING_ERRORS.md`.
- Inspect failure logs/artifacts before retrying; do not repeat an unchanged failed approach.
- Update this file with exact evidence and one next action.
