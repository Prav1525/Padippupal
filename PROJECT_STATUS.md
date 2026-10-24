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

## Next action

Poll the current UI smoke run; once complete, inspect its logs and screenshot artifacts against the checklist. If the run failed, diagnose and fix the root cause. Keep PR #13 unmerged until all required acceptance criteria are verified.


## CI automation implementation batch

- **Objective:** Add mandatory guide review, enforce status/error-record updates, and automate CI result recording plus bounded AI repair proposals.
- **Branch:** `automation/padippupal-autofix-loop`
- **Implementation status:** Files committed on the automation branch; review and workflow execution are still pending.
- **Added:** `AGENTS.md`, `.github/pull_request_template.md`, `.github/workflows/change-governance.yml`, `.github/workflows/failure-triage.yml`, `.github/workflows/ai-autofix-main.yml`, and `docs/CI_AUTOMATION.md`.
- **Recordkeeping behavior:** Completed configured CI runs get a structured Actions summary with run URL, exact SHA, result, job outcomes, and timestamp. Failed runs get a durable GitHub issue. The fix/handoff PR must update PROJECT_STATUS.md and docs/TESTING_ERRORS.md. The triage workflow deliberately does not commit after tests, because that would invalidate the tested SHA.
- **AI repair boundary:** The optional Codex repair worker is limited to failures on trusted main; it requires the repository secret OPENAI_API_KEY and creates a separate PR. It does not merge, deploy, or publish. PR/fork failures are recorded without exposing the API key.
- **Verification:** No CI run of the newly added workflows has completed in this batch. YAML/workflow behavior is **not yet verified**. The automation PR is draft. After the workflow files are incorporated into the base branch, inspect workflow runs and fix any failures.
- **Next action:** Review the full diff, validate workflow syntax and event/permission behavior, then inspect GitHub Actions evidence. Do not merge the automation PR without explicit user approval.

## Free-first AutoPilot implementation batch — 2026-10-24

- **Objective:** Build hybrid GitHub Actions + optional free local model workflow, with only predefined deterministic triage and human review for every code change.
- **Branch:** `automation/padippupal-autofix-loop` (automation PR #18; tutor PR #13 remains separate and unmerged).
- **Implemented:** Updated `AGENTS.md`; added `tools/padippupal_autopilot.py` with dynamic guide readability check, deterministic log classification, and optional Ollama local-model advisory; added `.github/workflows/autopilot.yml`; updated `docs/CI_AUTOMATION.md`.
- **Safety:** No model-generated code is applied. No API key is required for local Ollama review. The workflow does not mutate the tested SHA, merge, deploy, or publish.
- **Guide inventory:** Reviewed README, project status, testing error log, regression checklist, all discovered `docs/*.md` guide paths, and relevant existing workflow files. Some large guide contents were not fully re-read before the initial edits; that process gap is recorded as TE-034 and must be corrected by reviewing full guide contents before the next code batch.
- **Verification:** No tests or newly added workflow runs have been executed/observed in this batch. Python syntax, workflow validity, end-to-end CI event behavior, and Ollama connectivity are **Unverified**.
- **Next:** Review the full guide documents and full diff; run the AutoPilot guide check and Python syntax/classifier tests; inspect the resulting GitHub Actions run on the exact head SHA. Keep this PR draft and do not merge without explicit user approval.
