# Testing, Build, and Investigation Guidance

These rules are mandatory for all PadippuPal engineering, build, and test work. Carry them forward between sessions; do not make the user repeat them.

## Before acting
1. Read the current project state, development protocol, open PR context, prior test/build results, and investigation log before making changes.
2. Preserve the user's explicit guidance and constraints as durable project notes. Treat the existing investigation as continuous work, not a fresh start each message.
3. Identify the exact failing behavior or requirement and the last known evidence. Separate confirmed facts from hypotheses.
4. Before every new code/configuration/build-script edit or test/build/deployment action, re-open this guidance and apply the relevant sections. For read-only inspection, inspect the relevant guidance and latest evidence before taking consequential follow-up action.

## Build guidance
1. Read the README build instructions and inspect the actual Gradle wrapper, Gradle/plugin versions, Android SDK requirements, build variants, and CI workflow before choosing a build command. Do not assume a wrapper or task exists; verify it in the repository.
2. Prefer the repository's Gradle wrapper (for example, `./gradlew`) when present so local and CI Gradle versions are consistent. If it is absent, use the documented CI/build setup and record the exact Gradle version used. Do not silently upgrade Gradle, Kotlin, Android Gradle Plugin, JDK, SDK, dependencies, or build settings as a speculative fix.
3. Before a build/config change, record the branch and commit, the exact build failure or requirement, the relevant log/error, the hypothesis, the smallest intended change, and the verification plan.
4. Run the narrowest relevant Gradle task first. Then run the required build and tests appropriate to the change (for example, unit tests, lint/static checks, and the documented debug/release variant). Use only tasks and variants confirmed to exist in this repository.
5. Separate outcomes: compilation success is not test success; unit tests are not UI/end-to-end acceptance; APK creation is not proof the APK installs or works. Report each result independently with exact task, exit status, and CI/log link.
6. When an APK is required, verify the artifact exists, has plausible non-zero size, and corresponds to the tested commit/variant. If feasible, install it on the target emulator/device and run the relevant smoke/acceptance flow. Never call a build or release successful based only on an upload or green unrelated check.
7. Record environment blockers explicitly (JDK, Android SDK/platform/build-tools, Gradle, network, signing credentials, emulator/device). Do not invent secrets, print credentials, or place API keys/signing material in source control or logs.
8. If a build fails, preserve the first meaningful error and surrounding log; diagnose whether it is source, dependency/configuration, environment, test, packaging, or signing. Do not repeatedly rerun an unchanged failing build without new evidence or a justified environmental transient.
9. After a build-script, dependency, SDK, or toolchain change, run the affected build and relevant regression tests; compare the result with the prior attempt and append the result to `TEST_INVESTIGATION.md` (or the relevant durable build log).
10. Never claim "build fixed" without a successful build of the relevant variant. Never claim the app works without the relevant runtime verification.

## Every meaningful test/build attempt must be logged
Record:
- Date/time, branch and commit SHA, workflow/run/job URL, exact command/task/variant, and relevant environment versions.
- Exact PASS/FAIL/BLOCKED/UNVERIFIED outcome and the failing step/error text.
- Relevant logs, screenshots, UI hierarchy/accessibility dumps, APK artifacts, and links.
- What the attempt proves, what it does not prove, and how it differs from previous attempts.
- The next diagnostic/fix, with a reason based on the evidence.

Do not report a test as passing because the build passed, a script validated, or a related test passed. Report each layer separately. Keep failure records; do not overwrite history with only the latest result.

## Root-cause-first workflow
1. Reproduce the failure and inspect the actual logs/artifacts/screenshots and relevant code path.
2. Trace the failure to the responsible layer (source code, build configuration/toolchain, test harness, emulator/environment, platform API, app integration, backend, or data) before choosing a fix.
3. State the root cause as **confirmed**, **probable**, or **unknown**, and cite the evidence. Do not present a hypothesis as fact.
4. Make the smallest targeted change that addresses the supported cause.
5. Run the narrowest diagnostic test first, then relevant regression tests, then the full acceptance path.
6. Compare the new evidence with the previous attempt and update the durable investigation log.

## Do not loop
- Never repeat the same failed approach or make blind coordinate/selector/toolchain tweaks without a testable hypothesis.
- Before retrying, state what changed and why that change should alter the outcome.
- If a retry produces the same failure, do not repeat it again unchanged. Gather new evidence or switch to a materially different diagnostic.
- Do not call activity progress. A code change is not a fix until the relevant behavior is verified.

## Evidence and reporting
- Show the user the exact failure point and the most relevant screenshot/log/artifact when available.
- For UI failures, capture the state at failure and inspect the accessibility/UI hierarchy; distinguish a harness failure from an app/platform failure.
- Maintain a concise durable investigation record with: symptom, attempts, evidence, confirmed cause or open hypotheses, changes made, build/test outcomes, and next action.
- Report status explicitly as **PASS**, **FAIL**, **UNVERIFIED**, or **BLOCKED**, with the reason. Never claim a fix, build, test, or deployment succeeded without evidence.
- Keep user updates concise, direct, and action-oriented. Do not make the user repeatedly ask for status or repeat prior guidance.

## Change and merge safety
- Do not merge any PR or merge unrelated PRs without the user's explicit permission.
- Before proposing a merge, check acceptance criteria, required CI checks, relevant build variants, and regression/acceptance tests; report failures honestly.
- If blocked, explain the blocker and the specific evidence needed next instead of repeatedly trying the same thing.

## Current PadippuPal image-picker investigation
The latest recorded emulator smoke run failed before the app received a selected image URI: DocumentsUI remained on Downloads after the fixture row/thumbnail tap. The screenshot and XML show the filename/thumbnail nodes as non-clickable, while the separate preview control is clickable. This makes the test's selection interaction suspect, but does not by itself prove whether the picker, harness, or app is at fault. Root cause remains **UNKNOWN** until a materially different diagnostic isolates the layer. Do not repeat blind coordinate changes. Do not claim the image picker is fixed until the actual selection/URI return and downstream crop/rescan/save flow are verified.
