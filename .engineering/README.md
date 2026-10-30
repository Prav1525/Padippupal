# Engineering Operating System

This directory is PadippuPal's durable engineering memory. It supplements (and does not replace) the repository's mandatory `AGENTS.md`, `TESTING_GUIDANCE.md`, `.github/testing-regression-checklist.md`, and `docs/TESTING_ERRORS.md`.

## Start here
1. [Project charter](../PROJECT_CHARTER.md) — product mission, principles, roles, and approval boundaries.
2. [Project status](../PROJECT_STATUS.md) — dated handoff snapshot; re-verify before relying on it.
3. [Architecture](ARCHITECTURE.md) — inspected code-level component map and known uncertainty.
4. [System map](SYSTEM_MAP.md) — data and teaching flow across the app.
5. [Decision log](DECISIONS.md) — durable decisions and rationale.
6. [Known issues](KNOWN_ISSUES.md) — unresolved gaps, risks, and verification needs.
7. [Acceptance criteria](ACCEPTANCE_CRITERIA.md) — definition of done by engineering layer.
8. [Active work](tasks/active-work.md) — one objective, scope, evidence, and next action.

## Update rules
- Update status and active-work records at meaningful task boundaries.
- Append decisions; do not silently rewrite history.
- Keep known issues until there is evidence they are resolved.
- Use exact commit SHAs, workflow URLs, artifact links, and environment labels.
- Distinguish **Implemented**, **Tested**, **Verified**, **Deployed**, **Learner-ready**, and **Blocked**.
- Never store secrets, access tokens, private learner data, or production connection strings.
- This handbook is documentation, not proof of enforcement. CI automation and branch protection are a later phase.
