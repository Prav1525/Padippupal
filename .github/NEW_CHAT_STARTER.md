# PadippuPal — New Chat Starter

Copy this into a new ChatGPT conversation before asking for development or status work:

> Continue the existing PadippuPal project. Before answering or editing code, read `DEVELOPMENT_PROTOCOL.md`, `PROJECT_STATE.md`, `docs/ENGINEERING_BEHAVIOR_CHECKLIST.md`, `docs/REGRESSION_CHECKLIST.md`, and `docs/DECISION_LOG.md` from the current repository. Inspect the actual active branch, open PRs, latest commit, and fresh relevant GitHub Actions runs. Treat repository evidence as authoritative over chat memory. Resume the single active objective recorded in `PROJECT_STATE.md`; do not start unrelated work. Diagnose before patching, define acceptance tests first, never weaken tests to make CI green, and report PASS/FAIL/UNVERIFIED/BLOCKED with commit-specific evidence. Update the project state before ending the task. If any repository fact cannot be retrieved, say so and do not guess.

## Required startup actions (assistant)

1. Read the five project documents from GitHub, not from remembered chat summaries.
2. Fetch current branch/head and relevant open PR metadata.
3. Fetch latest workflow runs and match each run to its tested commit SHA.
4. Compare the fresh evidence with the handoff record; correct stale state before coding.
5. State the active objective and the next action in one short status report.
6. Only then begin work.

This prompt is a convenient entry point, not a technical guarantee that a model will execute itself. CI guards and review checks provide additional enforcement.
