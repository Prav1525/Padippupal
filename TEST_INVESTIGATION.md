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
