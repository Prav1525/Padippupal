# Known issues and unresolved risks

**Last reconciled:** 2026-10-30  
These are evidence-backed gaps or explicit verification needs from inspected repository documentation and GitHub state. Re-check before treating any item as current.

## KI-001 — Official curriculum source approval is incomplete
- **Evidence:** `backend/README.md` states no source is approved for automatic ingestion and exact file/reuse permissions remain to be verified.
- **Risk:** A generated lesson or diagram may be mistaken for official textbook-grounded content.
- **Required action:** Verify board, edition, exact source, page references, and legal/usage permissions before claiming official grounding or ingesting/reproducing content.
- **Status:** Open at snapshot; re-check source registry.

## KI-002 — Prototype and roadmap claims can be confused
- **Evidence:** Root README describes the app as a prototype and lists material incomplete areas including OCR, full chapter generation, concept mastery, and PDF export.
- **Risk:** A feature may be described as live based on a roadmap, branch, or demo rather than a merged/deployed implementation.
- **Required action:** Verify code, API, deployed commit, and target learner journey before marking shipped.
- **Status:** Open; requires per-feature verification.

## KI-003 — Synthesis-to-visual pipeline needs end-to-end verification
- **Evidence:** `docs/SYNTHESIS_VISUAL_MAPPING.md` describes the intended mapping and explicitly lists API payload/rendering and Android checks still required. Multiple visual-related PRs are open.
- **Risk:** Visuals may exist in storage or CI but fail to render inline, map to the wrong step, or become stale.
- **Required action:** Trace synthesis write -> visual persistence -> retrieval -> Android model mapping -> inline rendering and verify on the exact tested commit.
- **Status:** Open; inspect PRs #56, #57, #59 and current main before selecting the next implementation.

## KI-004 — Beyond Earth whiteboard pilot not yet release-verified
- **Evidence:** PR #59 was open at head `0383b1fe9690ff3c97dcc901c64710be04ddba14`; its description says Android build and chapter-specific visual verification are required before merge.
- **Risk:** A structured database record or code build may be mistaken for an accurate child-facing visual experience.
- **Required action:** Check latest CI on the exact PR head, inspect emulator screenshots/accessibility state, verify all teaching stages/labels/reveal/narration, and check content against authoritative source evidence. Keep test DB separate from production.
- **Status:** Open at snapshot; re-fetch PR and workflows.

## KI-005 — Tutor implementation has high coupling
- **Evidence:** Tutor behavior, playback, captions, and inline visual rendering are concentrated in the large `TutorScreen.kt` file.
- **Risk:** Small UI changes can affect playback, state restoration, language, visuals, or navigation.
- **Required action:** Trace affected state and add focused regression coverage; consider modularization only as a separately scoped design task.
- **Status:** Ongoing architectural risk.

## KI-006 — Speech synchronization has known limits
- **Evidence:** `docs/LIVE_TEACHING_DESIGN.md` distinguishes phrase-level playback synchronization from exact word-level alignment and describes missing/unfinished lifecycle capabilities.
- **Risk:** UI may claim precise word synchronization or interruption recovery without actual timing support.
- **Required action:** Verify current provider callbacks and target device behavior; use phrase-level fallback unless genuine alignment timestamps are available.
- **Status:** Verify current implementation before each speech feature.

## KI-007 — Background ingestion/worker scaling is limited
- **Evidence:** `backend/README.md` describes an in-process worker and recommends a durable queue/object storage for multi-instance production.
- **Risk:** Jobs may not scale safely or remain durable under multi-instance deployment.
- **Required action:** Inspect current deployment topology and persistence before changing ingestion/worker behavior.
- **Status:** Open per inspected backend documentation.

## KI-008 — Existing engineering-process PRs may overlap
- **Evidence:** PR #14, #15, #18 and #22 were open at the snapshot; #22 contains an expanded `AGENTS.md` work-entry protocol on its branch.
- **Risk:** Duplicate instructions, workflows, or automation may be created.
- **Required action:** Review those PRs before Phase 2 automation; do not merge them without explicit approval.
- **Status:** Open at snapshot; re-fetch.
