# PadippuPal CI automation

This is the existing PadippuPal AutoPilot workflow, not a separate agent.

## Existing flow

```text
Android / Curriculum / Emulator / API workflows
                    |
                    v
        .github/workflows/autopilot.yml
                    |
          +---------+----------+
          |                    |
          v                    v
   CI run summary       Failure issue record
          |                    |
          +---------+----------+
                    |
                    v
 TEST_INVESTIGATION.md + docs/TESTING_ERRORS.md
 + docs/TEST_FAILURE_REGISTER.md + PROJECT_STATUS.md
                    |
                    v
        approved-work.json gate
                    |
                    v
      reviewed repair PR (Stage 2)
```

The test workflows remain authoritative. AutoPilot records their outcomes and exact tested commit; it does not mark a product feature verified from a green build alone.

## Local checks

```bash
python tools/padippupal_autopilot.py validate
python -m py_compile tools/padippupal_autopilot.py tools/test_padippupal_autopilot.py
python tools/test_padippupal_autopilot.py
```

## Approved work

Edit `docs/approved-work.json` only after explicit founder approval. Each approved entry must include a stable unique ID, scope, non-goals, acceptance criteria and approver. Proposed or missing IDs are not eligible for autonomous implementation.

## Repair cap

The policy helper permits at most five distinct repair generations. A sixth generation is blocked. A production implementation must persist this count across workflow runs; Stage 1 validates the rule but does not yet run a model repair worker.

## Permissions

- Observer job: `actions: read`, `issues: write`.
- No write permission to repository contents or pull requests in the observer.
- No production credentials.
- No automatic merge, deployment, production database write, destructive migration, or public release.
- Public APK publishing is gated by owner-triggered `workflow_dispatch` with `publish_release=true`.

## Single trigger prompt

The complete non-Codex engineering procedure lives in [AUTOPILOT_TRIGGER_PROMPT.md](AUTOPILOT_TRIGGER_PROMPT.md). Use that one prompt to coordinate context recovery, CI evidence, failure investigation, approved-scope validation, bounded repair, retesting, engineering records, PR preparation and escalation.

Codex and paid model integrations are excluded. The trigger prompt does not imply that a code-repair worker or durable cross-run generation counter is already running; verify the actual tools and repository capabilities before starting a repair. If no safe repair mechanism or persistent counter exists, stop and report the limitation.

Do not add another agent, observer workflow, service or task ledger. PR #15's Codex worker is intentionally not part of this architecture.
