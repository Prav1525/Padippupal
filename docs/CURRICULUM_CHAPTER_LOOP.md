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
- [x] Re-query live DB: 11 synthesis rows (7 approved page-part rows, 4 broad drafts); specific findings in [Chapter 1 live synthesis audit](CHAPTER_1_LIVE_SYNTHESIS_AUDIT.md).
- [ ] Review sequence against exact textbook page images where accessible.
- [ ] Reconcile broad draft rows with the seven part rows using version-safe supersession; do not silently delete or approve rows.
- [ ] Fix/test concept-to-visual inference and all seven stage mappings, including timestamp/header false-positive regression.
- [ ] Persist visuals only through a reviewed, supported write path; this loop must not mutate production curriculum rows.
- [ ] Verify visual rows by DB read-back in an approved test/staging path.
- [ ] Run curriculum tests, Android build and UI smoke on latest commit.
- [ ] Inspect fresh screenshots for inline flow, no overlay/card, no large blank gaps, readable labels.
- [ ] Mark status only as evidence supports.

### Next candidate — A Journey through States of Water
Live DB contains both draft and approved lesson rows for this Grade 6 Science chapter, sourced from `fecu108.pdf` (24 pages). Reconcile row status, lesson JSON, source chunks and synthesis rows before editing. Then process remaining Grade 6 Science chapters in canonical source order, followed by Mathematics. Each chapter gets an audit and storyboard; never reuse drawings just because another chapter has similar keywords.

## Definition of done (per chapter)
Every topic reviewed against source evidence; visuals mapped to exact topic/step; asset persistence read back from DB; relevant automated tests pass; actual tutor screen visually inspected. Otherwise label **in progress**, **blocked**, or **source gap**.

## Artifacts
- `docs/CHAPTER_QUALITY_AND_INLINE_VISUAL_WORKFLOW.md`
- `docs/CHAPTER_1_REVISED_TEACHING_SEQUENCE.md`
- `docs/CHAPTER_1_SCIENCE_DB_VISUAL_AUDIT.md`
- `docs/CHAPTER_1_LIVE_SYNTHESIS_AUDIT.md`

## Run log
| Date (IST) | Result | Next item |
|---|---|---|
| 2026-10-29 | Workflow and Chapter 1 teaching-sequence draft exist. Live read-only query confirms 11 synthesis rows (7 approved part rows, 4 broad drafts), OCR contamination and overlapping spans. No production DB writes, approvals, merge or deployment. | Verify textbook page images; reconcile Chapter 1 synthesis and visual inference; then audit States of Water. |
