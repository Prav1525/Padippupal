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
- **Status:** OPEN — code fix committed on PR #13 at `0f648fe9159a9ac856d5b780c29fbb4820b9eb16`; fresh Android UI smoke is pending. Close only after the test proves at least two distinct inline highlight positions during speech.

### PP-TUTOR-005 — Chapter/topic selection remains deterministic

- **Expected:** selecting Mathematics, Patterns in Mathematics, and All 1s resolves to the intended identifiers regardless of previous saved UI state.
- **Checks:** clean-state and returning-user paths both work; picker controls remain discoverable when showing selected values; tests reset state deliberately rather than loosening assertions to accept ambiguous UI.
- **Status:** Revalidate.

## Test reliability / environment

### PP-TEST-001 — Classify failure before patching

For every failure, collect workflow URL, job/step, failing assertion or stack trace, branch/head SHA, and whether it reproduces. Classify as product defect, test defect, or environment defect before changing code.

### PP-TEST-002 — Stable emulator setup

Record Android/emulator version, app install/reset strategy, permissions, seeded data, and deterministic setup. Prefer a known clean state for picker/navigation tests while separately testing persistence. Do not rely on an undocumented saved emulator state.

- **Confirmed recurring fixture defect (2026-10-22):** the smoke script removed `padippupal_profile.xml` but left `padippupal_tutor_sessions.xml`. TutorScreen restores same-day subject/chapter/topic from the latter, so the test could see `Patterns in Mathematics` / `All 1s` where it expected the empty-state `Choose chapter` / `Choose concept` labels.
- **Correction in PR #13 head `159dc8c9902e992b53e55388303ab9f8d18d00eb`:** reset both preference files before seeding the CBSE profile; helper regression test verifies both resets happen before profile setup.
- **Status:** UNVERIFIED until fresh emulator smoke on that commit proves the clean selection path succeeds. Do not loosen selector assertions to accept stale state.

### PP-TEST-003 — Repeat-failure protocol

If a regression returns:
1. Compare the last passing and first failing commit.
2. Check whether the prior fix is present in the actual tested branch/build.
3. Inspect alternative code paths, stale persisted state, asynchronous races, and test setup.
4. Add or repair a regression test that reproduces the underlying cause.
5. Do not apply another patch until evidence supports the cause.

## How to record a new case

Add ID, severity, observed failure, expected behavior, evidence, confirmed cause, required test layer, current status, and last passing commit. Keep unresolved causes explicitly marked as unknown.


### PP-TEST-004 — Bounded CI auto-repair loop

- **Expected:** a failed eligible same-repository CI run produces a triage report with the exact run URL/SHA; when the optional repair credential is configured, one evidence-based repair proposal is tested and opened as a PR; relevant CI is dispatched against the proposal.
- **Negative checks:** no code changes when no safe patch is supported; no fork-controlled code is passed to the agent; no automatic merge/deploy; no infinite repair loop; no test assertions are weakened.
- **Credential/cost:** `OPENAI_API_KEY` is required for the agent stage and can incur separately billed API usage. Without it, the repair stage must skip cleanly.
- **Verification:** GitHub parsed the new `Bounded CI auto-repair` workflow on PR #15 head `de9f137802123bd62dfe5490acad2656fcdb2550`; its jobs skipped on the pull-request event as intended. A controlled injected-failure test has not run, so the end-to-end automation remains **UNVERIFIED**.
- **Status:** OPEN until the default-branch workflow is active, credential setup is explicitly accepted/configured, and a controlled failure demonstrates repair proposal plus retesting.


### PP-TUTOR-004 — Understanding checkpoint advances the lesson

