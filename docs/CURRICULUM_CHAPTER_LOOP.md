# PadippuPal Curriculum Chapter Loop — Persistent Queue

**Owner intent:** Continue chapter-by-chapter and topic-by-topic without requiring the owner to approve each ordinary review step.  
**Mandatory standard:** [Chapter quality and inline visual workflow](CHAPTER_QUALITY_AND_INLINE_VISUAL_WORKFLOW.md)  
**Working branch:** `fix/teacher-drawn-inline-tanglish`  
**PR:** [#55](https://github.com/Prav1525/Padippupal/pull/55) — draft; do not merge or deploy without explicit owner approval.  
**Safety boundaries:** Database reads are allowed for evidence. Do not mutate production curriculum rows, approve content, merge, deploy, or publish to learners autonomously.

## How the loop resumes
1. Read this queue and the workflow standard.
2. Check branch/PR head and latest CI.
3. Read live DB records and cited source chunks.
4. Make one coherent, reviewable slice on the working branch.
5. Update this queue with exact commit SHA, tests, blockers and next item.
6. If blocked, record why and move to the next safe item.
7. Report only verified work; never describe a draft as deployed.

## Queue and current progress

### In progress — Chapter 1: The Wonderful World of Science (Grade 6, NCERT Curiosity 2026–27)
- [x] Store cross-chapter quality workflow.
- [x] Inspect canonical chapter lesson and topic synthesis rows.
- [x] Inspect stored source chunk references for pages 1–8; exact textbook page-image review remains outstanding.
- [x] Record OCR/header/footer contamination, overlapping topic spans and the previously observed timestamp-triggered fraction visual.
- [x] Draft source-grounded seven-beat English/Tanglish sequence and inline storyboard.
- [x] Re-query live DB: 11 synthesis rows (7 approved page-part rows, 4 broad drafts); findings in [Chapter 1 live synthesis audit](CHAPTER_1_LIVE_SYNTHESIS_AUDIT.md).
- [ ] Review sequence against exact textbook page images where accessible.
- [ ] Reconcile broad draft rows with seven part rows using version-safe supersession; do not silently delete or approve rows.
- [x] Fix the observed Chapter 1 closing-step inference bug: “never stop wondering” was incorrectly classified as collaborative exploration; removed that phrase from the collaboration trigger so the dedicated curiosity rule can handle it. CI exposed a second edge in the same regression (Step 7 then had no inferred visual). Added explicit `never stop wondering` / `keep wondering` phrases to the curiosity trigger. Later exact-head CI passed on `c9197923`.
- [ ] Persist visuals only through a reviewed, supported write path; no production DB mutation in this loop.
- [ ] Verify visual rows by DB read-back in approved test/staging path.
- [x] Run curriculum tests, Android build and UI smoke on `c9197923`; all three workflows passed.
- [x] Inspect fresh emulator screenshot artifact from run `40875190509`: no separate card/overlay and spoken-word highlight moves, but the Canvas expands to a large blank band and the All 1s scene shows only one point. This is a confirmed UI defect; fixed the live Canvas to use content-sized height and made repeated-ones show all five terms in commit `5be1b49e`.
- [ ] Re-run exact-head CI and inspect a fresh screenshot after `5be1b49e`; visual acceptance remains pending.
- [ ] Mark status only as evidence supports.

### In progress — A Journey through States of Water (Grade 6 Science)
- [x] Query live synthesis rows from exact source ID `ed0b5f40-e9e0-474d-82ac-9681b0f4c1cd`.
- [x] Create [initial live DB audit](CHAPTER_8_STATES_OF_WATER_LIVE_AUDIT.md) with row-level OCR/segmentation defects and topic-specific visual storyboard.
- [x] Reconcile page count: live source/chunk inventory spans 20 PDF pages (printed textbook pages 143–162); the earlier 24-page reference was not the PDF page count. Exact page-image review remains outstanding.
- [x] Audit full synthesis inventory: 16 rows total, 8 approved page-part rows (Parts 1–8) and 8 broad draft topics; Part 8 is OCR-contaminated end-of-chapter assessment content.
- [ ] Reconcile eight broad draft concepts with approved part rows (overlapping spans currently 1–20).
- [ ] Inspect exact source page images and verify condensation, evaporation, cooling-effect and water-cycle wording.
- [ ] Inspect active visuals by exact lesson ID and source chunk mapping; add regression tests.
- [ ] Apply the same CI and screenshot acceptance gates before calling the chapter complete.

### Remaining chapters
Continue through the canonical Grade 6 Science chapter list in source order, followed by Mathematics. Each chapter gets an audit and storyboard. Do not reuse drawings merely because another chapter has similar keywords.

## Definition of done (per chapter)
Every topic reviewed against source evidence; visuals mapped to exact topic/step; asset persistence read back from DB; relevant automated tests pass; actual tutor screen visually inspected. Otherwise label **in progress**, **blocked**, or **source gap**.

## Artifacts
- `docs/CHAPTER_QUALITY_AND_INLINE_VISUAL_WORKFLOW.md`
- `docs/CURRICULUM_CHAPTER_LOOP.md`
- `docs/CHAPTER_1_REVISED_TEACHING_SEQUENCE.md`
- `docs/CHAPTER_1_SCIENCE_DB_VISUAL_AUDIT.md`
- `docs/CHAPTER_1_LIVE_SYNTHESIS_AUDIT.md`
- `docs/CHAPTER_8_STATES_OF_WATER_LIVE_AUDIT.md`

## Run log
| Date (IST) | Result | Next item |
|---|---|---|
| 2026-10-29 | Exact-head checks passed on `c9197923` (curriculum tests, APK build, guidance gate, API-35 emulator UI smoke). Screenshot review exposed the remaining large blank band caused by `Modifier.weight(1f)` and a one-point All 1s sketch. Fixed content-sized Canvas and repeated-ones sketch in `5be1b49e`; this fix is not yet validated by CI/screenshot. No production DB writes, approvals, merge or deployment. | Check CI on `5be1b49e`, inspect fresh screenshot, then continue Chapter 1 source-page review and synthesis reconciliation. |
