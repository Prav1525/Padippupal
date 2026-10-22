# PadippuPal Engineering Behaviour Checklist

Use this as the short enforcement checklist for every development task. The full rules are in `DEVELOPMENT_PROTOCOL.md`; verified current state belongs in `PROJECT_STATE.md`.

## Before changing code
- [ ] Read the protocol, project state, regression checklist, decision log, and new-chat starter from the current repository.
- [ ] Inspect the actual branch, HEAD SHA, open PRs, current diff, and fresh relevant CI runs.
- [ ] State one objective and explicit non-goals; do not drift into unrelated work.
- [ ] Compare expected versus actual behaviour and collect reproducible evidence.
- [ ] Trace the execution path and distinguish confirmed causes from hypotheses.
- [ ] Define observable acceptance criteria and regression tests before patching.

## While diagnosing and fixing
- [ ] Think across the full system: UI, state, data contracts, API, database, async/lifecycle behaviour, fallbacks, and tests where relevant.
- [ ] Fix the underlying cause, not just the visible symptom.
- [ ] Make the smallest complete change; preserve working behaviour and review shared dependencies.
- [ ] Never weaken assertions, skip tests, suppress errors, or hardcode success to make CI green.
- [ ] If a fix/test fails, capture the new evidence and revisit the diagnosis instead of stacking speculative patches.
- [ ] Do not change product direction or silently expand scope.

## Before calling it complete
- [ ] Review the full diff for unrelated changes and regressions.
- [ ] Run focused tests, relevant regression tests, build checks, and end-to-end/UI/emulator checks when required and available.
- [ ] Report each check as PASS, FAIL, UNVERIFIED, or BLOCKED against the exact commit SHA; link evidence.
- [ ] Do not confuse compilation with correct behaviour, or historical CI with current verification.
- [ ] Update `PROJECT_STATE.md`, regression cases, and decision records as applicable.
- [ ] If any required check did not run or failed, state that plainly and leave the task unverified/open.

## PadippuPal tutor-flow acceptance
- [ ] Lesson content comes from the approved curriculum source; missing matching content fails safely.
- [ ] Selected class/board/subject/chapter/topic controls the lesson text, narration, animation, highlighting, and checkpoint.
- [ ] Speech highlighting is inline in the same lesson text and scrolls appropriately.
- [ ] The visual demonstrates the exact concept currently explained.
- [ ] Teacher-like pacing and the understand/re-explain/question checkpoint work without unintended advancement.

## Status communication
State: objective; branch and HEAD SHA; changes made; fresh checks and evidence; unresolved failures/root-cause confidence; next single action. Never claim work or verification that did not actually happen.

**Rule of thumb:** Understand first. Plan the complete correction. Change code carefully. Test real behaviour. Review for regressions. Record evidence. Then move forward.
