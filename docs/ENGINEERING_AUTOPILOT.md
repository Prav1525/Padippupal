# PadippuPal integrated engineering agent — architecture note

This file is a short architecture reference, **not another prompt or operating guide**. The canonical behavior is in [`AGENTS.md`](../AGENTS.md); the only reusable trigger is [`AUTOPILOT_TRIGGER_PROMPT.md`](AUTOPILOT_TRIGGER_PROMPT.md); test/build-specific rules are in [`TESTING_GUIDANCE.md`](../TESTING_GUIDANCE.md).

## One agent, one cycle

The founder invokes the whole engineering process with **Proceed**. Engineering OS recovers context, selects approved work and owns acceptance. AutoPilot contributes policy validation, CI observation and evidence collection. The same active-work record, approved-work ledger, investigation history and exact branch/PR/SHA evidence are shared throughout.

## Existing implementation components

- `.github/workflows/autopilot.yml`: policy validation and CI result recording; optional full-cycle dispatch.
- `tools/padippupal_autopilot.py`: deterministic approved-work and contract checks.
- `tools/padippupal_proceed_controller.py`: dispatches/polls existing checks and writes one summary.
- `tools/test_padippupal_autopilot.py` and `tools/test_padippupal_proceed_controller.py`: policy/controller regression tests.
- `docs/approved-work.json`: approved scope allowlist.
- `.engineering/tasks/active-work.md`: one current task and handoff.
- Existing investigation/failure records: append-only evidence history.

## Verified capability boundary

The CI controller is not an AI code-repair worker. It coordinates checks and collects results; the engineering session performs approved investigation, implementation, repair and retesting. Durable cross-run repair-generation accounting is not yet implemented. Do not claim unattended repair or persistent counting until those capabilities are implemented and tested.

Codex remains excluded. No paid model integration is introduced. Merges, production deployments, production database writes and public releases require explicit founder approval.
