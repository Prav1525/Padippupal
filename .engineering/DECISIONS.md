# Engineering decision log

Append new decisions. Do not delete rejected alternatives or silently rewrite prior rationale.

## DEC-001 — GitHub repository is the durable project memory
- **Date:** 2026-10-30
- **Status:** Adopted for Phase 1
- **Decision:** Keep the engineering handbook in the existing `Prav1525/Padippupal` repository.
- **Reason:** Project code, tests, architecture, decisions, and task handoffs should evolve under the same version history.
- **Consequence:** Every new task must reconcile the docs with actual repository/CI/deployment state; documentation is not automatically live.

## DEC-002 — Founder approval is required for release-impacting actions
- **Date:** 2026-10-30
- **Status:** Adopted
- **Decision:** Do not merge PRs or change production systems/data without explicit founder approval.
- **Reason:** Build/test authorization is not release authorization; preserve clear human control over production.
- **Consequence:** Agents may prepare a PR and present evidence, but must stop before merge/deploy/production writes.

## DEC-003 — Actual evidence outranks remembered status
- **Date:** 2026-10-30
- **Status:** Adopted
- **Decision:** Re-fetch branch heads, PR state, workflow runs, artifacts, and deployed commit before relying on a prior handoff.
- **Reason:** Conversation memory and dated docs can become stale.
- **Consequence:** Status documents carry a snapshot date and must be reconciled at task start.

## DEC-004 — Preserve existing quality guidance instead of duplicating it
- **Date:** 2026-10-30
- **Status:** Adopted
- **Decision:** The new handbook links to and supplements `AGENTS.md`, `TESTING_GUIDANCE.md`, regression checklist, and test error ledger.
- **Reason:** Multiple competing rulebooks would drift and create contradictory instructions.
- **Consequence:** Update the existing canonical guides when their requirements change; keep this handbook focused on product context, architecture, decisions, and handoff.

## DEC-005 — Local Codex CLI is the bounded coding executor
- **Date:** 2026-11-12
- **Status:** Adopted with founder approval
- **Decision:** Use the founder's already authenticated local Codex CLI through a repository-owned `codex exec` runner, integrated with the existing PadippuPal approved-work ledger and single Proceed contract.
- **Reason:** The existing Python AutoPilot and Proceed controller enforce policy and coordinate evidence but do not edit source code. A local executor closes that capability gap without introducing a second agent, remote model service, or paid API integration.
- **Execution boundary:** The runner requires a clean working tree, an approved task, an authenticated Codex CLI, and passing policy validation. It creates a non-main branch and uses the `workspace-write` sandbox with `on-request` approvals.
- **Review boundary:** The runner returns a patch and summary; it does not commit, push, merge, deploy, publish, mutate production data, or perform destructive operations. Merge and release approvals remain separate.
- **Trigger limitation:** A ChatGPT message cannot wake a sleeping local Termux process. The local runner is started by `python tools/padippupal_local_executor.py proceed`; no remote or always-on bridge is claimed.
- **Consequence:** The existing GitHub Actions workflows remain responsible for CI validation and evidence. Local Codex execution is not treated as verified until the runner and its tests pass on the target Termux/Ubuntu environment.


## DEC-006 — Local polling listener connects the GitHub Proceed trigger to Termux

- **Date:** 2026-11-12
- **Status:** Adopted with founder approval
- **Decision:** When the founder's Android/Termux session is running, a repository-owned local listener polls the existing GitHub issue-comment stream and invokes the already approved local Codex executor for a valid owner-authored `/proceed` comment.
- **Reason:** The existing GitHub Actions bridge can dispatch CI but cannot reach or wake a process behind the founder's device/network boundary. A local poller is the smallest practical bridge without a cloud worker.
- **Authorization:** Accept only an exact `/proceed` comment by the repository owner on an open PR authored by the repository owner in the same repository. Fetch the PR ref and require the fetched SHA to match the API head SHA before execution.
- **Execution boundary:** Run the existing local executor in a detached isolated worktree; retain its local patch and summary; post a result comment. Store the fine-grained token on-device with owner-only permissions and never pass it to the Codex child process.
- **Availability boundary:** The listener must be running. If Termux is stopped or Android kills it, local execution pauses; GitHub Actions CI continues independently.
- **Safety:** No automatic commit, push, PR creation, merge, deployment, production write, release, destructive operation, paid model API, or approval bypass.
- **Consequence:** One local startup command arms the bridge. The end-to-end path is not considered verified until the target Termux session receives a fresh `/proceed`, runs Codex and posts its result successfully.
