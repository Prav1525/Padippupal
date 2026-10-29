# PadippuPal Curriculum Chapter Loop — Persistent Queue

**Owner intent:** Continue chapter-by-chapter and topic-by-topic without requiring the owner to approve each ordinary review step.  
**Mandatory standard:** [Chapter quality and inline visual workflow](CHAPTER_QUALITY_AND_INLINE_VISUAL_WORKFLOW.md)  
**Working branch:** `fix/teacher-drawn-inline-tanglish`  
**PR:** [#55](https://github.com/Prav1525/Padippupal/pull/55) — draft; do not merge or deploy without explicit owner approval.  
**Safety boundaries:** Database reads are allowed for evidence. Do not mutate production curriculum rows, approve content, merge, deploy, or publish to learners autonomously.

## How the loop resumes

At the start of each run:
1. Read this queue and the workflow standard.
2. Check the branch/PR head and latest CI results.
3. Read the next topic/chapter from the database and cited source chunks; never rely on a previous summary when live evidence is available.
4. Do one coherent, reviewable slice of work; commit docs/code/tests on the working branch.
5. Update this queue with evidence, exact commit SHA, tests, unresolved blockers and next item.
6. Continue to the next safe topic if a blocker requires owner action. Never wait for ordinary confirmation.
7. Report only verified work and do not describe a draft as deployed.

## Queue and current progress

### In progress — Chapter 1: The Wonderful World of Science (Grade 6, NCERT Curiosity 2026–27)
- [x] Store cross-chapter quality workflow.
- [x] Inspect canonical chapter lesson and topic synthesis rows in database.
- [x] Inspect cited source chunks for pages 1–8.
- [x] Record known defects: OCR/header/footer contamination, duplicated source fragments, weak source-topic alignment, and a fraction visual incorrectly triggered by page timestamp `10/18`.
- [x] Draft a source-grounded seven-beat English/Tanglish tutor sequence and topic-specific inline storyboard.
- [ ] Review the proposed sequence against exact textbook page images where accessible; record provenance and any limitations.
- [ ] Reconcile all 11 synthesis rows (7 approved, 4 draft) with the seven lesson stages; identify duplicates/stale versions and recommend version-safe changes.
- [ ] Fix and test concept-to-visual inference and all seven stage mappings.
- [ ] Persist visuals through the application’s supported write path only after a safe migration/upsert design is reviewed; do not mutate production DB in this autonomous loop.
- [ ] Verify active visual rows by DB read-back in an approved test/staging path.
- [ ] Run curriculum tests, Android build and UI smoke on latest commit.
- [ ] Inspect fresh tutor-screen screenshot(s): inline flow, no overlay/card, no large blank gaps, readable labels.
- [ ] Close audit and mark status only as evidence supports.

### Next chapters
- Discover canonical chapter inventory and source/lesson/topic counts from the database.
- Process chapters in stable curriculum order, then topics in source order.
- Create `docs/CHAPTER_<n>_<slug>_AUDIT.md` and a source-grounded storyboard/revision artifact for each chapter.
- Do not copy Chapter 1's drawings into other chapters; reuse the quality gates and choose visuals specific to each concept.

## Definition of done (per chapter)

A chapter is not complete until every topic has been reviewed against source evidence; every required visual is mapped to the exact topic/step; asset persistence is read back from the database; relevant automated tests pass; and the actual tutor screen has been visually inspected. Otherwise use **in progress**, **blocked**, or **source gap**.

## Latest recorded repository artifacts
- `docs/CHAPTER_QUALITY_AND_INLINE_VISUAL_WORKFLOW.md`
- `docs/CHAPTER_1_REVISED_TEACHING_SEQUENCE.md`
- `docs/CHAPTER_1_SCIENCE_DB_VISUAL_AUDIT.md`

## Run log

| Date (IST) | Result | Next item |
|---|---|---|
| 2026-10-29 | Workflow stored; Chapter 1 source-grounded teaching-sequence draft stored; live DB remains read-only; PR #55 remains draft. | Verify textbook page imagery and reconcile Chapter 1 synthesis rows. |
