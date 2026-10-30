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
