# PadippuPal — test and build execution standard

This file contains **test/build-specific rules only**. The integrated agent's behavior, context recovery, work selection, repair loop, escalation and approval policy are defined once in `AGENTS.md`. The sole trigger is `docs/AUTOPILOT_TRIGGER_PROMPT.md`.

`AGENTS.md` requires this file to be re-opened before every code/configuration edit and every test/build/deployment action. Apply the relevant rules below.

## Build environment and command selection

1. Read the repository README build instructions and inspect the actual Gradle wrapper, Gradle/plugin versions, JDK, Android SDK requirements, build variants and CI workflow before choosing a build command.
2. Prefer the repository's Gradle wrapper when present. If absent, use the documented CI/build setup and record the exact Gradle version. Never assume a task or variant exists; verify it first.
3. Do not speculatively upgrade Gradle, Kotlin, Android Gradle Plugin, JDK, SDK, dependencies or build settings.
4. Before a build/configuration change, record the branch and SHA, exact failure/requirement, relevant log, hypothesis, smallest intended change and verification plan.
5. Run the narrowest relevant task first, then required unit, lint/static, backend/curriculum and app build checks appropriate to the change.
6. Verify APK artifacts exist, are non-empty and correspond to the exact tested SHA and variant. When runtime behavior matters, install/run the artifact on the target emulator/device.

## Test selection and acceptance

1. Derive tests from the changed boundary and the user's actual acceptance criteria. Test the named screen, chapter, data and behavior—not a convenient substitute.
2. Keep test layers separate: static/unit, build, integration/API/data, runtime/UI, user acceptance and release verification.
3. A lower layer never proves a higher one. Compilation is not test success; APK creation is not runtime success; generic UI smoke is not feature-specific acceptance.
4. If a workflow fails before the target test starts, mark that test **NOT RUN**. If the wrong fixture, chapter or data is used, it is not feature-specific evidence.
5. For UI acceptance, capture the actual target screen and UI/accessibility hierarchy. Retrieve and inspect screenshots; a screenshot URL or artifact name alone is not proof.
6. Do not weaken assertions, skip required checks, substitute unrelated tests or suppress failures to obtain a green run.

## Evidence record for every meaningful attempt

Append to the existing investigation record:
- Date/time, branch, exact commit SHA, workflow/run/attempt/job URL.
- Exact command/task/variant and relevant environment versions.
- PASS / FAIL / BLOCKED / NOT RUN / UNVERIFIED, including the first meaningful error.
- Links to logs, screenshots, UI hierarchy, APKs and other artifacts.
- What the result proves and does not prove; how it differs from the previous attempt.
- One evidence-based next diagnostic or action.

Keep prior failures and attempts; do not overwrite history with only the latest result.

## Failure diagnosis

1. Reproduce and inspect the actual failing logs, artifacts, screenshots and relevant code path.
2. Identify whether the failure is source, test harness, build/toolchain, emulator/environment, dependency/network, API/integration or data related.
3. Label root cause **CONFIRMED**, **PROBABLE** or **UNKNOWN** and cite evidence.
4. Make the smallest targeted change, run the narrow diagnostic, then relevant regression tests and the target acceptance path.
5. Never repeat an unchanged failed approach. A retry requires new evidence or a justified transient-infrastructure reason.

## Current image-picker investigation

The latest recorded emulator smoke failed before the app received a selected image URI: DocumentsUI remained on Downloads after the fixture row/thumbnail tap. The screenshot and XML show the filename/thumbnail nodes as non-clickable, while a separate preview control is clickable. This makes the selection interaction suspect but does not prove whether the picker, harness or app is at fault. Root cause remains **UNKNOWN**. Do not repeat blind coordinate changes; verify actual selection/URI return and downstream crop/rescan/save flow before claiming resolution.
