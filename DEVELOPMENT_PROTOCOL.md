# PadippuPal Development Protocol

**Status:** Mandatory engineering process. Applies to every task, branch, chat, and handoff.
**Authority:** This file defines how work is performed. `PROJECT_STATE.md` defines the current verified state. The regression checklist defines required repeatable checks. The decision log records durable product/architecture decisions.

**Quick enforcement checklist:** Before each task, use [`docs/ENGINEERING_BEHAVIOR_CHECKLIST.md`](docs/ENGINEERING_BEHAVIOR_CHECKLIST.md). It is a short mandatory checklist, not a replacement for this full protocol.

## Non-negotiable rules

1. **Read before acting.** At the start of every work session, read this file and `PROJECT_STATE.md`; inspect the actual repository branch/head, open PRs, and latest relevant CI results. Do not rely on chat summaries as proof.
2. **One active objective.** Work on the current objective until its acceptance criteria pass or a documented blocker is established. Log unrelated discoveries instead of scope-switching.
3. **Evidence before diagnosis.** Reproduce failures where possible. Inspect logs, code, data contracts, and the relevant execution path. Mark hypotheses as hypotheses; never present an unverified guess as root cause.
4. **Plan before patch.** Record expected behavior, actual behavior, confirmed cause (or what remains unknown), fix approach, affected components, acceptance criteria, and regression risks before editing.
5. **Fix the cause, not the signal.** Never weaken assertions, skip tests, mask errors, accept unexpected states, or alter expected behavior merely to make CI green. Change a test only when its requirement is demonstrably wrong, and document why.
6. **Preserve working behavior.** Inspect shared dependencies and neighboring flows. Make a focused, complete change; avoid unrelated refactors. Add regression coverage for every confirmed recurring defect.
7. **Use explicit verification levels.** A commit is not a passing build; a passing build is not a passing test suite; passing unit tests are not proof of correct UI behavior. Report each result separately with links/logs where available.
8. **No unsupported completion claims.** Mark checks PASS only with fresh evidence tied to a specific commit. Mark unrun checks UNVERIFIED and failed checks FAIL/BLOCKED. Never claim a device test occurred if only CI or code inspection was performed.
9. **Failure means return to diagnosis.** If a fix or test fails, capture the new evidence and revisit the causal model. Do not stack speculative patches on the same symptom.
10. **No silent scope changes.** Interrupt the objective only if blocked, unsafe, or based on disproven assumptions. Record other issues in the backlog/state.
11. **Keep the handoff durable.** Update `PROJECT_STATE.md`, regression coverage, and decision records as applicable before declaring the task complete. Commit documentation with the code it describes where practical.
12. **Be transparent about access.** If a runner, emulator, secret, repository, or environment is inaccessible, state exactly what was and was not verified.

## Mandatory testing-error prevention gate

Before **every** test run (local, CI-triggered, emulator, smoke, or release verification):

1. Read `docs/TESTING_ERROR_LOG.md` and `.github/testing-regression-checklist.md`.
2. Identify prior failures that touch the files, components, data path, test harness, or behavior under test.
3. Convert each relevant past mistake into a pre-run check: a regression test, an explicit assertion, a fixture/setup check, a timeout/diagnostic, or a manual verification step. Confirm the safeguard is present and applicable before starting the run.
4. Check the planned test command, environment, branch, and exact commit SHA. Do not start a test against a stale or unintended head.
5. After every failure or newly discovered mistake, record it in `docs/TESTING_ERROR_LOG.md` **before rerunning**. Include the evidence, root cause or confidence level, correction, prevention rule, and regression coverage. If root cause is unknown, say so; do not invent one.
6. After a fix, rerun the failed test and the relevant regression set. Inspect the result and ensure the run tested the new exact commit. A prior green run is not proof for a new commit.
7. Never erase an entry because the bug is fixed. Mark its status and keep the prevention lesson permanently useful.

**No repeat without learning:** do not rerun a failed test unchanged unless the purpose is to reproduce/confirm the diagnosis, and label it as a reproduction. Before that reproduction, explain what evidence it is intended to collect. Every other rerun must include a meaningful code, test, setup, or diagnosis change.

## Required task record

Before implementation, record:

- Objective and explicit non-goals
- Reproduction steps and observed evidence
- Expected versus actual behavior
- Root cause and evidence, or unresolved hypotheses
- Proposed fix and affected files/data paths
- Acceptance criteria (observable, binary pass/fail)
- Regression checks and risks

If information is missing, investigate first. Ask the user only when a product-level decision is genuinely needed.

## Required workflow gates

1. **Orient:** read protocol/state; inspect repo, branch, diff, PR, and relevant CI.
2. **Define:** state one objective and its boundaries.
3. **Baseline:** establish current failures and existing passing behavior.
4. **Diagnose:** reproduce and trace the actual path across UI/API/database/config/tests as relevant.
5. **Plan:** choose the smallest complete root-cause fix; define acceptance tests before coding.
6. **Implement:** work on the intended branch; keep the diff focused.
7. **Verify:** run targeted tests, relevant regression tests, build, and real user-flow/emulator tests when required.
8. **Review:** inspect the final diff and test quality; ensure tests check behavior, not just labels or implementation details.
9. **Record:** update project state and regression/decision logs; link the commit and evidence.
10. **Close or block:** close only when required gates pass. Otherwise leave the task open with exact failure and next diagnostic step.

## Verification labels

- **PASS:** fresh check succeeded on the stated commit.
- **FAIL:** check ran and failed; include the failure.
- **UNVERIFIED:** check was not run or evidence is insufficient.
- **BLOCKED:** cannot run reliably due to a named external/environmental blocker.
- **ROOT CAUSE CONFIRMED:** supported by direct code/log/reproduction evidence.
- **ROOT CAUSE HYPOTHESIS:** plausible but not yet proven.

Do not convert UNVERIFIED or BLOCKED into PASS by inference.

## Status report format

When asked for status, report:
1. Current objective and scope
2. Current branch and exact head commit
3. Last verified commit and fresh CI/build/test results
4. What changed since the previous report
5. Open failures and root-cause confidence
6. Next concrete action
7. Completion estimate only if evidence supports one

If no code or test has changed, say so explicitly. Never repeat a prior successful result as if it were fresh.

## New-chat / handoff startup checklist

Before answering a project-status or development request in a new chat:

- Read `DEVELOPMENT_PROTOCOL.md` and `PROJECT_STATE.md` from the repository.
- Read `docs/ENGINEERING_BEHAVIOR_CHECKLIST.md`, `docs/REGRESSION_CHECKLIST.md`, and `docs/DECISION_LOG.md`.
- Inspect the active PR/branch and latest commits; do not assume the last discussed branch is still active.
- Fetch the latest relevant workflow runs and their commit SHAs.
- Reconcile chat memory with repository evidence. Repository state wins for code/CI; explicit user decisions in the decision log win for settled product choices unless the user changes them.
- Identify the single active objective and its next action.
- If state is stale or contradictory, fix the state record before making code changes.
- Do not ask the user to repeat information that can be recovered from repository records or available context.

## Scope of authority

This protocol authorizes routine engineering decisions within agreed product requirements. It does not authorize silently changing product direction, paid infrastructure, privacy/security posture, or user-visible requirements. Such decisions require discussion.

## Definition of done

A task is done only when its acceptance criteria pass, required regression checks pass, build succeeds, required end-to-end flow is verified, the final diff is reviewed, and durable records are updated. Any unrun required check means the task is not fully verified.
