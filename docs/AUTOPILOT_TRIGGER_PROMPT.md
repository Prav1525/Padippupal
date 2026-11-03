# PadippuPal — single engineering trigger

This is the **only reusable trigger** for the integrated PadippuPal engineering agent.

## Trigger

When the founder says **Proceed**, **continue**, **fix**, **test**, or **status**, resume the current approved objective and run the integrated engineering cycle. Do not ask which subsystem to invoke and do not start a separate Engineering OS or AutoPilot process.

## Operating authority

The complete operating contract lives in **`AGENTS.md`**. Read and follow it first. It defines context recovery, work selection, execution, five-generation repair limit, evidence requirements, escalation and production approval boundaries.

The detailed, test-specific rules live in **`TESTING_GUIDANCE.md`**. Read it before every code edit, test, build or deployment action as required by `AGENTS.md`.

## Chat-to-GitHub trigger bridge

When the founder says **Proceed** in ChatGPT and an active same-repository PR is the current work target, the ChatGPT session posts the exact `/proceed` command as a comment on that PR. The AutoPilot workflow listens for that command only when it is posted by the repository owner on an open PR authored by the repository owner; it resolves and records the exact PR head branch and SHA, then dispatches and polls the existing checks. The privileged bridge checks out only trusted default-branch controller code and refuses fork PRs.

This bridge becomes active only after this workflow change is merged into the repository's default branch. Until then, use the existing workflow_dispatch UI. The GitHub workflow runs tests and gathers evidence; the ChatGPT engineering session remains the reasoning and code-repair actor. No unattended model worker, paid model API, or Codex integration is introduced.

## One cycle

1. Recover live repository, roadmap, active-work, PR, CI and prior-investigation state.
2. Select the highest-priority executable task within the approved roadmap and the founder's explicit request.
3. Investigate from evidence; define acceptance criteria for the actual requested product path.
4. Implement the smallest justified change; do not weaken tests or alter unrelated behavior.
5. Run targeted diagnostics, relevant regressions, build and the real feature acceptance path.
6. Inspect results/artifacts, repair evidence-backed failures within the shared five-generation cap, and retest.
7. Update the existing investigation and active-work records; prepare a reviewable PR when appropriate.
8. Report verified results, what remains unverified, blockers and the next action.

## Same-invocation operating contract

- **Engineering OS lane (orchestrator):** recover project context, select approved work, coordinate dependencies and own acceptance.
- **AutoPilot lane (execution and quality subsystem):** enforce deterministic policy checks, observe CI, coordinate existing test workflows and collect evidence.
- **One shared state:** the approved-work ledger, active-work handoff, investigation history and exact branch/PR/SHA evidence are shared across both lanes.
- Together they execute **one coordinated cycle**. Neither lane is a separate user-facing agent or trigger.

## Single-source-of-truth map

- **Behavior and authority:** `AGENTS.md`
- **Build/test execution rules:** `TESTING_GUIDANCE.md`
- **Current task and handoff:** `.engineering/tasks/active-work.md`
- **Approved scope:** `docs/approved-work.json`
- **Durable engineering memory:** `.engineering/README.md` and linked records
- **Failure history:** existing investigation and failure registers
- **CI policy/evidence subsystem:** `.github/workflows/autopilot.yml` and `tools/padippupal_autopilot.py`
- **Existing-check coordinator:** `tools/padippupal_proceed_controller.py`

These are components of one agent workflow, not separate triggers or competing orchestrators. Keep one active-work record, one approved-work ledger and one coordinated report. Do not create duplicate prompts, guides, agents, workflows, queues or state stores.

## Capability honesty

GitHub Actions AutoPilot validates policy and records CI evidence. The Proceed controller dispatches/polls existing checks and summarizes them; it is not an AI code-repair worker. The engineering session performs approved diagnosis and code repair. Do not claim unattended repair or persistent cross-run generation accounting unless implemented and independently verified.

Codex is excluded. Do not add paid model integrations or incur unapproved API spend.

## Approval boundary

Branches, scoped edits, tests and reviewable PRs are allowed within approved scope. **Merging PRs, production deployments, production database writes, destructive migrations, public releases, and changes to security/approval controls require explicit founder approval.**

Start by recovering the live state and continue without asking the founder to repeat known context. Ask only for a genuinely missing decision, permission or approval that blocks safe progress.
