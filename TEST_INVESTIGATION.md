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
