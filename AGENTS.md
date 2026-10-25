# Mandatory Agent Instructions for PadippuPal

**Before every code edit, test change, configuration change, or deployment action, read `TESTING_GUIDANCE.md` in full and follow it.** This is a per-action requirement, not a one-time setup step. If a task spans multiple edits or sessions, re-open the guidance before each new batch of edits and whenever the investigation context changes.

## Required pre-change gate
Before touching code, state in your working notes (and in the user update when meaningful):
1. The relevant guidance being applied.
2. The current branch and commit.
3. The exact failure/requirement and latest evidence.
4. Whether the root cause is confirmed, probable, or unknown.
5. The specific change proposed and why it should address the evidence.
6. The diagnostic and regression tests that will verify it.

If the latest failure evidence or project state is not available, retrieve it first. Do not guess or restart the investigation from scratch.

## Required post-change gate
After any change:
1. Record the changed files and commit SHA.
2. Run the narrowest relevant test, then required regression/acceptance tests where possible.
3. Record exact outcomes and links to logs/artifacts/screenshots.
4. Compare results with previous attempts and update the durable investigation log.
5. Tell the user what changed, what was tested, what failed or remains unverified, and the next evidence-based action.

Never claim success without verification. Never repeat an unchanged failed approach. Never merge a PR without the user's explicit permission.

These requirements apply to all coding agents and human contributors. `TESTING_GUIDANCE.md` is the detailed source of truth.
