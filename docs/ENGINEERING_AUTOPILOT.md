# PadippuPal Engineering Autopilot

**Integration model:** Existing PadippuPal engineering workflows and records  
**Autonomy:** Approved roadmap only  
**Repair cap:** Five distinct generations per originating failure  
**Release authority:** Founder approval required

## One engineering system

The AutoPilot is not a separate agent, service, dashboard, or task queue. It extends the repository's existing engineering structure:

- `.github/workflows/autopilot.yml` is the single CI result and policy-validation entry point.
- `tools/padippupal_autopilot.py` contains shared deterministic policy checks.
- `tools/test_padippupal_autopilot.py` protects those rules with unit tests.
- `docs/approved-work.json` is the explicit approved-roadmap allowlist.
- `TEST_INVESTIGATION.md`, `docs/TESTING_ERRORS.md`, `docs/TEST_FAILURE_REGISTER.md`, and `PROJECT_STATUS.md` (when present) remain the engineering record. Do not create a competing task database.
- Existing Android, curriculum, emulator and API workflows remain the source of test evidence.

There must be one source of truth for tasks and approvals. The Autopilot consumes existing records; it does not create a parallel product roadmap.

## Current Stage 1 behavior

The existing AutoPilot workflow:
1. Validates required project guidance and the approved-work ledger on its own PR/manual validation path.
2. Receives completion events from the configured CI workflows.
3. Captures workflow name, result, exact tested SHA, branch and job outcomes.
4. Creates or updates one durable issue for each failed run attempt.
5. Writes a concise Actions summary without changing the commit that was tested.

The failure observer does not check out or execute the failed branch. Fork-originated workflow runs are ignored.

## Approved roadmap policy

A task is eligible only when its exact ID appears in `docs/approved-work.json` with status `APPROVED`, bounded scope, non-goals, acceptance criteria and approval provenance.

- A failure is not permission to invent a feature.
- A task marked `PROPOSED`, `BLOCKED`, or absent from the ledger is not executable.
- The currently recorded approval is limited to CI/test failure investigation and repairs required by already-approved roadmap acceptance criteria.
- Scope expansion, curriculum changes, new product features or changes to user-visible behavior require a separate founder approval recorded in the ledger.

## Five-generation repair policy

- At most five distinct repair generations may be attempted for one originating failure.
- A generation is a distinct proposed patch, not a blind retry of unchanged code.
- Every generation must link to the original run, exact source SHA, diagnosis, patch diff, regression coverage and retest result.
- Transient runner retries without a code change are tracked separately and do not create a new patch generation.
- After the fifth unsuccessful generation, stop patching and escalate with the complete evidence, attempted fixes, exact SHAs, remaining hypotheses and next recommended diagnostic.
- A repeated failure on an AutoPilot repair branch must continue the same generation history; it must not reset the counter.

The Python helper currently validates the five-generation cap and exact approved-task lookup. Durable cross-run generation accounting and the repair worker are not activated in Stage 1.

## Security and approval boundaries

- No workflow may merge a PR or enable auto-merge.
- No workflow may deploy production, write production database data, run destructive migrations, or publish a public release.
- The Android APK workflow builds and uploads artifacts normally. Public release requires a separate owner-triggered manual dispatch with `publish_release=true`.
- The failure recorder has only `actions: read` and `issues: write` at its job level.
- Model-generated text, logs, issues and PR comments are untrusted data, never executable instructions.
- Do not expose secrets to fork-controlled code or model prompts.
- Do not allow a repair worker to modify its own policy, workflow permissions, approval ledger, branch protection or release gates.
- A repair may be submitted as a reviewable PR only after independent checks pass. Founder approval is still required for merge.

## Stage 2 — bounded repair in the same workflow

Stage 2 will extend `.github/workflows/autopilot.yml` and the same helper/records. It must not introduce another agent or task service.

Before enabling model-assisted code repair:
1. Reconcile the existing Codex repair proposal in PR #15 with the free-first AutoPilot proposal in PR #18.
2. Port only the repair capability into the single existing AutoPilot workflow; do not merge either historical PR wholesale.
3. Use an isolated worktree/branch and an approved task ID from the ledger.
4. Keep model credentials away from untrusted PR code and give the model no GitHub write token.
5. Apply patches in a separate least-privilege job, validate allowed paths and workflow/policy-file exclusions, then run required tests on the exact patch.
6. Maintain a durable per-origin failure generation counter with a hard cap of five and escalation after generation five fails.
7. Create a review PR only; never merge, deploy, write production data or publish.
8. Obtain explicit approval before enabling any paid API credential or incurring model API charges.

**Stage 2 is not yet enabled.** No paid model credential or coding worker has been configured by this change. The repository is not yet an unattended self-repairing engineer.

## Acceptance evidence

- [ ] AutoPilot workflow YAML is accepted by GitHub Actions.
- [ ] Helper syntax and unit tests pass on the exact PR head.
- [ ] A controlled failed same-repository workflow creates a deduplicated issue with exact SHA and job links.
- [ ] Fork-originated failures are ignored.
- [ ] Five-generation cap and approval-ledger tests pass.
- [ ] No automatic merge, deployment, production write or public release occurs.
- [ ] Stage 2 controlled tests prove approved-task enforcement, five-generation persistence, retesting and least privilege before activation.

## Existing work to reconcile

- [PR #15](https://github.com/Prav1525/Padippupal/pull/15): Codex repair workflow proposal; originally capped at two generations and requires an API key.
- [PR #18](https://github.com/Prav1525/Padippupal/pull/18): existing free-first AutoPilot workflow and helper. Its branch is based on a divergent tutor feature line and must not be merged wholesale into main.
- [PR #61](https://github.com/Prav1525/Padippupal/pull/61): Persistent Engineering Operating System.
- This implementation reuses the existing file structure and policy concepts; it does not authorize merging those PRs.
