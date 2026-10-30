# Known Issues and Verification Gaps

> Reconcile this file against current source and live systems before acting. Keep resolved issues in history with their evidence rather than deleting them.

## KI-0001 — Beyond Earth PR #59 Android UI smoke gate failing
- **Status:** OPEN / CONFIRMED test-harness failure
- **Evidence:** Workflow run [40989118437](https://github.com/Prav1525/Padippupal/actions/runs/40989118437), job `emulator-smoke (35)`, job ID `123846977986`.
- **Failing test:** `SynthesisInlineVisualContractTests.test_live_smoke_accepts_inline_visual_but_still_rejects_separate_visual_overlay`.
- **Observed mismatch:** Test expects exact source text `"pattern of stars" in joined`; implementation uses an `any(...)` expression with three accepted lesson phrases. The live lesson text in logs contains the expected Beyond Earth explanation and inline visual caption. Script validation failed before emulator E2E, so emulator E2E was skipped.
- **Root cause confidence:** CONFIRMED for the Python test-helper source-contract mismatch. Actual Android visual/runtime correctness remains UNVERIFIED by this run.
- **Next action:** Make the helper assertion semantic/robust (or deliberately align source) and run helper tests; then rerun the complete smoke workflow and inspect emulator evidence.
- **Do not:** Describe this as an app rendering defect or claim runtime acceptance based on this log alone.

## KI-0002 — Architecture call graph and data contracts are incomplete
- **Status:** OPEN / DOCUMENTATION GAP
- **Evidence:** Phase 1 inventory has identified module paths, but has not yet traced all callers, DTOs, DB persistence or deployment dependencies.
- **Next action:** Build a source-backed module map incrementally, recording commit and line references.

## KI-0003 — Official curriculum source approval must be rechecked
- **Status:** OPEN / NEEDS REVALIDATION
- **Evidence:** README says the source registry currently approves no official curriculum text for ingestion at the time it was last edited.
- **Next action:** Inspect `backend/source_registry.json` and rights/provenance policy before claiming official textbook coverage or ingesting content.
