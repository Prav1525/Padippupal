# Synthesis-linked lesson visuals

PadippuPal's `chapter_lessons` records are the source of truth. Visuals must be derived from the saved `teaching_sequence`, not guessed from a topic label alone.

## Mapping

1. Load the exact approved lesson using board, class, subject, medium, chapter, and topic filters already used by `/tutor/lesson-plan`.
2. During approved PDF ingestion, transiently render only candidate figure pages and ask the configured vision model for a concise structural description (concept, objects, relationships, labels and teaching order). Rendered page images are discarded; only the description and page number are appended to the source text. ZIP ingestion uses the same path.
3. During synthesis, use those explicit figure-reference descriptions as structural evidence. The model must create an original composition and artwork—not trace or reproduce textbook illustration style—and include supported objects, relationships, reveal actions, narration sync phrases and reference page numbers.
4. For every saved teaching step, generate a compact 2D vector blueprint from that step's `title`, `caption`, `visual` fields, reference page numbers and `source_chunk_ids`. The blueprint and SVG are stored together in `blueprint_json`.
5. Store it in `lesson_visual_assets` with a stable lesson/step key, the summary/caption it illustrates, source chunk IDs, page references and a content fingerprint.
6. Return the stored visual alongside the same approved lesson response. The tutor renderer draws the visual in the same content flow and reveals its diagram parts once as speech progress moves through the teaching steps.
7. When a lesson synthesis changes, the fingerprint changes and the corresponding step record is updated. Removed steps are marked inactive so stale visual cards do not linger.

## Data contract

- `lesson_id + step_id`: stable mapping from one synthesis step to its visual.
- `summary_text`: the exact lesson caption/summary that the visual accompanies.
- `source_chunk_ids_json`: the source chunks cited by that step; no unrelated topic-only visual is attached.
- `blueprint_json`: a small, renderer-friendly 2D scene recipe plus generated SVG markup (kind, labels, spatial relationships, teaching order, reveal actions, narration sync, and explicit textbook reference pages where available).
- `content_fingerprint`: stable hash for detecting visual-content changes.

## Visual limits

- Compact 2D vector layouts only; one-shot staggered reveal capped at 850 ms per step. No 3D, large animation, looping, overlay or separate window.
- Page screenshots and extracted image bytes are not persisted. Only structural descriptions and source page numbers are retained.
- Artwork, composition and styling are original. The figure-reference analysis preserves educational relationships, not the source illustration's expressive details.
- Labels and relationships must be grounded in synthesis/source evidence; no guessed page numbers or unsupported textbook facts.
- Unsupported or empty visual metadata yields no generated visual rather than a misleading image.
- The visual endpoint only serves approved synthesized lessons: `GET /chapter-lessons/{lesson_id}/visuals`.

## Important limitation

Vision analysis is optional and requires `GEMINI_API_KEY` at ingestion time. If the key is absent or figure analysis fails, the source remains ingestible but the response reports zero analyzed visual-reference pages; synthesis can only make a simple original concept diagram from the available text. This fallback must not be described as a verified match to the textbook figure.

Existing source records retain extracted text and chunk/page metadata, not the original PDF bytes. Therefore, sources ingested before figure analysis was enabled cannot be truthfully backfilled with textbook-figure comparisons from the database alone. Re-upload the approved source PDF through the admin ingestion flow to analyze its figure pages; keep the resulting visual references tied to the exact source and page. Until that happens, visuals inferred from old synthesis captions are text-grounded teaching diagrams, not verified recreations of a specific textbook figure.

## Verification still required

Run backend tests and Android JVM/APK/emulator checks against the exact head. In particular, confirm the API's `synthesized_visuals` and `interactive_lesson` payload is rendered inside the live tutor screen and that its layout remains compact at phone width. This feature is not considered learner-ready until those checks pass.

Validation note: CI must be run against the full head while this branch is temporarily targeted at `main`; after validation, the draft PR will return to its intended stacked base (`ui/modern-learner-layout`).

Exact-topic binding regression assertions were added; rerun backend and Android checks against the updated branch head before considering the draft complete.
