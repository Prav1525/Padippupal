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
