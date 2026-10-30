# Mandatory Agent Instructions for PadippuPal

**Before every code edit, test action, build action, build/configuration change, or deployment action, read `TESTING_GUIDANCE.md` in full and follow it.** This is a per-action requirement, not a one-time setup step. If a task spans multiple edits or sessions, re-open the guidance before each new batch of edits and whenever the investigation context changes.

## Required pre-action gate
Before touching code or starting a consequential build/test/deploy action, state in working notes (and in the user update when meaningful):
1. The relevant guidance being applied, including build-specific rules when applicable.
2. The current branch and commit.
3. The exact failure/requirement and latest evidence.
4. Whether the root cause is confirmed, probable, or unknown.
5. The specific action proposed and why it is justified by the evidence.
6. The diagnostic, build, regression, and acceptance checks that will verify it.

If the latest failure evidence, build environment, or project state is not available, retrieve it first. Do not guess or restart the investigation from scratch. Before selecting a build command, verify the repository's documented setup, wrapper, versions, and available tasks.

## Required post-action gate
After any change or meaningful build/test action:
1. Record changed files, commit SHA, exact command/task/variant, and environment versions where relevant.
2. Run the narrowest relevant check, then required build/regression/acceptance checks where possible.
3. Record exact outcomes and links to logs/artifacts/screenshots/APKs.
4. Compare results with previous attempts and append to the durable investigation log.
5. Tell the user what changed, what was tested or built, what failed or remains unverified, and the next evidence-based action.

Never claim success without verification. A successful compile does not prove tests passed; a generated APK does not prove runtime behaviour. Never repeat an unchanged failed approach. Never merge a PR without the user's explicit permission.

These requirements apply to all coding agents and human contributors. `TESTING_GUIDANCE.md` is the detailed source of truth.


## Persistent engineering memory
Before starting or resuming any PadippuPal task, read:
1. `PROJECT_CHARTER.md` and `PROJECT_STATUS.md`.
2. `.engineering/README.md` and the relevant architecture/module, decision, known-issue, and acceptance records.
3. `.engineering/tasks/active-work.md` to recover the single active objective.
4. The existing mandatory guidance above and, for tutor/UI work, `.github/testing-regression-checklist.md` plus `docs/TESTING_ERRORS.md`.

Reconcile dated documentation with actual branch heads, PRs, CI runs/artifacts, and deployed state before acting. Actual evidence outranks this snapshot. Update the status and active-work handoff with exact commit/run links at meaningful task boundaries. Do not merge PRs or make production changes without explicit founder approval.
