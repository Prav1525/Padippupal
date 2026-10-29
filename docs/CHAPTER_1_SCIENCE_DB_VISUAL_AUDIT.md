# Chapter 1 Science visual audit — database-backed

**Scope:** CBSE, Grade 6, Science, English — *The Wonderful World of Science*  
**Audit date:** 2026-10-29  
**Status:** source record verified; existing stored visuals fail quality checks; renderer fix proposed on PR branch. This is not a claim that the new renderer is live or that the chapter has passed learner acceptance.

## Database evidence inspected

Queried the PadippuPal Neon project `padippupal-curriculum`, default branch `main`, read-only.

- `sources` record: `28077c43-b7fe-4a40-85c8-663b8ac326a2`
- Source title: `NCERT Curiosity Class 6 Science — Chapter PDF (fecu101.pdf)`
- Edition: `Reprint 2026-27`; source status: `ready`; page count: 8.
- Approved `chapter_lessons` record: `24297054-ccec-55ce-8428-ac94cbe0b79f`
- The lesson JSON contains 7 teaching stages. The stages cite source chunk IDs from pages 1–7.
- `syllabus_topic_syntheses`: 11 rows for this chapter, 7 marked approved.
- `lesson_visual_assets`: 2 active records for the approved chapter lesson.
- `tutor_topic_visual_assets`: 0 rows matched this chapter by its profile key.

These are live database observations, not counts inferred from `interactive_lessons.json`.

## Existing asset defects found in the database

1. The Part 3 source chunk lists paper, metal key, plastic ruler, rubber eraser, a magnet, and other everyday objects. Its saved visual has only the generic nodes `Magnet` and `Poles`. That does not represent the cited teaching point.
2. The Part 5 source text is about describing a daily-life scientific method. Its saved visual kind is `fraction`, with the node `10/18` and the label `Equal parts`. This is an OCR/date false positive and is educationally wrong.
3. The stored stages use broad extractive captions and generic checkpoints. Several Tanglish fields are templated rather than truly teaching the stage-specific idea. They need a content-quality pass; a drawing fix alone does not make the chapter fully ready.

## Grounded source map for the seven stages

| Stage | DB source chunk(s) | Pages | Source-grounded visual intent |
|---|---|---:|---|
| 1 | `85e8fe7b-ba04-45e3-8e88-54770f76a11b`, `540d5b48-97fc-4a93-8251-1b3e177b4b61` | 1 | Childlike curiosity: notice a flower or the night sky, wonder, ask why. Do not invent an answer to the question. |
| 2 | `c87f3be1-35c5-4b1e-b769-2e53850f6de5`, `51c5eeae-dcb2-4c04-a2ef-90e7fe5f6fc0` | 2–3 | Jigsaw metaphor: each discovery adds a piece and can lead to new questions. Label it as a metaphor. |
| 3 | `f03c46cb-1a45-403b-89b1-7a56640e8b08`, `4a6a000d-ae81-4737-8121-f52375ed449c` | 4–5 | Show the listed everyday objects without assigning unsupported materials to objects whose material is not stated. |
| 4 | `8caf1fd6-b2f3-436b-a7b9-f37c99e44e99`, `0988f81b-21f7-4e16-9f5b-8224f72a1767` | 5–6 | Pen stops writing → ask why → possible guess → test the guess. Keep a guess distinct from evidence. |
| 5 | `35d81817-d498-4c4c-9d46-d826259ece45`, `d5075a26-dc9d-457b-aab7-de1059240635` | 6–7 | Scientific-method sequence: observe → ask a question → suggest a possible answer → test by experiment/observation → analyse results. |
| 6 | `d5075a26-dc9d-457b-aab7-de1059240635` | 7 | Apply the process to source-listed examples (cooking dal, a flat bicycle tyre, or a bulb/switch). Do not draw an unverified outcome. |
| 7 | Confirm exact stage-to-chunk mapping in current `teaching_sequence` before implementation | Verify | Do not invent a seventh concept. Reconcile the stage text and its source IDs before drawing it. |

## Renderer changes on this branch

`backend/lesson_visuals.py` now has dedicated 2D renderer families for curiosity, the jigsaw metaphor, everyday material examples, and the scientific method. The inference rules put these source-grounded cases before generic fraction matching, preventing OCR fragments such as `10/18` from becoming a fraction lesson. Regression tests were added in `backend/test_lesson_visuals.py`.

## Acceptance gate before marking Chapter 1 complete

- [ ] Re-run backend visual tests and curriculum CI on the exact PR head.
- [ ] Rebuild the active visual records from the approved DB lesson and confirm exact source chunk IDs/page references persist.
- [ ] Inspect the seven stages against the stored source text; fix noisy extractive captions and template Tanglish before claiming content is child-ready.
- [ ] Capture fresh Android emulator screenshots for the live tutor flow and confirm no overlay/card, readable labels, no blank gap, and drawing appears inline with narration.
- [ ] Verify Tanglish speech and captions end-to-end.
- [ ] Only then mark the chapter approved for learners.

**No production database rows were changed by this audit.** The current PR changes are code and regression tests only; they must pass CI and be deployed before they can regenerate persisted visuals.