- **Priority:** P1 live-tutor flow correctness.
- **Expected:** after a segment ends at a checkpoint, selecting **I understand** hides the checkpoint and starts the next segment; the progress indicator advances (e.g. 2/5 → 3/5). The lesson must remain live and the concept-matched animation/highlighting must continue.
- **Observed on commit `159dc8c9902e992b53e55388303ab9f8d18d00eb`:** UI smoke found the checkpoint, visible repeated-ones animation, 2 distinct inline-highlight positions across 35 frames, and working pause/resume; after tapping **I understand**, the checkpoint remained visible and segment 3/5 did not appear within 30 seconds. Evidence: [UI run 39731013247](https://github.com/Prav1525/Padippupal/actions/runs/39731013247).
- **Patch under verification:** commit `5051b68715ea01cd5cea9bef6550fed6aff863ee` clears checkpoint state synchronously and schedules the next segment on the main handler without the previous 350 ms delay.
- **Status:** UNVERIFIED until fresh emulator CI proves the progress indicator advances and checkpoint controls disappear. Do not infer success from a build-only pass.


### PP-TUTOR-006 — Empty speech or unavailable TTS must not skip lesson segments

- **Priority:** P0 for a trustworthy live teaching flow.
- **Expected:** every playable segment has nonblank spoken text. If the generated segment is empty, the backend retries generation and rejects the lesson if it cannot produce valid speech. If hosted speech and device TTS are both unavailable, the live lesson pauses with a recovery message; it must not treat missing audio as completed teaching or auto-advance.
- **Confirmed failure evidence:** UI run [39732280667](https://github.com/Prav1525/Padippupal/actions/runs/39732280667) showed a no-compatible-English-voice state in one attempt. Another attempt reached checkpoint 2/5 but later showed 4/5 after “I understand”, consistent with the Android blank-segment path recursively skipping index 2.
- **Code correction in PR #13 at `4998d55e6f243879a0b7bdbd31b6e1af1175261b`:** backend `_validate_lesson_plan` rejects blank `spoken_text`, triggering the existing single retry; regression test covers a blank first response and valid second response. Android pauses on missing device locale and TTS utterance errors instead of calling completion. The smoke test polls more frequently for the 3/5 transition.
- **Verification:** backend tests PASS (44 tests; [run 39735164521](https://github.com/Prav1525/Padippupal/actions/runs/39735164521)); Android APK build PASS ([run 39735164510](https://github.com/Prav1525/Padippupal/actions/runs/39735164510)); emulator UI smoke remains IN PROGRESS ([run 39735164537](https://github.com/Prav1525/Padippupal/actions/runs/39735164537)). Do not close until fresh UI evidence confirms narration/highlighting, pause/resume, and checkpoint continuation.


### PP-TUTOR-006 — Speech fallback must preserve truthful playback state

- **Expected:** the tutor tries the configured hosted speech provider, falls back to a compatible installed device voice when hosted speech is unavailable, and never advances a lesson segment as if audio played when no voice started.
- **Checks:** hosted TTS 503/provider failures are observable in backend logs; device locale selection includes installed English variants (including British English) and the requested Tamil locale; if no compatible voice exists, the lesson pauses with a recoverable message and does not silently skip content.
- **Current evidence (2026-10-22):** Render logs show Gemini TTS HTTP 429 followed by Sarvam HTTP 402, producing `POST /tutor/speech` 503. The CI emulator then reported no compatible English TTS voice. This is a confirmed provider-quota/emulator-voice blocker; target-phone voice behavior remains UNVERIFIED.
- **Status:** OPEN. Latest locale compatibility change is commit `6c711eeed23087d4caa8ab9db6fe882c8e2f4aec`; await its build and emulator results.


- **Follow-up test harness change (2026-10-22):** latest PR #13 head `8fe4a4b35cef0acaca18c1d6fa1c7cc83bcd9ca1` switches the UI emulator to `google_apis_playstore` and detects explicit no-voice errors during checkpoint polling. This improves the test environment and shortens known failure diagnosis without skipping the speech/checkpoint assertions. Latest curriculum tests passed; APK/UI smoke were pending at handoff.


### PP-TUTOR-007 — Screenshot regression checks must remain performant

- **Expected:** screenshot assertions detect exact highlight colors and movement without spending minutes on Python-level full-screen pixel scans.
- **Checks:** synthetic-image test verifies exact RGB mask count/bounds; the UI smoke must still detect at least two distinct highlight positions and verify the teaching panel layout.
- **Correction:** PR #13 head `01cbd5185a531c7c0ce220438d4603f0be8a3a92` uses Pillow masks/bounding boxes and adds a synthetic mask regression test.
- **Status:** Code/build and curriculum tests PASS; UI smoke `39737297301` was still running at last check.


### PP-TUTOR-008 — Speech completion must not strand live lessons

- **Expected:** after a spoken segment actually ends, the tutor advances to the next segment or presents its understanding checkpoint; pause must not be mistaken for completion.
- **Regression evidence:** UI smoke `39737297301` showed the correct All 1s lesson, 13 distinct inline highlight positions, and pause/resume passing, but the lesson remained at 1/5 for 150 seconds after resume.
- **Correction under test:** PR #13 head `73a930a6a4be661c6413690dd387380774c67f0c` adds a per-utterance completion watchdog that recovers only after playback has been observed and then stopped, respects paused state, and checks MediaPlayer position before recovery.
- **Status:** OPEN / UNVERIFIED. Android APK build PASS (run `39739236650`); curriculum tests PASS (`39739236589`); UI smoke `39739236756` was still running at last poll. Do not mark passed unless the checkpoint appears and “I understand” advances 2/5 → 3/5.


### PP-TUTOR-009 — Live lesson smoke checks use the real accessible progress labels

- **Expected:** the smoke test identifies the active lesson using progress/content actually rendered by the app; it must not require a nonexistent literal such as `teacher is speaking`.
- **Guardrail:** correcting a stale label assertion must not bypass the independent inline-highlight movement, playback pause/resume, visible voice-error, concept-animation, understanding-checkpoint, or 2/5 → 3/5 continuation assertions.
- **Confirmed cause:** at PR #13 head `73a930a6a4be661c6413690dd387380774c67f0c`, the emulator accessibility tree showed `LIVE`, `1 / 5`, the inline lesson caption, and the All 1s animation, but not `teacher is speaking`. The stale assertion aborted the smoke before the later acceptance checks ran.
- **Correction:** PR #13 head `8d6e9304ed459a4efeb29b434dd72cf6eeef06b1` now validates the real progress label and recognizable lesson text while preserving downstream checks.
- **Verification:** Android APK PASS (run [39741609797](https://github.com/Prav1525/Padippupal/actions/runs/39741609797)); curriculum tests PASS (run [39741609927](https://github.com/Prav1525/Padippupal/actions/runs/39741609927)); UI smoke [39741609782](https://github.com/Prav1525/Padippupal/actions/runs/39741609782) was still in progress at last check. Speech/checkpoint behavior remains OPEN until fresh emulator evidence passes.
