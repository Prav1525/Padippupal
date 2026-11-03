# Mandatory Agent Instructions for PadippuPal

**Before every code edit, test action, build action, build/configuration change, or deployment action, read `TESTING_GUIDANCE.md` in full and follow it.** This is a per-action requirement, not a one-time setup step. If a task spans multiple edits or sessions, re-open the guidance before each new batch of edits and whenever the investigation context changes.

## Required pre-action gate
Before touching code or starting a consequential build/test/deploy action, state in working notes (and in the user update when meaningful):
1. The relevant guidance being applied, including build-specific rules when applicable.
2. The current branch and commit.
3. The exact failure/requirement and latest evidence.
4. Whether the root cause is confirmed, probable, or unknown.
5. The specific action proposed and why it is justified by the evidence.
6. The diagnostic, build, regression, and acceptance checks that will verify it.

If the latest failure evidence, build environment, or project state is not available, retrieve it first. Do not guess or restart the investigation from scratch. Before selecting a build command, verify the repository's documented setup, wrapper, versions, and available tasks.

## Required post-action gate
After any change or meaningful build/test action:
1. Record changed files, commit SHA, exact command/task/variant, and environment versions where relevant.
2. Run the narrowest relevant check, then required build/regression/acceptance checks where possible.
3. Record exact outcomes and links to logs/artifacts/screenshots/APKs.
4. Compare results with previous attempts and append to the durable investigation log.
5. Tell the user what changed, what was tested or built, what failed or remains unverified, and the next evidence-based action.

Never claim success without verification. A successful compile does not prove tests passed; a generated APK does not prove runtime behaviour. Never repeat an unchanged failed approach. Never merge a PR without the user's explicit permission.

These requirements apply to all coding agents and human contributors. `TESTING_GUIDANCE.md` is the detailed source of truth.


## Persistent engineering memory
Before starting or resuming any PadippuPal task, read:
1. `PROJECT_CHARTER.md` and `PROJECT_STATUS.md`.
2. `.engineering/README.md` and the relevant architecture/module, decision, known-issue, and acceptance records.
3. `.engineering/tasks/active-work.md` to recover the single active objective.
4. The existing mandatory guidance above and, for tutor/UI work, `.github/testing-regression-checklist.md` plus `docs/TESTING_ERRORS.md`.

Reconcile dated documentation with actual branch heads, PRs, CI runs/artifacts, and deployed state before acting. Actual evidence outranks this snapshot. Update the status and active-work handoff with exact commit/run links at meaningful task boundaries. Do not merge PRs or make production changes without explicit founder approval.

## Closed-loop partner contract (mandatory)

The goal is verified task completion, not activity, plans, or repeated status messages. Apply this loop to every practical engineering request, including short follow-ups such as "proceed", "fix", "test", and "status".

### 1. Recover state before asking
- Read the project memory and relevant guidance above, then inspect the live repository, branch/PR state, latest workflow runs, and prior evidence for the active objective.
- Treat the active-work handoff as a pointer, not truth: reconcile it against current GitHub and runtime evidence.
- Do not ask the user to repeat context already present in repository records or this conversation. Ask only for a genuinely missing decision, access, or approval that blocks safe progress.

### 2. Define one verifiable outcome
Before acting, turn the request into explicit acceptance criteria for the actual requested product path: target feature/screen/data, expected behaviour, relevant regression checks, and evidence required to call it done.
- Test the named scenario, not a convenient or unrelated substitute. A generic smoke test may support general app health but cannot prove feature-specific acceptance.
- Preserve existing user-visible lesson content unless the request explicitly authorizes changing it.
- Choose the smallest evidence-supported next action. Do not create another document, workflow, agent, or abstraction when an existing mechanism can be corrected.

### 3. Execute a closed loop
For each distinct repair generation:
1. Inspect the latest failure and relevant source/logs/artifacts.
2. State the root-cause confidence internally as CONFIRMED, PROBABLE, or UNKNOWN; distinguish evidence from hypothesis.
3. Make one coherent, scoped change justified by that evidence.
4. Run the narrowest diagnostic, then relevant unit/regression checks, then the target acceptance path.
5. Inspect results and compare them with the previous attempt.
6. Update the append-only investigation record and active-work handoff with commit/run links, outcome, what it proves, what remains unverified, and the next action.
7. Continue to the next evidence-supported action without waiting for the user to say "proceed" again, unless a stop condition below applies.

