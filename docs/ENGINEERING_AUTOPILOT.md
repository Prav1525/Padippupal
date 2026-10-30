# PadippuPal Engineering Autopilot

**Policy owner:** Founder  
**Autonomy mode:** Approved roadmap only  
**Maximum repair generations:** 5 per originating failure  
**Release boundary:** Explicit founder approval required

## Objective

Keep an approved engineering task moving through evidence collection, root-cause investigation, focused repair, retest, and review without requiring the founder to prompt every ordinary next step.

The Autopilot is a bounded workflow, not an unrestricted agent. It may act only on an explicit approved roadmap item with acceptance criteria. A failing check does not itself authorize a new product feature or a change in product direction.

## Architecture

1. **GitHub Actions observer (implemented in Stage 1):** listens for completion of the named CI workflows, records failed jobs and exact tested SHA, and creates/updates a deduplicated GitHub issue. It does not check out or execute the failed branch.
2. **Evidence and task ledger:** the failure issue links to the originating workflow run and lists the required investigation steps. The engineering handbook and task ledger remain the source of scope and approval.
3. **Reasoning/repair worker (Stage 2, not yet enabled):** a separately configured coding agent receives only the approved task, relevant source files, failure logs and required project guidance. It works in an isolated branch/worktree, proposes one root-cause patch per generation, and cannot merge or deploy.
4. **Verification worker (Stage 2):** runs the narrow diagnostic, regression suite and applicable build/integration/UI checks against the proposed exact commit. It must not weaken assertions or skip a failing acceptance criterion.
5. **Review and release gate:** a repair PR is the handoff to the founder. Merge, production deployment, production database writes, destructive actions and public releases remain human-approved.

## Approved-roadmap-only rule

A task is eligible for autonomous implementation only when the repository contains an explicit approved roadmap entry with:
- stable task ID and status `APPROVED`;
- bounded scope and non-goals;
- acceptance criteria and required verification;
- dependencies and risk classification;
- approval provenance/date.

The worker must not infer approval from a conversation summary, a failing test, a draft PR, a roadmap suggestion, or a previously discussed idea. If no matching approved entry exists, it may investigate and report but must not implement a feature.

## Bounded repair policy

- Maximum **5 distinct repair generations** for one originating failure.
- Each generation must state what evidence changed and why the proposed fix addresses the diagnosed cause.
- Never rerun an unchanged failed approach merely to consume a retry.
- A generation counts when a distinct patch is proposed; a transient infrastructure retry without a code change is recorded separately.
- After generation 5 still fails, stop automatic patching and escalate with the original symptom, all attempts, logs, exact SHAs, test outcomes, unresolved hypotheses and the next recommended diagnostic.
- A new originating workflow run does not silently reset the history; correlate it with the existing failure/task record.

## Permissions and security

- The Stage 1 observer has only `actions: read` and `issues: write`. It does not have contents, pull-request, deployment or release write access.
- The reasoning worker must not receive a GitHub write token or production credentials. A separate, narrow publisher job may open a PR after independent checks.
- Never use `pull_request_target` to execute untrusted PR code.
- Do not expose secrets to PR-controlled code or echo secrets in logs.
- Treat logs, issue bodies, model output and generated patches as untrusted data. Validate paths, diff scope and patch format.
- Do not permit the worker to edit its own policy, permissions, branch protection, required checks or release gates.
- No automatic merge, auto-merge, production deploy, production DB write, destructive migration, or public release.

## Public APK release approval

The Android build workflow must build and upload an artifact without publishing it. A public GitHub release is a separate workflow job that runs only when the repository owner manually dispatches the workflow with `publish_release=true`. The publishing job alone receives `contents: write`. This is an explicit founder action and uses the artifact produced by that same workflow run.

## Stage status

### Stage 1 — deterministic failure observer
- **Implemented on this branch:** `.github/workflows/autopilot-failure-observer.yml`.
- Records failed workflow name, exact SHA, job outcomes and links.
- Creates or updates a deduplicated issue.
- Does not modify source code or attempt an AI-generated fix.
- **Not operational on main until this branch is reviewed and merged.**

### Stage 1 safety hardening
- **Implemented on this branch:** Android public APK publishing is removed from automatic main-branch pushes.
- Public release now requires a manual workflow dispatch with `publish_release=true` by the repository owner.
- Build job has read-only contents permission; only the manually gated release job has contents write.
- **Not active on main until reviewed and merged.**

### Stage 2 — bounded repair worker
- **Not implemented/activated yet.**
- Existing proposals PR #15 (Codex-based repair) and PR #18 (free-first deterministic triage) must be reconciled before adding another overlapping system.
- PR #15 currently documents a two-generation limit; it does not satisfy the founder's five-generation policy as-is.
- A model/API credential or an available coding-agent integration and explicit cost approval may be required. Do not assume a secret exists or silently incur API charges.
- Before activation, inspect the complete workflow, action pinning, token scopes, path/diff allowlists, fork protections, retry accounting and controlled failure-test results.
- Stage 2 must use the approved roadmap manifest, stop after five distinct generations and create review PRs only.

## Acceptance criteria

- [ ] Observer YAML parses and GitHub accepts the workflow.
- [ ] A controlled same-repository failed workflow creates one issue with exact SHA, run URL and failed-job links.
- [ ] Repeated delivery for the same run attempt updates the same issue rather than creating duplicates.
- [ ] Fork-originated runs are ignored.
- [ ] Observer has no repository contents, pull-request, deployment or release write permission.
- [ ] Android build still uploads the APK on ordinary pushes/PRs.
- [ ] No public release is created by an ordinary push or pull-request run.
- [ ] Public release can run only after owner dispatch with `publish_release=true`, and publishes the artifact built in that run.
- [ ] Stage 2 controlled test proves approved-task scope, five-generation stop, independent retests, and no merge/deploy/production-write capability before activation.

## Related work to reconcile

- [PR #15 — automated CI failure triage reports](https://github.com/Prav1525/Padippupal/pull/15): Codex auto-repair proposal, two generations, requires a configured API key and cost acceptance.
- [PR #18 — free-first AutoPilot triage](https://github.com/Prav1525/Padippupal/pull/18): deterministic observer and optional local advisory model; no autonomous code patching.
- [PR #61 — Persistent Engineering Operating System](https://github.com/Prav1525/Padippupal/pull/61): project memory and acceptance rules.
- These PRs remain separate and unmerged. This document does not authorize merging any of them.
