# PadippuPal Engineering OS — canonical index

PadippuPal runs as **one integrated engineering agent**. There is one trigger (`Proceed`), one operating contract, one active-work handoff and one approved-work ledger. This handbook is an index and durable-memory map; it does not define a second workflow.

## Read in this order

1. [Agent behavior, authority and closed-loop execution](../AGENTS.md) — canonical operating contract.
2. [Single Proceed trigger](../docs/AUTOPILOT_TRIGGER_PROMPT.md) — the only reusable trigger; delegates to the canonical contract.
3. [Test and build execution standard](../TESTING_GUIDANCE.md) — test-specific rules, evidence and diagnostics.
4. [Project charter](../PROJECT_CHARTER.md) — mission, principles, roles and approval boundaries.
5. [Project status](../PROJECT_STATUS.md) — dated snapshot; refresh live evidence before relying on it.
6. [Architecture](ARCHITECTURE.md) and [system map](SYSTEM_MAP.md) — implementation and data flow.
7. [Decision log](DECISIONS.md), [known issues](KNOWN_ISSUES.md), and [acceptance criteria](ACCEPTANCE_CRITERIA.md).
8. [Active work](tasks/active-work.md) — the single current objective, evidence and next action.

## Shared state and execution

- Approved scope: `../docs/approved-work.json`.
- Investigation history and failure registers: update the existing records; never create parallel ledgers.
- CI policy/evidence subsystem: `../.github/workflows/autopilot.yml` and `../tools/padippupal_autopilot.py`.
- Existing workflow coordinator: `../tools/padippupal_proceed_controller.py`.
- Existing Android, curriculum, API and UI workflows remain the source of test evidence.

Engineering OS selects and coordinates the approved work; AutoPilot supplies policy checks, CI observation and evidence. They are parts of the same cycle, not separate agents.

## Recordkeeping rules

Update the one active-work handoff and append-only investigation history at meaningful task boundaries. Preserve decisions and failures. Use exact branch names, commit SHAs, run URLs and artifact links. Distinguish implemented, tested, runtime-verified, deployed and learner-ready. Never store secrets, tokens, private learner data or production connection strings.

This handbook is documentation. A documented rule is not automatically enforced by CI or branch protection; state enforcement limitations honestly.
