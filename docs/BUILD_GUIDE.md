# PadippuPal Build Guide — Batch Implementation Workflow

This guide defines how to implement work efficiently without slowing down by treating every small issue as a separate build-and-test cycle. It is separate from product-partnership principles, UI design standards, and the testing error log.

## Default workflow: implement a coherent batch, then test it

**Default batch size: 5–10 related issues per implementation cycle.** Build them together, review the combined change, and then run the planned verification suite. Do not stop after every tiny issue to launch a full test cycle.

The batch size is a planning target, not a quota. A single high-risk change may need its own cycle; unrelated issues must not be bundled just to reach ten.

## 1. Define one coherent objective

Before editing:

- Read the relevant project protocol, this guide, the current acceptance criteria, `docs/TESTING_ERRORS.md`, and `.github/testing-regression-checklist.md` as applicable.
- Inspect the current branch, latest commit, working changes, existing implementation, and relevant tests.
- Choose one outcome that the batch will deliver (for example, “finish the tutor-screen layout and playback-state cleanup”).
- List 5–10 concrete issues/tasks that contribute directly to that outcome.
- Record dependencies, risks, files likely to change, and explicit acceptance criteria.
- Keep exactly one active implementation objective. The batch can contain several related issues, but not unrelated features or a second objective.

## 2. Implement the batch before starting the full test cycle

- Make the related changes in a deliberate sequence, keeping shared components and interfaces consistent.
- Inspect the surrounding code and existing behavior before changing it. Fix root causes; avoid speculative patches and repeated symptom-level fixes.
- Add or update regression tests as part of the implementation batch. Do not postpone thinking about test coverage until after coding.
- Keep a short internal checklist of each batch item and mark it implemented only when the code change is actually present.
- Do not launch a full build/test suite after each small edit. Finish the coherent batch, review the combined diff, and then begin verification.
- Do not bundle unrelated cleanup, broad refactors, or opportunistic redesign into the batch.
- If a critical dependency or security/data-integrity issue is discovered, stop and address it explicitly rather than hiding it inside the batch.

**Important:** “Batch first, test after” means one planned verification cycle after a coherent set of related implementation tasks—not skipping review, deleting tests, weakening assertions, or merging unverified work. Cheap code inspection and consistency checks while implementing are still expected.

## 3. Review the complete batch before testing

Before running tests:

- Review the complete diff against the batch list and acceptance criteria.
- Check for accidental unrelated changes, duplicate logic, inconsistent states, API contract drift, accessibility regressions, and missing failure handling.
- Confirm that tests cover the behavior changed and important regressions.
- Read `docs/TESTING_ERRORS.md` and `.github/testing-regression-checklist.md` before each test run. Treat previous incidents as required regression knowledge.
- Confirm the test plan and exact commit/branch being tested.

## 4. Verify in layers, then inspect the real experience

Run the appropriate checks in an efficient order, typically:

1. Focused unit/JVM/backend tests for changed behavior.
2. Full relevant backend and application test suites.
3. Debug APK build and compile/smoke-helper tests.
4. API/deployment checks when the feature depends on a deployed service.
5. Emulator or device end-to-end flow for user-visible behavior.
6. Fresh screenshots/logs/recordings from the exact tested commit; inspect them rather than merely checking that artifacts exist.

Use the repository regression checklist to determine the required layers. A passing build alone is not a release pass. Report each layer independently and identify the exact commit and workflow runs.

## 5. If the batch fails

- Classify the failure: product code, test assertion, harness, API/data, deployment drift, emulator/ADB, or timing.
- Preserve useful logs, XML, screenshots and other evidence.
- Find the root cause and add regression protection.
- Fix the issue, then rerun the failed layer and all downstream layers affected by the fix. Read the testing error log and checklist again before every new test run.
- Do not loosen assertions, skip a failing flow, or call the batch done because unrelated checks passed.
- Record meaningful new incidents in `docs/TESTING_ERRORS.md`, including symptom, root cause (or clearly labelled hypothesis), why it escaped, corrective action, regression protection, evidence, and status.

## 6. Completion report

For each batch, report:

- **Objective and scope:** the outcome and the 5–10 included tasks.
- **Implementation:** changed areas and commit/PR link.
- **Verification:** each required layer as Pass, Fail, Unverified, or Blocked, with evidence.
- **Acceptance:** which criteria passed and which remain open.
- **Next step:** one clear next objective.

Use these labels precisely: **Implemented** means code was changed; **Built** means the relevant build succeeded; **Tested** means the specified tests ran and passed; **Verified** means the relevant acceptance criteria—including real-device/UI checks where required—were confirmed. These labels are not interchangeable.

## 7. Batch sizing examples

**Good batch — one outcome, multiple connected tasks**
- Correct tutor header density.
- Remove redundant prompt and tap-to-pronounce affordance.
- Correct active-segment layout.
- Eliminate faded future-text preview.
- Make loading/speaking/paused states truthful.
- Keep checkpoint actions pinned above system navigation.
- Preserve pause, stop, back navigation, and student input.
- Add regression tests for the affected states.
- Review live-lesson and checkpoint screenshots.

These form one tutor-screen quality batch; implement the related changes before running the planned test suite.

**Bad batch — unrelated work**
- Change tutor layout.
- Replace the AI provider.
- Redesign onboarding.
- Add PDF export.
- Update database schema.

Split these into separate objectives because they have different risks, acceptance criteria, and verification needs.

## Non-negotiable release rule

Batching reduces process overhead; it does not lower the quality bar. Do not merge the tutor-fix PR until its stated acceptance criteria and required regression checks pass. Do not merge separate process/automation PRs without explicit approval.