A repair generation is one distinct code/configuration repair hypothesis and its verification, not each command or poll. Maximum: five distinct repair generations for the same failure chain. After five unsuccessful generations, stop automated repair and report the evidence, hypotheses exhausted, and exact decision/help needed. Never reset the count by changing branches, sessions, or task wording.
- Persist the count in the machine-readable repair-state block in `.engineering/tasks/active-work.md`. Before a repair, add its next sequential generation with the hypothesis; after verification, record the exact commit, run and outcome. The AutoPilot validator rejects malformed/non-sequential state, unapproved task chains, and a sixth generation. Carry the block unchanged when continuing the same failure chain on another branch; never start a fresh chain ID to evade the cap.

### 4. Treat tests as a proof ladder
Track each layer separately:
- STATIC / UNIT: source, script, and unit-level checks.
- BUILD: the exact relevant app/variant builds successfully.
- INTEGRATION: the real data/API contract and mappings work.
- RUNTIME / UI: the app reaches the intended screen and behaviour on device/emulator.
- ACCEPTANCE: the user's named criteria are visibly satisfied, with actual screenshots/logs and assertions.
- RELEASE: deployed state and live behaviour verified after separately authorized release actions.

A lower layer never implies a higher one. If a workflow fails before the target test starts, report the target test as NOT RUN, not FAIL or PASS. If a generic fixture or unrelated chapter is used, state that it is not feature-specific evidence. For UI work, inspect the actual screenshot and accessibility/UI hierarchy; a screenshot URL alone is not inspection. Never claim a screenshot was captured or inspected unless the artifact was retrieved and actually examined.

### 5. Keep working while asynchronous work runs
- When a workflow/build/test starts, retain its exact run/job identifiers and poll it to a terminal state when the available tools permit.
- While it runs, do useful read-only diagnosis or prepare a justified next step; do not start overlapping duplicate runs without a reason.
- On failure, fetch the failed step logs and artifacts before retrying. If logs are unavailable, identify that exact observability blocker and use another available evidence source rather than guessing.
- A workflow being "in progress" is not completion. Do not repeatedly send unchanged status updates; report meaningful state transitions and the next action.
- If tool permissions or capabilities prevent an action, state exactly which action is unavailable and what evidence or permission is missing. Never imply the action happened.

### 6. Hard stop and approval boundaries
Continue autonomously only within the user's approved scope and repository policy. Stop and request user input only when:
- an irreversible or externally visible action requires approval;
- requirements conflict or a material product decision cannot be inferred safely;
- required credentials, permissions, or a real-world choice are unavailable;
- five distinct repair generations are exhausted; or
- further action would risk data loss, learner impact, security, or production integrity.

Creating branches and reviewable PRs is allowed within the approved roadmap. **Never merge PRs, deploy production, mutate production databases, publish/release publicly, spend unapproved paid API budget, or weaken/remove required tests without explicit user approval.** Do not bypass a failing check to make a workflow green.

### 7. Definition of done and user communication
A task is DONE only when its stated acceptance criteria pass and the evidence is recorded. Otherwise use exactly one truthful state: IN PROGRESS, FAIL, UNVERIFIED, or BLOCKED.
- Every report should say: state; what changed; exact evidence; what that evidence proves; what remains; next action.
- Keep updates concise. Do not ask the user to request a test after implementation, ask for status while a known workflow is running, or declare success because a commit/PR/build exists.
- If the user asks "status", retrieve live state and report it. If the user says "fix and test", continue the loop. If they say "proceed", continue the already agreed objective rather than restarting discovery.
- Prefer fixing an existing broken mechanism over adding new process. If a policy is not technically enforced, explicitly label it as instruction-only or partially enforced; do not claim CI or branch protection guarantees it.
