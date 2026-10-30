# Active work handoff

**Last updated:** 2026-10-30  
**Rule:** Maintain one primary objective. Use this file as the shared handoff for Engineering OS and AutoPilot; do not create separate task queues.

## Active objective: One coordinated “Proceed” operating cycle
- **Task ID:** `UNIFIED-PROCEED-OPERATING-CYCLE`
- **Approval:** Founder explicitly approved implementing the unified Engineering OS + AutoPilot operating behavior in the ChatGPT conversation on 2026-10-30.
- **Scope:** Align repository instructions, canonical trigger, AutoPilot capability documentation, approval ledger and handoff so one “Proceed” invocation runs context recovery, task selection, policy/evidence checks, permitted execution, retest, acceptance review and record updates as one shared cycle.
- **Non-goals:** no second agent/service/workflow/task database; no Codex; no paid model integration; no autonomous GitHub code-writing worker; no changes to learner-facing app behavior; no production writes/deployments/releases; no automatic PR merge.
- **Base:** `main@dcd1b98c2d269fad97af933ed6ff4df5dca18033`.
- **Branch:** `engineering/unified-proceed-operating-cycle`.
- **Status:** Implementation in progress; PR and exact-head verification pending.
- **Acceptance:** `AGENTS.md` and the one canonical trigger define the same invocation; Engineering OS and AutoPilot share one task identity and handoff; AutoPilot's actual capability limits are explicit; exact approval and five-generation policy remain enforced; no competing queue or worker is introduced; policy validation and unit tests pass.
- **Next action:** open a focused PR, run required checks on its exact head, inspect results and update this handoff with SHAs and links.

## Operating sequence for every “Proceed”
1. Re-fetch main, active branch, open PRs and recent workflow runs.
2. Recover the charter, status, architecture, system map, decisions, known issues, acceptance criteria, active task, approved-work ledger and relevant product/test records.
3. Build one prioritized queue from approved active work, open PRs, verified regressions and required dependencies.
4. Select the highest-priority executable task; state why briefly.
5. Apply AutoPilot's approval/evidence/diagnosis/repair-cap/retest rules to that same task.
6. Execute through available connected tools; do not imply background/unattended execution.
7. Verify acceptance on exact commit, update the shared investigation and this handoff, then continue to the next approved item.
8. Stop for missing approval, unavailable evidence/access, unsafe action, or an unresolved dependency.

## Capability truth
GitHub `.github/workflows/autopilot.yml` currently validates policy and records completed CI runs/failures. `tools/padippupal_autopilot.py` provides deterministic checks; it does not implement an AI code-repair worker or durable cross-run generation storage. Five generations remain the operating limit, but unattended repair must stay disabled until durable counting, least-privilege execution and controlled tests exist.

## Completed foundation
- PR #61 — Engineering Operating System merged: `fb17b56524b0f081f7176ff35c949e76d9580d2f`.
- PR #62 — Unified trigger / AutoPilot Stage 1 merged: `dcd1b98c2d269fad97af933ed6ff4df5dca18033`.
- PR #62 exact-head Android emulator navigation smoke passed: https://github.com/Prav1525/Padippupal/actions/runs/40992845745.

## Resume checklist
- Re-fetch live GitHub state; do not trust this snapshot.
- Read `AGENTS.md` and `TESTING_GUIDANCE.md` before every new edit/test/build batch.
- For tutor/UI tasks, also read `.github/testing-regression-checklist.md` and `docs/TESTING_ERRORS.md`.
- Inspect logs/artifacts before retrying; never repeat an unchanged failed approach.
- Record exact SHAs, commands, check URLs, outcomes and limitations.
