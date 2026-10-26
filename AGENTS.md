# Repository work entry point

This file is the mandatory starting point for every coding, testing, debugging, review, or release task in this repository. It coordinates existing project guidance; it does not replace or silently override it.

## Required start-of-work sequence

1. Read this file and inspect the current branch, working tree/PR, latest commit, and relevant CI status before proposing or editing code.
2. Read `.github/testing-regression-checklist.md` for tutor/UI/test work.
3. Read `docs/TESTING_ERRORS.md` before every test run. Search it for incidents touching the changed behavior, harness, API, emulator, or workflow.
4. Read `docs/TUTOR_RELEASE_ACCEPTANCE.md` for tutor or release-facing changes. Read the relevant domain/design docs and implementation before editing.
5. Inspect the latest failing run and artifacts/logs before changing a previously failing area. Separate confirmed evidence from hypotheses.
6. Write down one active objective, scope, acceptance criteria, affected layers, and the exact checks to run. Do not start unrelated work while it is active.

## Execution rules

- Trace the full path from input/data through backend/API, Android state/UI, and the observable user outcome when relevant.
- Diagnose the cause before changing code. Do not repeat a previously failed approach without new evidence.
- Add or strengthen a focused regression test for the proven cause. Do not weaken/delete a valid assertion, skip a failing step, or treat a build-only pass as end-to-end success.
- Run cheap deterministic checks before expensive emulator/integration checks. Use bounded waits and preserve diagnostics.
- After a failure, keep the same objective active: capture the exact failing step, run/commit, logs and screenshots; classify app, test harness, data/API, emulator/ADB, or timing; fix the cause; run the focused regression and neighboring checks; then rerun the end-to-end check.
- If required evidence is unavailable, say what is blocked and do not claim the behavior is verified.
- Keep status labels distinct: **Implemented** means code changed; **Tested** means specified tests ran and their results are known; **Verified** means all relevant acceptance criteria passed on the same commit; **Blocked** means evidence or a required dependency is missing.
- Update `docs/TESTING_ERRORS.md` with meaningful newly discovered mistakes and their evidence. Update the applicable acceptance/failure records with exact commit and workflow-run links; do not erase unresolved incidents.
- Before handoff, report the active objective, changed files/commit, checks and outcomes, unresolved risks, and the single next step.

## Release and pull-request safety

- A green build is not a release pass. Follow the acceptance checklist for the changed feature and inspect the actual end-to-end evidence.
- Never merge while required checks or acceptance criteria fail or remain unverified.
- Do not merge process/automation PRs or unrelated PRs without explicit user approval. Keep separate concerns in separate PRs.
- Before any merge, confirm the intended PR, current head SHA, required checks, review state, and scope have not changed.

## Existing guidance (read the source; do not duplicate it here)

- `.github/testing-regression-checklist.md` — regression checklist, test order, working agreement, and active tutor acceptance criteria.
- `docs/TESTING_ERRORS.md` — durable incident log; mandatory before every test run.
- `docs/TUTOR_RELEASE_ACCEPTANCE.md` — tutor release acceptance criteria.

If a referenced file is missing on the checked-out branch, do not assume its contents or silently substitute a stale copy. Report the discrepancy and locate the correct branch/version first.

## Start-of-task note

Before making changes, briefly record internally or in the PR/task notes:
- Objective and acceptance criteria
- Guides and relevant prior incidents reviewed
- Current head SHA and failing/passing checks
- Planned change and regression test
- Verification required to call the work complete
