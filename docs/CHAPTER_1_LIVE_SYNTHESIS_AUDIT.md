# Chapter 1 — Live database synthesis audit (evidence snapshot)

**Status:** In progress; not approved for replacement or release.  
**Source:** Neon project `raspy-hat-20043046`, main branch `br-jolly-haze-azhqgco9`. Read-only queries only.  
**Textbook source row:** `28077c43-b7fe-4a40-85c8-663b8ac326a2` — NCERT Curiosity Class 6 Science, Reprint 2026–27, `fecu101.pdf`, 8 pages.  
**Canonical lesson row:** `24297054-ccec-55ce-8428-ac94cbe0b79f` (see prior audit; lesson status and exact JSON should be re-read before any migration).

## Live synthesis inventory

Query of `syllabus_topic_syntheses` filtered by the exact source ID returned **11 rows: 7 approved part rows and 4 drafts**. All rows reported `validation_status=passed`; this does not prove teaching quality, source-span precision, or visual suitability.

| Topic row | Status | Pages | Evidence-based issue |
|---|---|---:|---|
| The Wonderful World of Science — Part 1 | approved | 1–1 | Caption includes malformed phrase “Or watched a flower bloom”; generic teacher-says/checkpoint template. |
| The Wonderful World of Science — Part 2 | approved | 2–2 | Caption includes running header/page contamination: “The Wonderful World of Science 3 daily lives.” Actual citation refs span pages 2–3. |
| The Wonderful World of Science — Part 3 | approved | 4–4 | Caption includes running header “The Wonderful World of Science 5” inside passage; visual should show listed objects/materials rather than a generic magnet/poles drawing. |
| The Wonderful World of Science — Part 4 | approved | 5–5 | OCR split “fi nd”; text appears to splice pen troubleshooting and scientific-method introduction. |
| The Wonderful World of Science — Part 5 | approved | 6–6 | Caption contains exercise/header/OCR contamination including “scientifi c”, “Chapter 1.indd 6”, timestamp “10/18/2024 9:49:28 AM”, and next-page header. Must never be interpreted as fraction/math content. |
| The Wonderful World of Science — Part 6 | approved | 7–7 | Caption begins mid-sentence from prior page; content mixes everyday examples with the journey-ahead message. |
| The Wonderful World of Science — Part 7 | approved | 8–8 | Generic template and page-local extract only; should serve as a short, accurate closing. |
| Welcome to the Wonderful World of Science | draft | 1–8 | Broad span overlaps Part 1; potential duplicate topic. |
| Science as an Endless Jigsaw Puzzle | draft | 1–8 | Broad span overlaps Parts 2–3; metaphor should not imply all discoveries are linear. |
| Applying the Scientific Method in Daily Life | draft | 1–8 | Broad span overlaps Parts 4–6; too broad for precise source mapping. |
| Collaborative Exploration and the Journey Ahead | draft | 1–8 | Broad span overlaps Parts 6–7; potential duplicate topic. |

**Citation refs observed in database:** Part 1: `85e8fe7b-ba04-45e3-8e88-54770f76a11b`, `540d5b48-97fc-4a93-8251-1b3e177b4b61`; Part 2: `c87f3be1-35c5-4b1e-b769-2e53850f6de5`, `51c5eeae-dcb2-4c04-a2ef-90e7fe5f6fc0`; Part 3: `f03c46cb-1a45-403b-89b1-7a56640e8b08`, `4a6a000d-ae81-4737-8121-f52375ed449c`; Parts 4–7 citation IDs are preserved in the live rows and the revised sequence draft.

## Visual asset evidence

Prior read-only inspection found two active `lesson_visual_assets` rows for the Chapter 1 lesson and zero matching rows in `tutor_topic_visual_assets` for the chapter profile key. This requires a fresh exact join/read-back before concluding current state. A prior asset attached to the scientific-method passage used `visual_kind=fraction` with node `10/18` and label `Equal parts`; this is a false-positive caused by the PDF timestamp and is a **blocking content/visual defect** until corrected through the approved asset workflow.

## Required remediation (safe sequence)

1. Re-read the canonical source chunks and, where available, the actual PDF page images for pages 1–8. Treat OCR text as a retrieval aid, not definitive page proof.
2. Preserve the seven part-row IDs and citations while preparing a reviewed new synthesis version; do not overwrite approved rows in place.
3. Resolve the four broad draft duplicates through explicit version/supersession semantics; do not silently delete or approve them.
4. Create a distinct storyboard per teaching beat: curiosity/observation; jigsaw metaphor; objects/materials plus water states; test a tentative pen-ink hypothesis; scientific-method loop; everyday questions plus collaboration; keep exploring.
5. Eliminate timestamp-triggered fraction visual. Add a regression test for dates/page headers not classifying a lesson as fractions.
6. Use a supported application write path or a reviewed staging migration only; production remains read-only in this workflow.
7. Read back saved visual rows, run curriculum and Android tests on the exact SHA, and inspect fresh screenshots for inline flow/no overlay/no empty gap.
8. Keep status **in progress** until every gate is proven.

## Current run conclusion

The live database query confirms that the source content needs editorial cleanup despite `validation_status=passed`. It does **not** authorize changing approval states. The seven-beat teaching proposal is in `CHAPTER_1_REVISED_TEACHING_SEQUENCE.md`; it remains an editorial draft pending page-image verification and review.
