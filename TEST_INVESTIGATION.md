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


### 2026-10-26 — Install the built APK before emulator acceptance
- **Branch / starting commit:** `fix/diary-image-picker-reliability`, `fc141185e5ea29a6b652955114ca7752366abd97`.
- **Guidance applied:** Re-read `AGENTS.md`, full `TESTING_GUIDANCE.md` (blob `7a660ee2baca4585632388477ab036d4e980d5b5`), the current workflow, manifest, and latest investigation ledger before editing. Keep API 35 as the controlled environment comparison; do not change lesson-preparation behavior or picker gestures in response to a pre-picker failure.
- **Exact failure evidence:** API-35 UI runs [40269347644](https://github.com/Prav1525/Padippupal/actions/runs/40269347644) and [40269351181](https://github.com/Prav1525/Padippupal/actions/runs/40269351181) both pass JVM tests, debug APK build, and script validation, then fail before picker interaction with `Error: Activity class {com.padippupal.app/com.padippupal.app.MainActivity} does not exist.` Logs also show `Unable to connect to adb daemon on port: 5037` during emulator startup, but the fatal assertion is the missing activity at launch. The manifest confirms `.MainActivity` is the exported launcher activity. The workflow builds `app/build/outputs/apk/debug/app-debug.apk` but had no explicit `adb install` command before running `.github/scripts/diary_crop_emulator_test.sh`.
- **Root cause:** **CONFIRMED for the test-harness launch failure:** the workflow does not explicitly install the built APK before the test script calls `am start`; package/activity absence is the observed runtime error. This does not explain or resolve the earlier API-30 picker-selection failure.
- **Change made:** Add explicit `adb install -r app/build/outputs/apk/debug/app-debug.apk`, verify package path with `pm path`, and verify launcher resolution for `com.padippupal.app/.MainActivity` before running TTS setup and the diary acceptance script. No app source, picker interaction, API level, or lesson-preparation code changed.
- **Verification plan:** Let exact-head CI run static tests, JVM tests, APK build, then the API-35 emulator test. Confirm installation/launcher checks pass; inspect whether the test reaches the Photo Picker and captures the selection-result screenshot/XML; only then assess picker URI return and crop/rescan/review/save.
- **Result at edit time:** Workflow change proposed and committed below; emulator acceptance is still unverified. No PR merge performed.


### 2026-10-27 — Isolated syllabus synthesis integration checks
- **Branch:** `feature/production-syllabus-synthesis-only`
- **Starting commit:** `d08cdba5d3cf646b9ee9337ae50906133173f0b9`
- **Guidance applied:** Re-read `AGENTS.md` and the full `TESTING_GUIDANCE.md` before this code-edit batch. Keep the synthesis change backend-only; do not deploy or merge until the exact-head checks and production-safe acceptance gates pass.
- **Exact evidence:** Curriculum Engine Tests run [40432954843](https://github.com/Prav1525/Padippupal/actions/runs/40432954843), job 121954804894, reported 68 passed and 2 failed. Synthesis API test failed because lesson review returned `approved` but its associated synthesis round remained `draft` (`test_syllabus_synthesis_api.py:141`). Diary scan test failed because runtime passed timeout 75 while the test asserted 35 (`test_study_features.py`); current `backend/app.py` explicitly uses `urlopen(..., timeout=75)`.
- **Root cause:** **CONFIRMED** for synthesis review synchronization: the main-branch review handler updated only `chapter_lessons`, unlike the prototype handler, which also synchronizes the exact evidence-matching synthesis round and topic approval state. **CONFIRMED** for diary test: the assertion was stale against the current backend timeout.
- **Change in this batch:** Port the evidence-matched review-state synchronization into the isolated backend; update the stale diary test assertion to 75; retain this record append-only. This does not change diary runtime behavior.
- **Verification plan:** Re-run exact-head Curriculum Engine Tests, check Android/workflow gates, inspect failures if any, then run the production-safe draft-only synthesis acceptance process. No production database writes, lesson generation, merge, or deployment has been performed by this investigation entry.
- **Outcome at edit time:** Fixes committed for CI verification; exact commit/run result to be appended after the next workflow completes.


### 2026-10-27 — Retry strict chapter synthesis after validation failure
- **Branch / commit:** `fix/chapter-lesson-synthesis-validation`; code commit `ec16112b04295744d125c6d75e156c62c53aa938`; ledger follow-up commit pending.
- **Test command or workflow URL:** [Curriculum Engine Tests](https://github.com/Prav1525/Padippupal/actions/runs/40455163866); [Investigation Guidance Gate](https://github.com/Prav1525/Padippupal/actions/runs/40455163898); [Android UI smoke](https://github.com/Prav1525/Padippupal/actions/runs/40455163729); [APK build](https://github.com/Prav1525/Padippupal/actions/runs/40455163881).
- **Result:** Curriculum Engine Tests **PASS**; APK build **PASS**; Investigation Guidance Gate **FAIL** because this code PR did not append a dated entry to this ledger; Android UI smoke **IN PROGRESS** at last check.
- **Exact failure or assertion:** Gate log: `FAIL: code/config changed but TEST_INVESTIGATION.md was not updated in this PR.`
- **Evidence links (logs/screenshots/XML/artifacts):** Gate job 122026672939; failing step is `Validate guidance and investigation record`; workflow log shows the exact assertion above.
- **Change made (files + rationale):** Append this entry to document the chapter-synthesis retry, its test evidence, and remaining production verification; this satisfies the repository's append-only investigation requirement without changing runtime code.
- **Root cause:** **CONFIRMED** for the gate failure: `backend/app.py` changed but `TEST_INVESTIGATION.md` was not included in the PR diff. This is a documentation-gate failure, not evidence that the Python fix failed.
- **What this attempt proves:** The curriculum test suite and APK build passed on the code commit; the required investigation ledger was missing from the PR.
- **What remains unverified:** Android UI smoke completion; retry behavior against the failing production Science chapter; production deployment and saved-draft verification.
- **Difference from previous attempt:** Adds the missing evidence-ledger record instead of changing application behavior or weakening validation.
- **Next action and why:** Re-run the gate and wait for Android smoke to complete; only then evaluate all checks. Do not merge or deploy without explicit authorization, and keep source-citation validation strict and lesson status draft-only.


### 2026-10-27 — Improve chapter synthesis citation retry diagnostics
- **Branch / commit:** `fix/synthesis-citation-retry-diagnostics`; commits `d9dbf310f4c7993169c5f8ea5accbbe0e94829a1` and `f99d53986196389416b3b95269bcf2def1438eef`.
- **Test command or workflow URL:** [Curriculum Engine Tests](https://github.com/Prav1525/Padippupal/actions/runs/40461379063); [Investigation Guidance Gate](https://github.com/Prav1525/Padippupal/actions/runs/40461379160); [Android UI smoke](https://github.com/Prav1525/Padippupal/actions/runs/40461379077); [Android APK](https://github.com/Prav1525/Padippupal/actions/runs/40461379084).
- **Result:** Curriculum Engine Tests **PASS**; Investigation Guidance Gate **FAIL** due to the ledger not being included in the PR; Android UI smoke and APK build were **IN PROGRESS** at last check.
- **Exact failure or assertion:** The gate reported: `FAIL: code/config changed but TEST_INVESTIGATION.md was not updated in this PR.`
- **Evidence links (logs/screenshots/XML/artifacts):** [Investigation gate job log](https://github.com/Prav1525/Padippupal/actions/runs/40461379160); production Render logs on 2026-10-27 reported `lesson leaves 1 supplied source chunks uncited` and `concept_map[1] cites an unknown source chunk` with two supplied chunks uncited.
- **Change made (files + rationale):** Updated `backend/syllabus_synthesis.py` to report exact unknown and missing chunk IDs in validation errors, and updated `backend/test_syllabus_synthesis.py` to assert that missing chunk IDs appear. This gives the existing retry actionable diagnostics without relaxing citation validation.
- **Root cause:** **CONFIRMED** for the PR gate failure: the code-changing PR omitted the required append-only investigation ledger update. The production generation failure is also confirmed as citation mismatch/coverage errors; this PR improves retry feedback but does not yet prove that the model will correct all citations.
- **What this attempt proves:** Curriculum Engine Tests passed on the PR head. The required guidance gate failed for documentation-only reasons; other checks were still running when inspected.
- **What remains unverified:** Android UI smoke and APK checks must finish; retry behavior on the failing Mathematics chapters must be tested after the fix is reviewed and deployed. No merge or production deployment has been performed.
- **Next action and why:** Append this entry to satisfy the investigation gate, verify all required CI checks, then review the diff. Keep PR draft-only until checks are green; do not merge or deploy without authorization. After deployment, retry only `Lines and Angles` and `Number Play` and confirm exact source citation coverage before continuing.


### 2026-10-27 — Improve synthesis citation retry diagnostics
- **Branch / PR:** `fix/synthesis-citation-retry-diagnostics`; [PR #34](https://github.com/Prav1525/Padippupal/pull/34).
- **Production evidence:** Render application logs from 2026-10-27 show rejected Mathematics synthesis retries with `concept_map[1] cites an unknown source chunk` and `lesson leaves 1 supplied source chunks uncited`. These are strict citation-validation failures; invalid lessons are not persisted.
- **Change in this batch:** Report the exact unknown citation IDs and exact missing supplied chunk IDs in validator errors. Update the regression test to assert the missing chunk ID is exposed. Citation validation remains strict; draft approval/persistence behavior is unchanged.
- **Verification:** Curriculum Engine Tests run [40461379063](https://github.com/Prav1525/Padippupal/actions/runs/40461379063) passed. Investigation Guidance Gate run [40461379160](https://github.com/Prav1525/Padippupal/actions/runs/40461379160) failed because this PR did not append this required ledger entry; this is a documentation-gate failure, not a test assertion failure. Android APK run [40461379084](https://github.com/Prav1525/Padippupal/actions/runs/40461379084) and Android UI smoke run [40461379077](https://github.com/Prav1525/Padippupal/actions/runs/40461379077) were still in progress at time of entry.
- **Next action:** Include this append-only entry, rerun required checks, and inspect any remaining failures. Do not merge/deploy or regenerate the failing production chapters until the required checks and draft-only regression verification are complete.


### 2026-10-27 — Handle JSON-serialized IDs in detail URL paths
- **Branch / commit:** `fix/malformed-synthesis-detail-ids`; implementation commits `6a91c2d7aea3fe50b1677f4516db5be071db874c` and `f4240c3a6a62f577e80ae423a97ef734b31515ab`; ledger follow-up pending.
- **Guidance applied:** Re-read `AGENTS.md` and the full `TESTING_GUIDANCE.md`. Keep this backend-only and isolated; do not merge or deploy without explicit permission.
- **Exact failure evidence:** Render logs previously showed a request to `/admin/syllabus-synthesis/rounds/%7B...JSON containing round_id...%7D`, while the route expects a scalar `round_id`. The reported `Chapter lesson not found.` response is consistent with the same malformed-ID pattern on the chapter-lesson detail endpoint, but the exact originating client request for that response is not yet confirmed.
- **Root cause confidence:** **CONFIRMED** that the round-detail request shape is malformed based on the logged URL and route contract. **PROBABLE** that the chapter-lesson 404 has the same cause; the regression test now targets that scenario.
- **Change made:** Added strict normalization for legacy JSON-object path IDs on synthesis-round and chapter-lesson detail GET endpoints. It only extracts the one expected key, rejects malformed/unexpected objects with HTTP 400, and keeps ordinary scalar IDs unchanged. Added regression assertions for both endpoints in `backend/test_syllabus_synthesis_api.py`. No citation checks or draft/approval rules were weakened.
- **Verification plan:** Run the exact-head Curriculum Engine Tests and Investigation Guidance Gate; inspect all required checks and the resulting PR diff. Then verify the deployed request shape and original error against the live API only after authorized deployment.
- **Result:** **UNVERIFIED** at ledger append time; CI has not yet completed for this branch. No merge, deployment, or production data mutation performed.
- **What this proves / does not prove:** The source change and regression cases are committed to the isolated branch. It does not yet prove tests pass, that the exact chapter-lesson 404 has no additional cause, or that production is fixed.
- **Next action and why:** Open an isolated PR, inspect exact-head CI and required checks, and keep it unmerged until checks pass and the remaining request-to-error link is confirmed.

### 2026-10-27 — Correct topic evidence ranges and avoid copied objectives
- **Branch:** `fix/synthesis-topic-evidence-ranges`; reconciled on top of current main `e039d2c7010a189e19b4dd9d451e206cc612a885` to retain the merged detail-ID normalization fix.
- **Observed evidence:** Production audit of the CBSE Class 6 Mathematics chapter “Lines and Angles” found four topic rows each assigned the chapter-wide page range 1–53, even though their citation sets cover different page spans. The same two chapter-level learning objectives were copied into all four rows.
- **Root cause:** Topic persistence assigned chapter-wide page boundaries and chapter-level objectives to every topic rather than deriving them from each teaching step's cited evidence.
- **Change:** Build a chunk-ID-to-page map from the supplied evidence packet, derive each topic's page range only from its cited chunks, request step-specific objectives, and store those objectives when provided. If omitted, persist an empty list with an explicit validation note.
- **Regression coverage:** Assert topic page boundaries and that omitted step objectives are not copied from chapter-level objectives.
- **Safety:** Draft-only behavior and strict source-citation validation remain unchanged. No production DB rows changed and no lessons were approved.
- **Verification status:** Reconciled commit prepared; CI must pass on the updated PR head before merge. Production re-synthesis remains pending deployment and review.

### 2026-10-27 — Add Class 6 lesson content-consistency validation
- **Branch / PR:** `fix/class6-maths-content-qa`; [PR #40](https://github.com/Prav1525/Padippupal/pull/40).
- **Observed production evidence:** Class 6 Maths draft audit identified a Fractions history/notation conflation, chikki thirds-versus-sixths mismatch, number-line denominator mismatch, a four-stroke example described as a fifth tally, overgeneralized diagonal-unit wording, and imprecise triangle/rectangle base-height wording. All affected lessons remain drafts.
- **Change made:** Added targeted content consistency checks to `backend/syllabus_synthesis.py` and seven regression tests in `backend/test_lesson_content_consistency.py`. The checks reject the known patterns during chapter-lesson validation; they do not automatically rewrite existing production lesson rows or approve content.
- **Test evidence:** Curriculum Engine Tests run [40521410289](https://github.com/Prav1525/Padippupal/actions/runs/40521410289) was still running at ledger update time. Investigation Guidance Gate run [40521410373](https://github.com/Prav1525/Padippupal/actions/runs/40521410373) initially failed because this required append-only ledger entry was missing; this entry addresses that documentation gate.
- **Root cause confidence:** **CONFIRMED** for the observed lesson/visual contradictions by inspecting the live lesson JSON; **UNVERIFIED** whether the new validator passes all regression tests until CI completes.
- **What this proves:** The code and regression cases are committed to an isolated PR. It does not prove the tests pass, that the PR is merged/deployed, or that existing production drafts are corrected.
- **What remains unverified:** Exact-head CI; deployment of the guardrails; authenticated correction of existing drafts; live tutor delivery for approved versus draft lessons.
- **Next action:** Inspect all required CI results and fix failures. Then use the authenticated admin workflow to correct and revalidate existing drafts. Keep them unapproved until source-based human review is complete.



### 2026-10-27 — Add authenticated draft-only lesson content editing
- **Branch / PR:** `fix/class6-maths-content-qa`; [PR #40](https://github.com/Prav1525/Padippupal/pull/40).
- **Change made:** Added `PUT /admin/chapter-lessons/{lesson_id}/content`. It requires the existing admin-token dependency, permits edits only for `draft` or `review` lessons, verifies every stored source chunk still exists under the expected ready source and curriculum profile, and runs the chapter lesson validator before saving.
- **Safety:** A successful edit always leaves the lesson in `draft` with review required. Approved/rejected lessons return HTTP 409; failed citation/content validation returns HTTP 422. Matching synthesis round/topic status is returned to draft only when the evidence chunk set matches exactly. No production lesson was edited or approved.
- **Regression tests added:** `backend/test_chapter_lesson_content_endpoint.py` covers missing admin auth, invalid citation rejection without mutation, valid draft update with draft preservation, and approved lesson lock.
- **Verification:** Pending CI on the updated PR head. This entry records implementation, not a claim that tests or production behavior have been verified.
- **Next action:** Inspect the latest exact-head CI results; only after tests pass, use the authenticated endpoint to correct the known Maths draft issues and revalidate them. Keep all lessons unapproved until human source review is complete.


### 2026-10-27 — Guarded API-only corrections for known Class 6 Maths drafts
- **Change made:** Added `backend/scripts/apply_class6_math_qa_corrections.py`. It fetches the three identified lessons through the authenticated admin API, checks each is still a draft, verifies expected old wording before editing, and sends updates only through the new content endpoint. It defaults to dry-run; `--apply` is required to save.
- **Corrections covered:** Fractions historical wording and two visual/narration mismatches; Data Handling tally marks and warm-up visual; Perimeter and Area diagonal-length scope and triangle-area base/height wording.
- **Safety:** Requires `PADIPPUPAL_ADMIN_TOKEN` from the caller's secure environment; no token is stored in code. No direct database writes, approval action, or publish action. Every API save must confirm draft status and human review required.
- **Regression tests added:** `backend/test_class6_math_qa_corrections.py` runs the proposed edits through the same lesson validator; it does not call production.
- **Verification:** CI pending for this exact commit. The script has not been run against production because no authenticated HTTP execution context is available in this session. No production lesson has been changed by this script.


### 2026-10-27 — Correction-script regression finding
- The first regression run caught a case-sensitive text replacement in the diagonal wording guard. The script was corrected to replace the full targeted teacher narration after verifying the expected old phrase case-insensitively.
- The follow-up CI run on the corrected commit is pending. Do not run the production correction script until the latest tests pass and a trusted authenticated environment is available.


### 2026-10-28 — Reduce home-screen clutter and restore inline tutor visuals
- **Branch / pre-ledger commit:** `ui/modern-learner-layout`; latest code commit before this log entry `7b82081b4b7a1c80499a86c1b864249453bb0a20`.
- **Requirement / evidence:** User reports the app still does not feel polished and asks to identify redundancy, apply modern Android UI practices, and keep visuals inside the tutor screen. Source inspection confirmed the home screen had multiple competing card groups plus a repeated planner entry also present in bottom navigation. The tutor's `ChapterOneMathAnimation` and `DatabaseLessonVisual` composables returned before rendering; `DatabaseInteractiveLessonLab` also returned immediately and had no call site. `WordByWordCaption` rebuilt text and inserted paragraph breaks every third sentence instead of preserving source whitespace.
- **Guidance applied:** Re-read `AGENTS.md`, full `TESTING_GUIDANCE.md`, README build instructions, Gradle app configuration, Android APK workflow, Android UI smoke workflow, smoke helper and regression test code before changes. Google Android guidance consulted: adaptive layout and content ([Android Developers](https://developer.android.com/design/ui/mobile/guides/layout-and-content/adapt-layout)), layout/navigation patterns ([Android Developers](https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns)), and Material 3 in Compose ([Android Developers](https://developer.android.com/develop/ui/compose/designsystems/material3)).
- **Change made:** Reworked the home dashboard around one primary `Start learning` action, a compact two-row action list for homework scan and exam practice, and one syllabus connection row. Removed the duplicate subject/planner tiles because those destinations already have bottom-navigation entries. Restored the inline pattern animation and textbook lesson visual rendering; wired database-provided interactive lessons into the latest assistant message as inline content, falling back to the static lesson visual when no interactive lesson is provided. Removed the unused duplicate local interactive-lab composable. Reworked word highlighting to preserve the original text whitespace/paragraph boundaries, with consistent 16sp text and 26sp line height. Updated home smoke expectations and added source-contract regression tests for the new home and caption layout.
- **Root cause:** **CONFIRMED** for the invisible visual components and forced paragraph breaks by early returns and the caption construction code. **CONFIRMED** for redundant home entry points by source: Subjects and Planner were present in bottom navigation and duplicated as home tiles. This does not establish whether every backend response supplies an interactive lesson or textbook image.
- **Verification status:** **UNVERIFIED** pending exact-head CI. No APK build, emulator screenshot review, live text/audio check, or learner deployment has been performed for this branch yet.
- **What this proves / does not prove:** Source now contains the intended inline rendering path and a simpler home layout. It does not prove that the live backend returns usable interactive visual metadata, that textbook image assets are present, or that the new layout renders correctly on-device.
- **Next action:** Run the smoke-helper regression tests, Android JVM tests, debug APK build, and API-35 emulator flow. Inspect screenshots/accessibility output for the new home labels, inline visual rendering, caption alignment, and overlapping content; fix any real failures before declaring the UI verified. Do not merge or deploy without explicit permission.


### 2026-10-28 — UI redesign first CI compile failure and correction
- **Branch / commits:** `ui/modern-learner-layout`; first PR head `5a2db6f93b1c617b334129d224fe221bab7ab284`; compile correction `0744d5b27562f6fadc3e50b62aac74554771888c`; caption-test boundary correction `8310f8971b6b0ed38d99afbf6446923c7a5ba514`.
- **Test / evidence:** [Android APK run 40713741627](https://github.com/Prav1525/Padippupal/actions/runs/40713741627), job 122905656986, compiled the PR merge ref with Gradle 8.9 and JDK 17.
- **Result:** **FAIL** on the initial head at `:app:compileDebugKotlin`; exact error: `MainActivity.kt:259:26 Unresolved reference 'BorderStroke'`. The new home card used `BorderStroke` without importing it. The smoke run for that superseded head was cancelled after a newer commit was pushed.
- **Correction:** Added `androidx.compose.foundation.BorderStroke` import. Also corrected a new source-contract test to find the now-active `ChapterOneMathAnimation` function directly after removing the unused `InteractiveLessonLab` composable.
- **Root cause:** **CONFIRMED** for the compile error by the Kotlin compiler diagnostic. The correction is committed, but its build/test status is **UNVERIFIED** until CI on the corrected head completes.
- **What remains:** Latest-head debug APK build, UI smoke helper tests, JVM tests, and API-35 emulator screenshots/flow must pass. Do not mark the redesign verified based on the import fix alone.
- **Next action:** Inspect CI on the corrected head; if a new failure appears, use its first meaningful error and screenshot/log evidence rather than repeating an unchanged build. No merge or deployment performed.


### 2026-10-28 — UI smoke helper validation found stale paragraph assertion
- **Branch / commit under test:** `ui/modern-learner-layout`; PR head at failed run `3db30454bd496ed4ac786afb1027d8166d79262d`; test correction `3dec9a073ba5622ad1853972aaf3a3468e6c6543`.
- **Workflow:** [Android UI smoke run 40713993637](https://github.com/Prav1525/Padippupal/actions/runs/40713993637), API 35, JDK 17, Gradle 8.9.
- **Result:** **FAIL** at smoke-script validation. Kotlin/JVM tests **PASS** and debug APK build **PASS**. Emulator flow was **SKIPPED** because validation failed first.
- **Exact failure:** `test_spoken_caption_groups_sentences_into_natural_paragraphs` required the old string `separate paragraphs only after every third sentence`; the code now intentionally preserves source whitespace and paragraph breaks.
- **Root cause:** **CONFIRMED** stale test expectations contradicted the new UI requirement. This was not a Kotlin compilation or APK packaging failure.
- **Correction:** Replaced the stale test with assertions that the caption retains original whitespace, trailing text, and paragraph boundaries, and no longer injects a break after every third sentence. Removed duplicate coverage for the same contract. Added incident details to `docs/TEST_FAILURE_REGISTER.md`.
- **What remains unverified:** Corrected script validation, API-35 emulator navigation/screenshots, and inline visual rendering are pending a fresh CI run on the updated head. No merge/deployment performed.
- **Next action:** Check the latest PR run. If script validation passes, inspect the emulator artifact and verify the home labels, lesson visual, paragraph layout, and absence of overlap.


### 2026-10-28 — Inline lesson visuals: source provenance and original diagrams
- **Branch:** `ui/modern-learner-layout`; UI enhancement commit `f9e7efa76eeca60e510b5d4a9935c8e2354fd493`; source/visual regression commit `eb1aac6090238fee496ce655ecf879f6ea9198b3`.
- **User requirement:** Use teaching visuals in the same tutor screen, synchronized to the concept being taught; avoid overlays or separate visual windows.
- **Research reviewed:** Android guidance on [Compose performance best practices](https://developer.android.com/develop/ui/compose/performance/bestpractices) and [mobile layout/navigation patterns](https://developer.android.com/design/ui/mobile/guides/layout-and-content/layout-and-nav-patterns). The lesson dataset records NCERT content as `restricted_do_not_ingest_or_redistribute_full_text_without_permission`; the official [NCERT/ePathshala textbook terms](https://epathshala.nic.in/wp-content/doc/book/gtextbook/textbook.htm) restrict reuse/redistribution of NCERT E-content and explicitly address software use.
- **Change made:** Added an original four-part fraction diagram and an angle arc to the existing in-line Compose Canvas visual. Added textbook source labels/page ranges from each lesson's existing `source_refs` metadata, so page attribution is shown with the teaching visual rather than guessed or hardcoded.
- **Rights decision:** Did **not** copy or bundle NCERT textbook page images. The app can show original concept illustrations alongside verified textbook page references; adding actual NCERT images to app software needs the appropriate written permission/license first. Source metadata currently covers the Grade 6 Mathematics chapter “Patterns in Mathematics” (36 lesson references, pages 1–17); most other lesson topics do not yet have verified page references.
- **Regression coverage:** Added source-contract tests for the fraction diagram, angle arc, and source-reference rendering. Exact-head CI remains the authority for build/test status.
- **What remains unverified:** Visual balance on-device, actual source page labels in a live API response, and natural narration/highlight synchronization. No merge or deployment performed.
- **Next action:** Let latest-head CI finish; inspect emulator screenshot/artifact for home layout, inline diagram size/overlap, source label readability, and lesson navigation before adding more scene-specific diagrams.


### 2026-10-28 — Emulator failure after home redesign: stale CTA selector
- **Branch:** `ui/modern-learner-layout`; failed head `901a0888c8285e383bb0d76f821a1b714eab2067`; fix commits `2e21c2fa49838825d13a6ba88c551c906d7e9db0` and `d2ada5de0225b18a0d998b98717bfb44b9ea648f`.
- **Workflow:** [Android UI smoke run 40714616741](https://github.com/Prav1525/Padippupal/actions/runs/40714616741).
- **Result:** JVM tests, APK build, and smoke-script validation **PASS**; emulator end-to-end **FAIL**. The home screen loaded and all new expected labels were accessible.
- **Exact failure:** Automation tried to tap `Begin lesson`; current home UI exposes `Start learning`.
- **Root cause:** **CONFIRMED** stale selector in `.github/scripts/android-ui-smoke.sh` after the home redesign.
- **Correction:** Changed the tap target to `Start learning` and added a regression assertion that the current target is present and the removed target is absent. Added incident details to `docs/TEST_FAILURE_REGISTER.md`.
- **What remains unverified:** Fresh API-35 emulator run after this fix, including lesson selection and tutor visual flow. No merge or deployment performed.


### 2026-10-28 — Inline visual test boundary typo
- **Failed workflow:** [Android UI smoke run 40716183030](https://github.com/Prav1525/Padippupal/actions/runs/40716183030); source commit `264f8286da099e5eccb7cb35d13e1a24d9b638e6`; correction `43dd69b52760cb020e3c6545720bdcf875c84c51`.
- **Result:** JVM tests and APK build passed; smoke-script validation failed before emulator execution.
- **Root cause:** **CONFIRMED** new test attempted to find a literal escaped-newline boundary before `find_interactive_lesson`; the source did not contain that exact string.
- **Correction:** Use the stable function declaration substring `def find_interactive_lesson(` as the boundary. Failure is documented in `docs/TEST_FAILURE_REGISTER.md`.
- **Remaining verification:** Re-run helper tests and API-35 emulator flow on the corrected head. No merge or deployment performed.


### 2026-10-28 — Wire exact-match concept visuals into live teaching
- **Branch:** `ui/modern-learner-layout`; implementation is being committed after source review.
- **Finding:** The live `/tutor/lesson-plan` path returned speech segments but did not return the exact-matched `interactive_lesson` blueprint; Android then showed the special Patterns animation only. The chat path already returned matched blueprints. The live planner and chat prompts also contained a conflicting text-only instruction.
- **Change made:** Attach the exact chapter/topic-matched blueprint to successful live lesson responses; keep the lesson successful if optional visual lookup fails. Carry the blueprint into the single continuous spoken lesson and render a compact inline visual in the live tutor column. Drive the active blueprint step from the spoken caption's current word progress, preserve the existing Patterns animation as fallback, and retain the visual with the completed lesson in chat. Align backend prompts with optional, matched, inline visuals and prohibit invented textbook image assets.
- **Rights and source scope:** Only original app-rendered diagrams and existing source page references are used; no NCERT images are copied into the software. Actual NCERT image reuse remains subject to the relevant permission/license.
- **Regression coverage:** Add a backend assertion that an exact matched blueprint is attached to an approved live lesson and source-contract assertions for inline visual rendering and word-progress synchronization.
- **Verification status:** **PENDING** exact-head JVM tests, APK build, guidance gate, and API-35 emulator flow. No merge or deployment performed.


### 2026-10-28 — UI branch CI exposed stale text-only prompt assertions
- **Branch:** `ui/modern-learner-layout`; failing head `036cc7058d58bf891895db99b818b0bfaaca899b`; test correction `7210cd2a3cf3ec5003a931675a6696a06eb09973`.
- **Workflow:** [Curriculum Engine Tests run 40718714772](https://github.com/Prav1525/Padippupal/actions/runs/40718714772).
- **Result:** 81 passed, 2 failed. Both failures were assertions that the lesson-plan prompt must be text-only. The current intended product contract is chat-first with optional inline concept visuals, with exact chapter/topic-matched blueprints rendered in the same tutor screen.
- **Root cause:** **CONFIRMED** stale tests contradicted the current source contract; they were not runtime app failures.
- **Fix:** Updated both assertions in `backend/test_tutor.py` to require the inline visual policy and current chat-first mode wording. No production behavior changed in this correction.
- **Validation:** New-head CI is pending. APK run for prior head passed; UI smoke run for prior head was cancelled by a newer push and must be checked on the latest head.
- **Next:** Inspect fresh curriculum test, APK build, and emulator smoke on commit `7210cd2a3cf3ec5003a931675a6696a06eb09973`. No merge or deployment performed.


### 2026-10-28 — Smoke helper retained a pre-refactor completed-lesson assertion
- **Branch:** `ui/modern-learner-layout`; failed head `036cc7058d58bf891895db99b818b0bfaaca899b`; correction `2da08c4acac3ebf1ced859dec16568129f707838`.
- **Workflow:** [Android UI smoke run 40718715394](https://github.com/Prav1525/Padippupal/actions/runs/40718715394).
- **Result:** Smoke-script validation failed in `test_completed_lesson_is_kept_for_follow_up_chat`; home-label assertions passed and emulator interaction had not started.
- **Root cause:** **CONFIRMED** test expected the old two-argument `TutorMessage` constructor. Current source correctly retains `liveInteractiveLesson` when saving the completed lesson so follow-up chat can keep the inline lesson visual.
- **Fix:** Updated the helper assertion to require the current constructor call including `interactiveLesson = liveInteractiveLesson`. No production code changed.
- **Validation:** Corrected prompt assertions and this helper assertion are queued for latest-head CI. No merge or deployment performed.


### 2026-10-28 — Synthesis-linked compact 2D visuals
- **Branch / PR:** `feat/synthesis-linked-2d-visuals`, draft [PR #49](https://github.com/Prav1525/Padippupal/pull/49), stacked on `ui/modern-learner-layout`.
- **Goal:** Derive visuals from approved `chapter_lessons.lesson_json.teaching_sequence`, persist one visual blueprint per lesson step, and return it beside the exact matching summary and source chunk IDs.
- **Implementation:** Added `backend/lesson_visuals.py`, `lesson_visual_assets` table, lazy create/update and retrieval in the approved lesson path, and `GET /chapter-lessons/{lesson_id}/visuals`. The existing tutor response gets a compact `interactive_lesson` adapted from these stored records.
- **Constraints:** Small 2D vector/card blueprints only; no 3D, large animation, separate overlay, invented textbook images, or guessed page references. Empty or unsupported step metadata must not create unrelated visuals.
- **Tests added:** `backend/test_lesson_visuals.py` covers step-to-summary mapping, source chunk retention, compact/static constraints, stable fingerprints, and empty-sequence behavior.
- **Validation status:** Not yet verified on the exact head. Draft PR was opened to trigger CI; inspect backend tests and APK/emulator checks before calling this ready. No merge or deployment performed.


### 2026-10-28 — New visual persistence changed assumptions in two existing tutor tests
- **Workflow:** Curriculum Engine Tests run [40721266652](https://github.com/Prav1525/Padippupal/actions/runs/40721266652), head `b0bda67b7ce5e0a75da9cdf39942c341c5165364).
- **Result:** 85 passed; 2 failed. One fake database asserted that every SQL statement must be the approved-lesson query; the other fake database returned an approved lesson row for the new visual-assets query, causing a missing `step_id`.
- **Root cause:** **CONFIRMED** the tests were intended to isolate lesson selection/topic validation but did not stub the newly added visual persistence boundary.
- **Fix:** Updated both tests to stub `get_or_create_lesson_visuals` as empty; dedicated tests cover the synthesis-to-visual builder separately. This preserves the original test purpose while avoiding fake DB behavior that cannot represent the new table.
- **Validation:** Correction pushed in commit `888ffe464ed615c0e42b8d4435ee6caef6f6252a`; exact-head CI rerun pending. No merge or deployment performed.


### 2026-10-28 — Render synthesized visual blueprints with a dedicated static Compose card
- **Branch / PR:** `feat/synthesis-linked-2d-visuals`, draft PR #49; Android renderer commit `f446d1ae05bc3c780177354f72f247f54fbee522`.
- **Requirement:** The generated visuals must appear in the same tutor screen, remain compact, and not inherit large or looping animation behavior from the generic interactive lesson renderer.
- **Change:** Added a dedicated `synthesis_static` renderer that shows the synthesis step's caption and up to six compact labels in a simple 2D card; its active summary follows the existing speech-progress step index.
- **Verification plan:** Exact-head Android APK build and API-35 emulator UI smoke, plus backend tests. The prior backend run passed 87 tests before this Android renderer edit; the exact new head still needs verification.
- **No merge or deployment performed.**


### 2026-10-28 — Generate visuals at synthesis approval, not only on first learner retrieval
- **Branch / PR:** `feat/synthesis-linked-2d-visuals`, draft PR #49; commit `6b9900d1bfa04dbec7a036c2133fdc8037cca263`.
- **Requirement clarification:** The user's intended workflow is generate/store visuals from already-synthesized content, then retrieve those stored visuals like lesson/topic data.
- **Change:** Approval now generates and persists the per-step visual records immediately and returns `visual_count`; the retrieval path still backfills existing approved lessons that predate this feature. Empty teaching sequences deactivate old visual rows.
- **Verification:** Exact-head backend tests, Android build, and emulator smoke must rerun after this change. No merge or deployment performed.


### 2026-10-28 — Add a real SQLite persistence regression test
- **Branch / PR:** `feat/synthesis-linked-2d-visuals`, draft PR #49; test commit `d436d4e2791ccdd0aeddbdf7d8d91083cda036f2`.
- **Purpose:** The earlier visual-builder tests checked mapping in memory but did not prove database persistence or updates after a synthesis caption changes.
- **Change:** Added a temporary-SQLite test that inserts an approved synthesized lesson, verifies the generated visual is stored with its source chunk IDs, then updates the synthesis caption and verifies the stored visual fingerprint and summary update.
- **Verification:** Exact-head backend test run pending. No merge or deployment performed.
