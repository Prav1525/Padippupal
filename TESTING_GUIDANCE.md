# Testing and Investigation Guidance

These rules are mandatory for all PadippuPal engineering and test work. Carry them forward between sessions; do not make the user repeat them.

## Before acting
1. Read the current project state, development protocol, open PR context, prior test results, and investigation log before making changes.
2. Preserve the user's explicit guidance and constraints as durable project notes. Treat the existing investigation as continuous work, not a fresh start each message.
3. Identify the exact failing behavior and the last known evidence. Separate confirmed facts from hypotheses.

## Every test attempt must be logged
For every meaningful run, record:
- Date/time, branch and commit SHA, workflow/run/job URL, and test command or test name.
- Exact PASS/FAIL/BLOCKED/UNVERIFIED outcome and the failing step/error text.
- Relevant logs, screenshots, UI hierarchy/accessibility dumps, artifacts, and links.
- What the attempt proves, what it does not prove, and how it differs from previous attempts.
- The next diagnostic/fix, with a reason based on the evidence.

Do not report a test as passing because the build passed, a script validated, or a related test passed. Report each layer separately. Keep failure records; do not overwrite history with only the latest result.

## Root-cause-first workflow
1. Reproduce the failure and inspect the actual logs/artifacts/screenshots and relevant code path.
2. Trace the failure to the responsible layer (test harness, emulator/environment, platform picker, app integration, backend, or data) before choosing a fix.
3. State the root cause as **confirmed**, **probable**, or **unknown**, and cite the evidence. Do not present a hypothesis as fact.
4. Make the smallest targeted change that addresses the supported cause.
5. Run the narrowest diagnostic test first, then relevant regression tests, then the full acceptance path.
6. Compare the new evidence with the previous attempt and update the investigation log.

## Do not loop
- Never repeat the same failed approach or make blind coordinate/selector tweaks without a testable hypothesis.
- Before retrying, state what changed and why that change should alter the outcome.
- If a retry produces the same failure, do not repeat it again unchanged. Gather new evidence or switch to a materially different diagnostic.
- Do not call activity progress. A code change is not a fix until the relevant behavior is verified.

## Evidence and reporting
- Show the user the exact failure point and the most relevant screenshot/log/artifact when available.
- For UI failures, capture the state at failure and inspect the accessibility/UI hierarchy; distinguish a harness failure from an app/platform failure.
- Maintain a concise durable investigation record with: symptom, attempts, evidence, confirmed cause or open hypotheses, changes made, test outcomes, and next action.
- Report status explicitly as **PASS**, **FAIL**, **UNVERIFIED**, or **BLOCKED**, with the reason. Never claim a fix, test, or deployment succeeded without evidence.
- Keep user updates concise, direct, and action-oriented. Do not make the user repeatedly ask for status or repeat prior guidance.

## Change and merge safety
- Do not merge any PR or merge unrelated PRs without the user's explicit permission.
- Before proposing a merge, check acceptance criteria, required CI checks, and relevant regression tests; report failures honestly.
- If blocked, explain the blocker and the specific evidence needed next instead of repeatedly trying the same thing.

## Current PadippuPal image-picker investigation
The latest recorded emulator smoke run failed before the app received a selected image URI: DocumentsUI remained on Downloads after the fixture row/thumbnail tap. The screenshot and XML show the filename/thumbnail nodes as non-clickable, while the separate preview control is clickable. This makes the test's selection interaction suspect, but does not by itself prove whether the picker, harness, or app is at fault. Root cause remains **UNKNOWN** until a materially different diagnostic isolates the layer. Do not repeat blind coordinate tweaks. Do not claim the image picker is fixed until the actual selection/URI return and downstream crop/rescan/save flow are verified.
