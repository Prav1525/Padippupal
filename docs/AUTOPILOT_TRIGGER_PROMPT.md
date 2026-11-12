# PadippuPal — single engineering trigger

This is the **only reusable trigger** for the integrated PadippuPal engineering agent.

## Trigger

When the founder says **Proceed**, **continue**, **fix**, **test**, or **status**, resume the current approved objective and run the integrated engineering cycle. Do not ask which subsystem to invoke and do not start a separate Engineering OS or AutoPilot process.

## Operating authority

The complete operating contract lives in **`AGENTS.md`**. Read and follow it first. It defines context recovery, work selection, execution, five-generation repair limit, evidence requirements, escalation and production approval boundaries.

The detailed, test-specific rules live in **`TESTING_GUIDANCE.md`**. Read it before every code edit, test, build or deployment action as required by `AGENTS.md`.

## Chat-to-GitHub trigger bridge

When the founder says **Proceed** in ChatGPT and an active same-repository PR is the current work target, the ChatGPT session posts the exact `/proceed` command as a comment on that PR. The AutoPilot workflow listens for that command only when it is posted by the repository owner on an open PR authored by the repository owner; it resolves and records the exact PR head branch and SHA, then dispatches and polls the existing checks. The privileged bridge checks out only trusted default-branch controller code and refuses fork PRs. The same coordinated matrix also runs automatically on qualifying engineering PRs after policy validation; a PR's exact head ref/SHA is passed as data, never executed with the privileged controller token.

The GitHub comment bridge is active on main; its workflow was merged in PR #186. An owner-authored /proceed comment starts the existing GitHub Actions check cycle. If the local Termux listener described below is also running, it independently detects the same comment and starts the approved local Codex executor. The GitHub workflow remains the CI evidence collector; the local listener is only a transport/dispatcher, not a second agent. No cloud worker or paid model API is introduced.

## Main-branch post-merge cycle

Every push to `main` starts all five existing check workflows and the trusted
coordinator. The coordinator waits for and reuses each workflow run matching
the exact pushed SHA, then polls active runs every five minutes. If an exact
push run does not appear within five minutes, it reports the gap and refuses
to dispatch against a potentially newer branch head. This keeps post-merge
monitoring on the same exact-commit evidence path as an explicit Proceed cycle.

## One cycle

1. Recover live repository, roadmap, active-work, PR, CI and prior-investigation state.
2. Select the highest-priority executable task within the approved roadmap and the founder's explicit request.
3. Investigate from evidence; define acceptance criteria for the actual requested product path.
4. Implement the smallest justified change; do not weaken tests or alter unrelated behavior.
5. **Run one coordinated, feature-complete test pass.** Build a single test matrix from the acceptance criteria and execute all applicable independent checks together (parallelize where safe): static/unit, backend/API/integration, app build, emulator/device UI, feature-specific runtime acceptance, regression and safety-boundary checks. Do not make the founder request or approve tests one at a time, and do not split a known complete test scope into repeated sequential test sessions merely for convenience. Do not substitute a generic smoke test for the named feature.
6. Inspect the complete result set and actual artifacts (logs, screenshots, UI hierarchy, API responses and build outputs). If any check fails, diagnose from evidence, make the smallest justified repair within the shared five-generation cap, then rerun the **complete affected acceptance matrix as one coordinated pass** so the final report reflects one consistent tested commit. Avoid duplicate or overlapping runs; do not wait for another user prompt between independent checks.
7. Update the existing investigation and active-work records; prepare a reviewable PR when appropriate.
8. Report one consolidated result: each layer's PASS / FAIL / BLOCKED / NOT RUN state, exact tested SHA and run/artifact links, what the combined evidence proves, remaining gaps, and the next action. Never describe a partial test subset as full feature verification.

## Same-invocation operating contract

