# Test Investigation Ledger

> Append a new entry for each meaningful test attempt or code-change investigation. Do not delete or rewrite older entries; correct mistakes by adding a dated correction. Follow `AGENTS.md` and `TESTING_GUIDANCE.md`.

## Current status
- **Area:** Diary image picker selection
- **Status:** FAIL
- **Root cause:** UNKNOWN
- **Last known evidence:** GitHub Actions run [40207402376](https://github.com/Prav1525/Padippupal/actions/runs/40207402376); job 121213999919; artifact [12605182220](https://github.com/Prav1525/Padippupal/actions/runs/40207402376/artifacts/12605182220).
- **Observed failure:** DocumentsUI stayed on Downloads after the fixture row/thumbnail tap; the app did not receive a selected image URI.
- **Interpretation:** Screenshot/XML indicate filename and thumbnail nodes are non-clickable and a separate preview control is clickable. This makes the test interaction suspect but does not establish whether the harness, picker, or app is the root cause.
- **Next action:** Use a materially different diagnostic to isolate picker selection from downstream image decoding/crop/rescan/save. Do not repeat blind coordinate changes.

## Append-only attempt log

### 2026-10-25 — Latest known picker smoke attempt
- **Branch:** `fix/diary-image-picker-reliability`
- **Commit under test:** `ba200e9e419210355a16fc9d66e1af4025f3b765`
- **Result:** **FAIL**
- **Exact failure:** `FAIL: file selection did not return from DocumentsUI after row tap and any visible confirmation; inspect diary-picker-selection-result.xml and picker-selection-stuck.png`
- **Evidence:** [Workflow run](https://github.com/Prav1525/Padippupal/actions/runs/40207402376), [artifact](https://github.com/Prav1525/Padippupal/actions/runs/40207402376/artifacts/12605182220).
- **What it proves:** The current smoke path does not complete the selection interaction.
- **What it does not prove:** It does not prove the app URI callback, bitmap decoding, backend scan, crop, or save flow is broken; those steps were not reached.
- **Root cause confidence:** **UNKNOWN**.
- **Next action:** Stop coordinate-only retries; introduce an independent diagnostic for Android URI return and a separate deterministic test of the app's image-processing path.

## New entries (append below; never remove prior attempts)

Use this format:

### YYYY-MM-DD — Short test/change description
- **Branch / commit:**
- **Test command or workflow URL:**
- **Result:** PASS / FAIL / BLOCKED / UNVERIFIED
- **Exact failure or assertion:**
- **Evidence links (logs/screenshots/XML/artifacts):**
- **Change made (files + rationale):**
- **Root cause:** CONFIRMED / PROBABLE / UNKNOWN — evidence:
- **What this attempt proves:**
- **What remains unverified:**
- **Difference from previous attempt:**
- **Next action and why:**


### 2026-10-25 — Add repository guidance gate and append-only ledger
- **Branch / commit:** `fix/diary-image-picker-reliability`; guidance/gate commits `7e0b5848`, `1d5f316e`, `4bcfec55`, `ed09111f`, `7ba36e04`, `b6ecc74c`, `d0480328`.
- **Test command or workflow URL:** GitHub Actions workflow `Investigation Guidance Gate` added at `.github/workflows/investigation-guidance.yml`; execution result not yet available.
- **Result:** **UNVERIFIED**
- **Exact failure or assertion:** No workflow run has yet verified that the new gate executes correctly.
- **Evidence links (logs/screenshots/XML/artifacts):** [Guidance gate workflow file](https://github.com/Prav1525/Padippupal/blob/fix/diary-image-picker-reliability/.github/workflows/investigation-guidance.yml); [validator](https://github.com/Prav1525/Padippupal/blob/fix/diary-image-picker-reliability/.github/scripts/validate_investigation_ledger.py); prior picker failure [run 40207402376](https://github.com/Prav1525/Padippupal/actions/runs/40207402376).
- **Change made (files + rationale):** Added `AGENTS.md`, `TESTING_GUIDANCE.md`, `TEST_INVESTIGATION.md`, PR checklist, a ledger validator, and a pull-request workflow. Validator was tightened to reject a template placeholder as a real entry.
- **Root cause:** UNKNOWN for the original picker issue; this documentation/automation change is a process safeguard, not a picker fix.
- **What this attempt proves:** The instructions, ledger, validator, and workflow have been committed to the feature branch.
- **What remains unverified:** The workflow has not run; required branch protection is not confirmed; automated checks cannot validate whether a diagnosis is truthful or reasoning was actually performed.
- **Difference from previous attempt:** Moves from instructions alone to an automated PR check and a persistent investigation ledger.
- **Next action and why:** Trigger/observe the GitHub Actions gate and fix any workflow/validator issues; then configure the gate as a required status check in repository branch protection if permissions allow.

### 2026-10-25 — Add mandatory build guidance
- **Branch / commit:** `fix/diary-image-picker-reliability`; guidance updates `cb70d1311f1ca657ee990b9beae9b555dd64c919` and `6aa2eb7f3216944dcecd76b7ca0ab4fbb34a57ae`.
- **Test command or workflow URL:** Documentation-only change; no Android build or CI workflow was run as part of this update.
- **Result:** **UNVERIFIED** for the overall gate; documentation commits succeeded.
- **Exact failure or assertion:** None from a build attempt; the guidance gate's CI execution remains unverified as recorded above.
- **Evidence links:** [Updated testing/build guidance](https://github.com/Prav1525/Padippupal/blob/fix/diary-image-picker-reliability/TESTING_GUIDANCE.md); [updated agent instructions](https://github.com/Prav1525/Padippupal/blob/fix/diary-image-picker-reliability/AGENTS.md).
- **Change made (files + rationale):** Added build-tool/version discovery, wrapper preference, task/variant verification, staged build and test requirements, APK verification, environment-blocker handling, secret safety, and explicit separation of compile/build/runtime acceptance. Updated `AGENTS.md` so build actions are included in the pre-action gate.
- **Root cause:** Not applicable to picker failure; picker root cause remains UNKNOWN.
- **What this attempt proves:** The build guidance is committed to the feature branch.
- **What remains unverified:** No build was run; the repository guidance workflow was not triggered/verified here; this does not technically intercept every ChatGPT GitHub tool call.
- **Difference from previous attempt:** Build and packaging actions are now explicitly covered rather than being implied by testing guidance.
- **Next action and why:** Verify the guidance workflow on a PR and inspect/configure required branch protection if permissions allow. Do not merge without explicit user permission.


### 2026-10-25 — Fix validator date/field regex escaping
- **Branch / commit:** `fix/diary-image-picker-reliability`; validator fix commit `0e0e024d09306c6d49e569e8c16755c27650fd97`.
- **Test command or workflow URL:** Static inspection of `.github/scripts/validate_investigation_ledger.py`; automated PR workflow execution pending.
- **Result:** **UNVERIFIED** for CI enforcement; validator source corrected, but no workflow result has yet confirmed it.
- **Exact failure or assertion:** The validator used doubled backslashes inside raw regex strings, so date and Markdown-field patterns did not match the intended ledger format reliably.
- **Evidence links (logs/screenshots/XML/artifacts):** [Validator](https://github.com/Prav1525/Padippupal/blob/fix/diary-image-picker-reliability/.github/scripts/validate_investigation_ledger.py); [guidance workflow](https://github.com/Prav1525/Padippupal/blob/fix/diary-image-picker-reliability/.github/workflows/investigation-guidance.yml).
- **Change made (files + rationale):** Corrected raw regex escapes for dates, newlines, Markdown bold markers, end-of-input, and word boundaries so the intended dated-entry validation can operate.
- **Root cause:** **CONFIRMED** for this validator defect by inspection of the regex literals; unrelated to the original picker failure.
- **What this attempt proves:** The committed regex patterns now express the intended matching syntax.
- **What remains unverified:** Workflow run, status-check requirement, branch protection, and whether the integration can configure repository rules.
- **Difference from previous attempt:** Fixes the validator itself rather than only adding process instructions.
- **Next action and why:** Let the PR workflow execute on the new commit and inspect its result; then ask the repository owner to require the status check if admin-level settings are unavailable.


### 2026-10-25 — Change picker smoke tap from thumbnail to filename row
- **Branch / commit:** `fix/diary-image-picker-reliability`; helper commit `50f0622bf04c71836f439941483d9b3d2e93efdd`; regression-test commit `4406f11f9b163f25a3f7444db5f551ec5e107723`.
- **Test command or workflow URL:** Pending exact-head CI after these commits.
- **Result:** **UNVERIFIED** — change committed; automated regression and emulator acceptance have not run on this exact head yet.
- **Exact failure or assertion:** Previous run [40207402376](https://github.com/Prav1525/Padippupal/actions/runs/40207402376) tapped thumbnail center `(94,735)` and remained in DocumentsUI for all eight checks; log says `Single-tapping DocumentsUI thumbnail ...`.
- **Evidence links (logs/screenshots/XML/artifacts):** [Failed run](https://github.com/Prav1525/Padippupal/actions/runs/40207402376), [failure artifact](https://github.com/Prav1525/Padippupal/actions/runs/40207402376/artifacts/12605182220).
- **Change made (files + rationale):** `.github/scripts/ui_smoke.py` now taps the filename node's own center rather than selecting the non-clickable thumbnail; `.github/scripts/test_diary_emulator_script.py` now asserts the filename-row coordinates `(424,713)` for the exact previously observed XML and rejects the old thumbnail-selection strategy.
- **Root cause:** **PROBABLE, not confirmed** — the failing action is demonstrably tapping a non-clickable thumbnail; filename-row tap is a distinct, evidence-led interaction, but only a fresh emulator run can establish whether it selects the URI.
- **What this attempt proves:** A concrete test-harness defect was identified and the selector plus its regression expectation were changed.
- **What remains unverified:** Unit/static regression checks, DocumentsUI return, content-URI receipt, crop/rescan, date isolation, save-to-planner, and runtime behavior.
- **Difference from previous attempt:** Changes the target from thumbnail center `(94,735)` to filename-row center `(424,713)`; no repeated coordinate retry on the same target.
- **Next action and why:** Run exact-head script/JVM/APK/emulator checks; inspect the new picker screenshot/XML if the filename-row tap still fails and then switch to a URI-level diagnostic rather than another blind tap.


### 2026-10-25 — Correct smoke-script regression assertions to match subprocess API
- **Branch / commit:** `fix/diary-image-picker-reliability`; test correction commit `98775487373b047b81de3f3c258780787caad022`.
- **Test command or workflow URL:** Prior exact-head validation [run 40212740440](https://github.com/Prav1525/Padippupal/actions/runs/40212740440), job 121227295458; corrected commit's CI run pending.
- **Result:** **FAIL** on prior head; corrected assertions **UNVERIFIED** pending CI.
- **Exact failure or assertion:** Three Python regression tests failed before emulator allocation. Two expected a single argv string `"input tap 185 140"` / `"input tap 424 713"`, but implementation correctly invokes subprocess with separate argv entries `"input", "tap", "185", "140"` / `"input", "tap", "424", "713"`. The third asserted for a shell-command string `f"input tap {x} {y}"` not used by the implementation.
- **Evidence links:** [Failed workflow](https://github.com/Prav1525/Padippupal/actions/runs/40212740440); test failure output in emulator-smoke job 121227295458.
- **Change made (files + rationale):** `.github/scripts/test_diary_emulator_script.py` now asserts the actual subprocess argv structure. This fixes a test-harness assertion mismatch; it does not change picker behavior or claim the selector is correct.
- **Root cause:** **CONFIRMED** for the three script-validation failures by comparing exact assertion output with the implementation's subprocess argv. Root cause of the original DocumentsUI selection failure remains **UNKNOWN**.
- **What this attempt proves:** The prior CI was blocked by three self-test assertions incompatible with the helper's actual command construction; APK build and JVM tests had passed in that run.
- **What remains unverified:** Corrected script tests, emulator selection, URI return, crop/rescan, and save flow.
- **Difference from previous attempt:** Corrects assertions to inspect tokenized subprocess arguments rather than changing tap coordinates or selection strategy.
- **Next action and why:** Inspect CI on the corrected commit. If script validation passes, use the resulting emulator XML/screenshot and selection-return evidence to isolate the original picker failure; do not call the picker fixed based on unit/script validation alone.


### 2026-10-25 — Stop non-clickable filename tap; isolate actual picker selection
- **Branch / commit:** `fix/diary-image-picker-reliability`; latest observed CI head `e44dd6ae82b350b06114aa28fa63dc8e2908bac7`. Guidance re-read before this investigation: `AGENTS.md` and `TESTING_GUIDANCE.md`.
- **Test command or workflow URL:** Latest Android UI smoke runs [40212992310](https://github.com/Prav1525/Padippupal/actions/runs/40212992310) and [40212988861](https://github.com/Prav1525/Padippupal/actions/runs/40212988861); failed run artifact [12606607030](https://github.com/Prav1525/Padippupal/actions/runs/40212992310/artifacts/12606607030).
- **Result:** **FAIL** for emulator picker selection; **PASS** for Android APK build [40212992380](https://github.com/Prav1525/Padippupal/actions/runs/40212992380), curriculum tests [40212992366](https://github.com/Prav1525/Padippupal/actions/runs/40212992366), and guidance gate [40212992351](https://github.com/Prav1525/Padippupal/actions/runs/40212992351).
- **Exact failure or assertion:** `FAIL: file selection did not return from DocumentsUI after row tap and any visible confirmation; inspect diary-picker-selection-result.xml and picker-selection-stuck.png`.
- **Evidence links (logs/screenshots/XML/artifacts):** [failed UI run](https://github.com/Prav1525/Padippupal/actions/runs/40212992310); [emulator evidence artifact](https://github.com/Prav1525/Padippupal/actions/runs/40212992310/artifacts/12606607030); prior failed attempt [40207402376](https://github.com/Prav1525/Padippupal/actions/runs/40207402376).
- **Change made (files + rationale):** No app or test code changed in this investigation entry. The previous filename-center tap at `(424,713)` is explicitly not accepted as a fix because the captured XML reports the filename node and parent row as `clickable=false`; only the separate preview control is marked clickable. This entry records the evidence and prevents repeating the same non-clickable target.
- **Root cause:** **UNKNOWN** for the end-to-end picker failure. **CONFIRMED** that the most recent test tap targets a node reported non-clickable by the captured accessibility hierarchy; this confirms the interaction is not justified, but does not establish whether the preview route, picker intent, fixture setup, or app callback is the underlying issue.
- **What this attempt proves:** On the tested commit, the emulator test remains in DocumentsUI and no successful URI-return event is demonstrated. The build and unrelated tests passing do not prove picker runtime behavior.
- **What remains unverified:** What tapping the clickable preview control does; whether DocumentsUI exposes a genuine selection/open action after that; whether Android returns a content URI to PadippuPal; and crop/rescan/save behavior.
- **Difference from previous attempt:** Stops repeating the earlier thumbnail tap and the subsequent filename-label tap. The next diagnostic must observe the preview interaction and inspect picker-launch implementation before changing selectors or coordinates.
- **Next action and why:** Inspect the diary picker launch code, intent/action and result callback, plus the smoke workflow fixture setup. Then make one evidence-based diagnostic that captures UI hierarchy/screenshot immediately after tapping the clickable preview control and explicitly checks for activity return/URI receipt. Follow with crop/rescan/save acceptance only after URI return is confirmed. Do not change coordinates blindly, and do not mark the picker fixed until the full path passes.


### 2026-10-25 — Focus and keyboard-activate the DocumentsUI row
- **Branch / commit:** `fix/diary-image-picker-reliability`; implementation commits `f7cf7504cd06d87d78d25d3095b0a7f18c6a0dd6` and `8a587129b7467108606453ad471f7a5c1b111d3d`.
- **Test command or workflow URL:** Push-triggered Android UI smoke workflow; targeted regression is `python3 .github/scripts/test_diary_emulator_script.py`.
- **Result:** **UNVERIFIED pending fresh CI/emulator evidence**.
- **Exact failure or assertion:** Previous run [40212992310](https://github.com/Prav1525/Padippupal/actions/runs/40212992310) failed with `file selection did not return from DocumentsUI`. The captured hierarchy reported the filename and `item_root` as non-clickable, but `item_root` was focusable; the separate preview control was clickable.
- **Evidence links (logs/screenshots/XML/artifacts):** [failed emulator run](https://github.com/Prav1525/Padippupal/actions/runs/40212992310); [UI evidence artifact](https://github.com/Prav1525/Padippupal/actions/runs/40212992310/artifacts/12606607030).
- **Change made (files + rationale):** `.github/scripts/ui_smoke.py` now locates the focusable DocumentsUI `item_root`, taps its body away from the preview control, and sends `DPAD_CENTER` rather than tapping a filename node marked non-clickable. `.github/scripts/test_diary_emulator_script.py` now asserts this two-command interaction. This is a new diagnostic hypothesis based on the observed focusable row, not a confirmed picker fix.
- **Root cause:** **CONFIRMED** old target was non-clickable; **UNKNOWN** whether focus + keyboard activation actually selects the file or whether app picker integration is also faulty.
- **What this attempt proves:** Code and regression expectation are updated; runtime selection is not proven until fresh emulator evidence returns.
- **What remains unverified:** Script regression result, actual row focus/activation, Android content-URI return, and crop/rescan/save.
- **Difference from previous attempt:** Replaces the repeated non-clickable filename tap with a keyboard activation attempt on the focusable row; avoids preview control.
- **Next action and why:** Inspect the newly triggered workflow, including the exact failing step and screenshot/XML artifact. Do not retry unchanged if DPAD_CENTER fails; use fresh UI evidence to select a different diagnostic or correct the app's picker intent/result handling.


### 2026-10-26 — Replace failed focus-plus-DPAD activation with row double-tap diagnostic
- **Branch / commit:** `fix/diary-image-picker-reliability`; helper change commit `e95be55901a09d6d84a7672103d89284e04b11ae`; test and ledger updates follow.
- **Test command or workflow URL:** Fresh push-triggered Android UI smoke workflow; targeted regression `python3 .github/scripts/test_diary_emulator_script.py`.
- **Result:** **UNVERIFIED** — interaction changed; no emulator result yet.
- **Exact failure or assertion:** Latest run [40215174588](https://github.com/Prav1525/Padippupal/actions/runs/40215174588) failed at picker selection. Its screenshot [artifact](https://github.com/Prav1525/Padippupal/actions/runs/40215174588/artifacts/12607905643) and UI XML show `item_root focused=true`, `selected=false`; one row tap plus `DPAD_CENTER` did not activate the file. The current branch head before this change was `b3323c04ea38b64e28c25a342a31c941cc126456`; the failing run tested that exact SHA. APK build and curriculum tests passed, but the UI acceptance test failed.
- **Change made (files + rationale):** `.github/scripts/ui_smoke.py` now taps the same focusable row body twice, 250 ms apart, outside the separate preview control. This is materially different from the proven-ineffective focus + keyboard sequence and tests whether DocumentsUI requires a double-tap to open the file. `.github/scripts/test_diary_emulator_script.py` updates the selector expectations. No app URI-processing code changed because the callback is not reached.
- **Root cause:** **PROBABLE** test interaction mismatch; not yet confirmed. Evidence localizes the failure before URI return, but only the next emulator run can show whether double-tap returns a URI.
- **What this attempt proves:** A new activation strategy is committed for CI to exercise; source-level regression assertions are updated.
- **What remains unverified:** Targeted test execution on CI, actual DocumentsUI selection/URI return, crop, rescan, review, and planner save.
- **Difference from previous attempt:** Replaces a single tap plus `DPAD_CENTER` with a double-tap on the row body; no unchanged retry.
- **Next action and why:** Check the fresh workflow on this exact commit and inspect its screenshot/XML at the moment of activation. If the picker remains open, stop changing tap gestures and inspect DocumentsUI's actual activity/result semantics and test fixture launch path instead.


### 2026-10-26 — Fix stale assertion blocking the double-tap picker diagnostic
- **Branch / commit:** `fix/diary-image-picker-reliability`; assertion-fix commit 141355d53dec41067daa931eebf2d61c4313bb12.
- **Test command or workflow URL:** Android UI smoke run [40257054355](https://github.com/Prav1525/Padippupal/actions/runs/40257054355), job [121361328034](https://github.com/Prav1525/Padippupal/actions/runs/40257054355).
- **Result:** **FAIL** — smoke-script validation failed before emulator allocation; emulator test was skipped.
- **Exact failure or assertion:** `test_picker_opens_filename_row_not_preview_affordance` failed because it expected the obsolete log text `Focusing DocumentsUI row`; the changed helper now logs `Double-tapping DocumentsUI row`. The run reports JVM tests and APK build passed, script validation failed.
- **Evidence links (logs/screenshots/XML/artifacts):** [Workflow run](https://github.com/Prav1525/Padippupal/actions/runs/40257054355); the uploaded artifact [12622748394](https://github.com/Prav1525/Padippupal/actions/runs/40257054355/artifacts/12622748394) contains only the failure report because emulator allocation was skipped.
- **Change made (files + rationale):** `.github/scripts/test_diary_emulator_script.py` updates the brittle source-text assertion to match the helper's current `Double-tapping DocumentsUI row` log. This fixes a test-harness expectation mismatch only; it does not claim the gesture works.
- **Root cause:** **CONFIRMED** for this CI failure: the regression test still expected a log message from the previous focus-plus-DPAD implementation. The actual picker interaction root cause remains **UNKNOWN**.
- **What this attempt proves:** CI was blocked by a stale assertion before the double-tap could be exercised in the emulator.
- **What remains unverified:** Actual double-tap behavior, DocumentsUI closing, URI callback receipt, and crop/rescan/save.
- **Difference from previous attempt:** Corrects the exact test assertion identified in the CI traceback; no picker gesture or app behavior changed in this fix.
- **Next action and why:** Let CI run on this updated test and inspect the emulator result. If validation passes but DocumentsUI still does not return, stop gesture guessing and use the captured activity/logcat/result data to diagnose the launch/result contract.


### 2026-10-26 — Replace non-clickable row double-tap with clickable preview diagnostic
- **Branch / commit:** `fix/diary-image-picker-reliability`; helper commit `dde06e3ab456d9974919254be6db754007843a02`, regression tests `ccbbcc2ece714579b09106ba1891cf46edf2d6e1`, emulator-script comments `64bc07a1a620bb70c20fd8eecdf8b05130a5d383`; ledger update follows.
- **Test command or workflow URL:** Latest failing emulator run [40257341527](https://github.com/Prav1525/Padippupal/actions/runs/40257341527), job [121362234384](https://github.com/Prav1525/Padippupal/actions/runs/40257341527); artifact [12623437302](https://github.com/Prav1525/Padippupal/actions/runs/40257341527/artifacts/12623437302).
- **Result:** Previous row double-tap **FAIL**. New preview-control diagnostic **UNVERIFIED pending CI**.
- **Exact failure or assertion:** `FAIL: file selection did not return from DocumentsUI after row tap and any visible confirmation; inspect diary-picker-selection-result.xml and picker-selection-stuck.png`.
- **Evidence links (logs/screenshots/XML/artifacts):** [workflow](https://github.com/Prav1525/Padippupal/actions/runs/40257341527); [screenshot/XML artifact](https://github.com/Prav1525/Padippupal/actions/runs/40257341527/artifacts/12623437302); Android's [DocumentsUI picker action handler](https://android.googlesource.com/platform/packages/apps/DocumentsUI/%2B/07e538caffec348d204096b387562b99437ba780/src/com/android/documentsui/picker/ActionHandler.java) and [ACTION_OPEN_DOCUMENT guidance](https://developer.android.com/training/data-storage/shared/documents-files).
- **Change made (files + rationale):** In `.github/scripts/ui_smoke.py`, `tap_file` now resolves the filename-specific `preview_icon`, verifies it is enabled/clickable, and taps its center once. Updated `.github/scripts/test_diary_emulator_script.py` to assert that exact clickable target and coordinate selection. Updated `.github/scripts/diary_crop_emulator_test.sh` comments to describe the evidence-based route. No app code changed.
- **Root cause:** **PROBABLE** test-interaction mismatch; **UNKNOWN** for the full picker failure. The screenshot visibly shows the fixture and a preview affordance, and the UI tree marks the row/filename non-clickable while marking preview clickable. The prior test explicitly avoided this only clickable file affordance. This confirms the prior gesture was poorly grounded, but does not yet prove preview will return a URI or rule out picker/app integration issues.
- **What this attempt proves:** The latest emulator had a visible fixture and clickable preview affordance; the previous double-tap did not close DocumentsUI. JVM tests, APK build, and script validation passed in the failed run, but end-to-end picker acceptance failed.
- **What remains unverified:** Whether tapping preview opens a preview/confirmation screen, whether confirmation returns a content URI to PadippuPal, and whether crop/rescan/review/save succeeds.
- **Difference from previous attempt:** Stops repeating double taps on a row reported `clickable=false`; uses the matching accessibility node explicitly reported `clickable=true`.
- **Next action and why:** Run targeted regression/script validation and fresh emulator CI. Inspect the immediate post-preview XML/screenshot. If preview opens a confirmation screen, use its actual accessible confirmation control; if it does not, capture activity/result and DocumentsUI logs and isolate the picker intent/fixture/provider path before any further gesture change. Do not merge or call the picker fixed until URI return and downstream flow pass.


### 2026-10-26 — Switch from document preview affordance to the system Photo Picker contract
- **Branch / starting commit:** `fix/diary-image-picker-reliability`; starting source commits: app `1e007e1f5802ceedb51e85eb2853257cb73472cf`, emulator script `fd5e297624a63310b806f6f5f16e2d4bd396663c`, script tests `85fd7d9df6b54ab9db62cd80ef23f8dde7a7b6ad`. Latest failed emulator run [40258979146](https://github.com/Prav1525/Padippupal/actions/runs/40258979146), artifact [12623786655](https://github.com/Prav1525/Padippupal/actions/runs/40258979146/artifacts/12623786655).
- **Guidance applied:** Re-read `AGENTS.md` and the full `TESTING_GUIDANCE.md`; no repeated coordinate/gesture changes; separate build, script, and runtime outcomes; no merge without permission.
- **Exact evidence:** After tap at `(985,735)`, `picker-selection-result.png` is visually unchanged from the Downloads list. XML still shows the `preview_icon` as a preview affordance; no confirmation control appears and DocumentsUI never returns to PadippuPal. The previous assumption that preview would lead to selection is rejected.
- **Root cause confidence:** **CONFIRMED** that the preview-control strategy does not select/return the file in this test; **UNKNOWN** whether the underlying DocumentsUI row behavior is emulator-specific or related to the document-provider path. Android documents `PickVisualMedia` as the dedicated single-image selection contract, preferring the system Photo Picker and falling back to `OpenDocument` when unavailable ([API reference](https://developer.android.com/reference/androidx/activity/result/contract/ActivityResultContracts.PickVisualMedia)).
- **Change proposed:** Replace `OpenDocument` with `PickVisualMedia(ImageOnly)` for the diary photo flow. Change the emulator test to interact with the system Photo Picker's fixture filename and require return to PadippuPal before checking crop/rescan/save. This changes the app's picker contract and eliminates DocumentsUI preview assumptions rather than trying another tap pattern.
- **Verification plan:** Static script regression, JVM tests, APK build, then emulator UI acceptance. Inspect the actual Photo Picker screenshot/XML and verify app return plus crop/rescan/review/save. This entry does not claim the fix works until CI evidence arrives.


### 2026-10-26 — Correct Photo Picker compile error and stale smoke navigation
- **Branch / commit:** `fix/diary-image-picker-reliability`; correction commits `f82db5d9b5a85817e947cada05c6980c84d79aec`, `4b0842ef5f080f562b4f3451a56e51ef77a78730`, `38e1e10a0b05a742553be2a530c26955fd12beb5`.
- **Test command or workflow URL:** Prior build [run 40260125791](https://github.com/Prav1525/Padippupal/actions/runs/40260125791), job 121370489013; prior UI workflow [run 40260125781](https://github.com/Prav1525/Padippupal/actions/runs/40260125781), job 121370633433.
- **Result:** Prior attempt **FAIL**; corrections **UNVERIFIED** pending new CI.
- **Exact failure or assertion:** Kotlin compiler reported `Unresolved reference 'PickVisualMediaRequest'` at `StudyFeatures.kt:212`. The UI workflow stopped before emulator allocation. Script inspection also found stale hamburger/Downloads/List-view navigation remained before the new Photo Picker selection check, contradicting the intended direct Photo Picker flow.
- **Evidence links (logs/screenshots/XML/artifacts):** [APK build log](https://github.com/Prav1525/Padippupal/actions/runs/40260125791); [UI smoke log/artifact](https://github.com/Prav1525/Padippupal/actions/runs/40260125781).
- **Change made (files + rationale):** Imported `androidx.activity.result.PickVisualMediaRequest`; removed the leftover DocumentsUI navigation before capturing the Photo Picker screen; added static regression assertions that the picker section has no Downloads/List-view navigation and captures the picker screen once.
- **Root cause:** **CONFIRMED** for compile failure (missing import) and stale harness path (obsolete navigation was still present in source). Original runtime picker-selection root cause remains **UNKNOWN**.
- **What this attempt proves:** The compile error and stale test path are identified from exact CI logs/source and targeted corrections are committed.
- **What remains unverified:** Compilation, JVM tests, emulator selection/URI callback, crop/rescan, review and planner save.
- **Difference from previous attempt:** Fixes a source-level import defect and removes an unintended old navigation sequence; it is not another gesture/coordinate retry.
- **Next action and why:** Run fresh CI on the corrected head. If the test reaches the picker, inspect screenshot/XML and the return-to-app evidence before claiming selection works.


### 2026-10-26 — Fix remaining qualified Photo Picker request reference
- **Branch / starting commit:** `fix/diary-image-picker-reliability`; prior source HEAD `e81844d72eb18a0a6c55af8bf93d4fae7960daa5`.
- **Guidance applied:** Re-read `TESTING_GUIDANCE.md` and `AGENTS.md`; checked README build instructions, Android Gradle dependencies, and UI workflow before changing code.
- **Exact failure:** APK run [40261087137](https://github.com/Prav1525/Padippupal/actions/runs/40261087137) failed at `:app:compileDebugKotlin`, `StudyFeatures.kt:213:86 Unresolved reference 'PickVisualMediaRequest'`. UI run [40261087192](https://github.com/Prav1525/Padippupal/actions/runs/40261087192) failed in its first JVM test step and skipped emulator execution.
- **Root cause confidence:** **CONFIRMED** — source imported the top-level `androidx.activity.result.PickVisualMediaRequest`, but the call incorrectly referenced `ActivityResultContracts.PickVisualMediaRequest`; the request type is not nested inside ActivityResultContracts.
- **Change:** Call the imported `PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)` directly. Add static regression assertions for the import and call, and forbid the invalid qualified name.
- **Verification plan:** Fresh CI must pass JVM compilation/tests, debug APK build, script validation, and emulator test. The actual image URI return and crop/rescan/review/save flow remain **UNVERIFIED** until emulator evidence confirms them.
- **Result at time of entry:** Change committed; verification pending. No merge authorized or performed.


### 2026-10-26 — Fix picker-section static assertion and remove duplicate capture
- **Branch / failing commit:** `fix/diary-image-picker-reliability`, `3f365b31196f6e28123075b2079440e16d2b3dda`.
- **Failure evidence:** Android UI smoke run [40261764690](https://github.com/Prav1525/Padippupal/actions/runs/40261764690) failed in Python static validation at `test_diary_emulator_script.py:37` with `AssertionError: 0 != 1`; emulator test did not run. APK [40261764614](https://github.com/Prav1525/Padippupal/actions/runs/40261764614) and JVM tests [40261764621](https://github.com/Prav1525/Padippupal/actions/runs/40261764621) passed on that commit, but do not validate picker runtime.
- **Root cause confidence:** **CONFIRMED** — the Python assertion used a literal backslash followed by `n` rather than Python's newline escape, so it counted zero actual script lines. Source also had duplicate `dump_ui diary-picker` and screenshot commands despite the assertion intending one capture.
- **Change:** Correct the assertion to count the actual newline-terminated command and remove the duplicate picker dump/screenshot. No coordinate or gesture change.
- **Verification plan:** Fresh CI static test and JVM suite, APK build, then emulator acceptance. Runtime picker return and crop/rescan/review/save remain **UNVERIFIED** until the emulator reaches and passes them.
- **Outcome:** Fix committed; fresh CI pending. No merge performed.


### 2026-10-26 — Isolate picker failure from API 30 emulator environment
- **Branch / starting commit:** `fix/diary-image-picker-reliability`, API-30 failing source commit `9a85f998f78224a4afcd016606acfb7201fa951f`; diagnostic workflow commit `80910dde9e5e7c96bd243d944b599d909aed1b58`.
- **Guidance:** Re-read `AGENTS.md` and `TESTING_GUIDANCE.md` before the workflow edit. No app source was changed.
- **Exact prior evidence:** [API 30 emulator run 40262312607](https://github.com/Prav1525/Padippupal/actions/runs/40262312607): JVM tests, APK build, and script validation passed; emulator acceptance failed at selection. Logs report tapping `PadippuPal-diary-test.jpg` followed by repeated unchanged picker XML, then `PickVisualMedia did not return to PadippuPal`. The picker screenshot/XML showed DocumentsUI, not the dedicated Photo Picker.
- **Root-cause confidence:** **PROBABLE environment/test compatibility contributor; app callback failure remains UNKNOWN.** Official Android documentation says `PickVisualMedia` falls back to `ACTION_OPEN_DOCUMENT` if a dedicated Photo Picker is unavailable. API 30 is the only environment in the failing workflow, so the prior run did not compare environments.
- **Diagnostic change:** Change only `.github/workflows/android-ui-smoke.yml` emulator `api-level` and `system-image-api-level` from 30 to 35. Keep app source and the smoke script unchanged so the next run tests the same app/test against a newer Android system image. This is a controlled environment comparison against the retained API 30 evidence, not a claimed fix.
- **Verification plan:** Inspect the triggered API 35 workflow result, runtime Android version, picker activity/UI XML and screenshot, whether the result returns to PadippuPal, and whether the crop editor is reached. If API 35 passes selection while API 30 failed, environment compatibility is strongly implicated; if it fails similarly, inspect the new activity/result evidence before changing the app or gestures.
- **Outcome:** Diagnostic workflow change committed; CI result pending. No merge performed.


### 2026-10-26 — Remove stale API-30 pin from emulator regression test
- **Branch / starting commit:** `fix/diary-image-picker-reliability`; diagnostic workflow commit `80910dde9e5e7c96bd243d944b599d909aed1b58`; prior investigation note commit `a57309a41ad06dafa03e3e0c6c73b0d2150c0680`.
- **Guidance applied:** Re-read `AGENTS.md`, the full `TESTING_GUIDANCE.md`, README build requirements, the current workflow, the failing regression test, and this investigation log before editing.
- **Exact failure evidence:** API 35 run [40267375923](https://github.com/Prav1525/Padippupal/actions/runs/40267375923) and duplicate run [40267370886](https://github.com/Prav1525/Padippupal/actions/runs/40267370886) failed during script validation. Traceback: `test_smoke_workflow_does_not_force_the_incompatible_hayai_engine` asserted `system-image-api-level: 30` although the diagnostic workflow intentionally configures both `api-level: 35` and `system-image-api-level: 35`. Emulator acceptance was skipped; this run provided no picker evidence.
- **Root cause confidence:** **CONFIRMED** for the CI blocker: a TTS-related regression test unnecessarily hard-coded the old emulator API version and prevented the diagnostic environment from running.
- **Change made:** `.github/scripts/test_ui_smoke_helpers.py` now extracts both API-level settings and asserts there are exactly two and that they match, instead of requiring API 30. This keeps the important configuration invariant while allowing deliberate API-version changes. No app code or picker interaction was changed.
- **Verification plan:** Fresh CI must run the script regression tests and JVM tests, build the debug APK, and reach the emulator test. Then inspect picker screenshot/XML/logcat and verify selected URI return and crop flow.
- **Outcome at commit time:** Test fix committed as `d49c99b7f782d4051282b6d2c602296715efbc25`; verification pending. The API-35 picker/environment hypothesis remains **UNVERIFIED**. No merge performed.
