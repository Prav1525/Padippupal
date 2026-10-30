# Architecture and Product Decision Record

Append decisions; do not silently rewrite historical choices.

## ADR-0001 — GitHub repository is the durable engineering source of truth
- **Status:** Accepted
- **Decision:** Keep project charter, architecture inventory, decisions, current state, active work and acceptance criteria in the existing Padippupal repository.
- **Reason:** These records can be reviewed alongside code, versioned with changes and recovered across ChatGPT sessions.
- **Consequence:** Notes must be reconciled with live GitHub/CI/deployment state at session start. Repository docs are not a substitute for live verification.

## ADR-0002 — Owner approval gates production-impacting operations
- **Status:** Accepted
- **Decision:** PR merges, production database writes/schema changes and production-impacting releases require explicit owner approval.
- **Reason:** Protect production data and preserve founder control.
- **Consequence:** Automation may validate and prepare releases but must not merge or deploy to production autonomously.

## ADR-0003 — Evidence-based status vocabulary
- **Status:** Accepted
- **Decision:** Track IMPLEMENTED, TESTED, DEPLOYED and LEARNER-READY separately; use UNVERIFIED/BLOCKED when evidence is missing.
- **Reason:** Prevent a successful build or mock test from being misreported as end-to-end success.
- **Consequence:** Every status claim links to a commit, workflow, log, artifact, screenshot or environment read-back where applicable.

## ADR-0004 — Phase 1 documentation is conservative by design
- **Status:** Accepted
- **Decision:** Architecture and system maps distinguish repository-observed facts from inferred or unknown runtime behaviour.
- **Reason:** Avoid encoding hallucinated architecture into the project's permanent memory.
- **Consequence:** Complete call graphs and data-flow diagrams only after source-level inspection.
