# PadippuPal Regression Checklist

This is a living record. Add a named regression case for every confirmed recurring bug. Do not mark a case passed without fresh evidence tied to a commit.

## Global release/task checks

- [ ] Confirm the expected branch and commit SHA before testing.
- [ ] Run targeted unit/backend tests for changed logic.
- [ ] Run relevant integration tests for data/API/UI contracts.
- [ ] Build the Android app when Android code/configuration is affected.
- [ ] Run emulator/user-flow tests for user-visible tutor changes.
- [ ] Re-run previously failing tests after the fix; inspect logs/screens/accessibility hierarchy rather than relying only on exit code.
- [ ] Confirm tests did not pass because assertions were weakened, scenarios skipped, or errors swallowed.
- [ ] Review final diff for unrelated changes, debug leftovers, unsafe fallback behavior, and altered expectations.
- [ ] Record exact commit SHA and run links.

## Tutor lesson content / animation coordination

### PP-TUTOR-001 — Selected topic must own the lesson content

- **Priority:** P0 for tutor correctness.
- **Known regression:** Class 6 CBSE Mathematics → Patterns in Mathematics → All 1s displayed an unrelated explanation about adding counting numbers up and then down.
- **Expected:** every displayed/spoken segment belongs to the selected approved topic; missing topic content fails closed with a clear explanation rather than substituting a different topic.
- **Negative assertions:** while All 1s is selected, reject unrelated content such as counting-up/down explanation, `1 + 2 + 1 = 4`, or square-number progression unless the approved All 1s source explicitly requires it.
- **Positive assertions:** the explanation accurately describes `1, 1, 1, 1, 1`, the value remaining the same, and the rule of repeating 1, consistent with the approved lesson data.
- **Required coverage:** backend/unit contract and Android end-to-end UI smoke; inspect the actual rendered lesson and accessibility text, not just the topic label.
- **Confirmed cause (2026-10-22):** the live lesson-plan retrieval query included the long teacher-instruction message and considered only the top five keyword-scored chunks. The approved source database has the All 1s sequence in the page-3 chunk, while page 7 contains the unrelated “adding the counting numbers up and then down” explanation. No reviewed topic-specific `chapter_lessons` row exists for this exact profile/topic, so the Gemini retrieval fallback was allowed to mix neighbouring chapter concepts.
- **Code correction in PR #13:** query using the selected topic/chapter rather than the long instruction prompt; consider up to ten candidate chunks; retain only passages matching the selected topic; retry one semantically off-topic All 1s generation; reject and fail closed if it remains off-topic. The implementation is committed but end-to-end acceptance is still pending.
- **Status:** OPEN until fresh tests on the latest code head pass and the full live teaching flow is verified against the corrected backend.

### PP-TUTOR-002 — Animation and narration must stay synchronized

- **Expected:** the visible animation/action, spoken sentence, inline word highlight, and checkpoint all refer to the same current lesson segment.
- **Checks:** segment transitions update caption, animation state, highlight position and checkpoint coherently; no stale visual from a prior segment.
- **Status:** OPEN until end-to-end evidence confirms.

### PP-TUTOR-003 — Understand checkpoint gates continuation

- **Expected:** after a segment, the app presents the understand / explain again / ask a question choices in the agreed lower-screen area; the next segment does not advance before the student response.
- **Checks:** selecting understand dismisses the checkpoint and advances exactly once; explain again replays the same segment; question path accepts the student's question without accidentally advancing.
- **Status:** Revalidate.

### PP-TUTOR-004 — Inline word highlighting and scroll behavior

- **Expected:** spoken words highlight inside the same displayed lesson text, not in a separate duplicate overlay; highlight advances with speech and content scrolls when needed.
- **Checks:** accessibility/text hierarchy shows one primary lesson text; screenshot/frame evidence confirms the highlight is on that text and moves during playback; longer segments remain readable.
- **Status:** Revalidate.

### PP-TUTOR-005 — Chapter/topic selection remains deterministic

- **Expected:** selecting Mathematics, Patterns in Mathematics, and All 1s resolves to the intended identifiers regardless of previous saved UI state.
- **Checks:** clean-state and returning-user paths both work; picker controls remain discoverable when showing selected values; tests reset state deliberately rather than loosening assertions to accept ambiguous UI.
- **Status:** Revalidate.

## Test reliability / environment

### PP-TEST-001 — Classify failure before patching

For every failure, collect workflow URL, job/step, failing assertion or stack trace, branch/head SHA, and whether it reproduces. Classify as product defect, test defect, or environment defect before changing code.

### PP-TEST-002 — Stable emulator setup

Record Android/emulator version, app install/reset strategy, permissions, seeded data, and deterministic setup. Prefer a known clean state for picker/navigation tests while separately testing persistence. Do not rely on an undocumented saved emulator state.

### PP-TEST-003 — Repeat-failure protocol

If a regression returns:
1. Compare the last passing and first failing commit.
2. Check whether the prior fix is present in the actual tested branch/build.
3. Inspect alternative code paths, stale persisted state, asynchronous races, and test setup.
4. Add or repair a regression test that reproduces the underlying cause.
5. Do not apply another patch until evidence supports the cause.

## How to record a new case

Add ID, severity, observed failure, expected behavior, evidence, confirmed cause, required test layer, current status, and last passing commit. Keep unresolved causes explicitly marked as unknown.