- **Engineering OS lane (orchestrator):** recover project context, select approved work, coordinate dependencies and own acceptance.
- **AutoPilot lane (execution and quality subsystem):** enforce deterministic policy checks, observe CI, coordinate existing test workflows and collect evidence.
- **One shared state:** the approved-work ledger, active-work handoff, investigation history and exact branch/PR/SHA evidence are shared across both lanes.
- Together they execute **one coordinated cycle**. All independent existing checks are dispatched and monitored concurrently, then reported in one stable matrix. While a test run is active, its status is rechecked every five minutes (best-effort; GitHub Actions scheduling/API latency can delay an observation). This is monitoring, not a blind test rerun. A failed check does not prevent other checks from completing. Neither lane is a separate user-facing agent or trigger.

## Single-source-of-truth map

- **Behavior and authority:** `AGENTS.md`
- **Build/test execution rules:** `TESTING_GUIDANCE.md`
- **Current task and handoff:** `.engineering/tasks/active-work.md`
- **Approved scope:** `docs/approved-work.json`
- **Durable engineering memory:** `.engineering/README.md` and linked records
- **Failure history:** existing investigation and failure registers
- **CI policy/evidence subsystem:** `.github/workflows/autopilot.yml` and `tools/padippupal_autopilot.py`
- **Existing-check coordinator:** `tools/padippupal_proceed_controller.py`
- **Local GitHub-to-Termux transport:** `tools/padippupal_proceed_listener.py` (polls comments and invokes the existing local executor; it does not select or authorize new work)

These are components of one agent workflow, not separate triggers or competing orchestrators. Keep one active-work record, one approved-work ledger and one coordinated report. Do not create duplicate prompts, guides, agents, workflows, queues or state stores.

## Capability honesty

GitHub Actions AutoPilot validates policy and records CI evidence. The Proceed controller dispatches existing checks, discovers newly-created runs, monitors active runs at five-minute intervals, and summarizes them; it is not an AI code-repair worker. ChatGPT coordinates the approved objective and reviews the evidence; the local Codex CLI runner performs source edits when explicitly invoked on the founder's device. Do not claim unattended repair or persistent cross-run generation accounting unless implemented and independently verified.

## Local Codex execution

The local authenticated Codex CLI is the approved coding executor. The existing runner is invoked inside an isolated worktree with the workspace-write sandbox and on-request approvals. It validates the approved-work ledger, active objective and policy, reads the canonical engineering instructions, runs the mandatory Python safety checks, and leaves a reviewable local patch. It never commits or pushes.

### One-time Termux setup

1. Create a GitHub fine-grained personal access token restricted to this repository with **Issues: read/write** and **Pull requests: read** permissions. No Contents write permission is needed.
2. Run `python tools/padippupal_proceed_listener.py start`. If no token is configured, it prompts for the token with hidden input, validates repository/issue/pull-request read access, stores it under the user's home directory with owner-only file permissions, then starts polling. If already configured, it starts directly. The token never belongs in Git or ChatGPT.

When the founder says **Proceed** here, ChatGPT posts the exact `/proceed` comment to the active owner-authored PR. GitHub Actions runs the existing CI cycle; the local listener detects the same comment, validates the PR owner/same-repository/open state and exact head SHA, creates an isolated Git worktree, then invokes `python tools/padippupal_local_executor.py proceed`. It posts the result and exact tested SHA back to that PR. Each comment is claimed once and historical comments are not replayed on first startup.

**Trigger boundary:** ChatGPT cannot wake a stopped Android/Termux process. Local Codex execution happens only while the listener is running and polling. If Termux is stopped or Android kills it, GitHub CI still runs but local Codex waits until the listener is restarted. The listener does not pass its GitHub token to the Codex child process. Codex retains workspace-write sandboxing and on-request approvals; never use danger-full-access or approval bypass.

The listener retains each execution worktree, patch and summary locally for review. It does not commit, push, create PRs, merge, deploy, publish, write production data or perform destructive operations. The direct local runner remains available for manual diagnostics.
## Approval boundary

Branches, scoped edits, tests and reviewable PRs are allowed within approved scope. **Merging PRs, production deployments, production database writes, destructive migrations, public releases, and changes to security/approval controls require explicit founder approval.**

Start by recovering the live state and continue without asking the founder to repeat known context. Ask only for a genuinely missing decision, permission or approval that blocks safe progress.
