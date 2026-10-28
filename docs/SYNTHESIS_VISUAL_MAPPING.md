# Synthesis-linked lesson visuals

PadippuPal's `chapter_lessons` records are the source of truth. Visuals must be derived from the saved `teaching_sequence`, not guessed from a topic label alone.

## Mapping

1. Load the exact approved lesson using board, class, subject, medium, chapter, and topic filters already used by `/tutor/lesson-plan`.
2. For every saved teaching step, derive one compact visual blueprint from that step's `title`, `caption`, `visual` fields, and `source_chunk_ids`.
3. Store it in `lesson_visual_assets` with a stable lesson/step key, the summary/caption it illustrates, source chunk IDs, and a content fingerprint.
4. Return the stored visual alongside the same approved lesson response. The existing tutor renderer receives an inline `interactive_lesson` object and draws it in the tutor flow.
5. When a lesson synthesis changes, the fingerprint changes and the corresponding step record is updated. Removed steps are marked inactive so stale visual cards do not linger.

## Data contract

- `lesson_id + step_id`: stable mapping from one synthesis step to its visual.
- `summary_text`: the exact lesson caption/summary that the visual accompanies.
- `source_chunk_ids_json`: the source chunks cited by that step; no unrelated topic-only visual is attached.
- `blueprint_json`: a small, renderer-friendly 2D scene recipe (kind, labels, actions, narration sync).
- `content_fingerprint`: stable hash for detecting visual-content changes.

## Visual limits

- Compact 2D vector/card layouts only; no 3D, large animation, or separate overlay/window.
- Labels are copied from the saved synthesis step; this module does not invent textbook facts or create unlicensed textbook-page copies.
- Unsupported or empty visual metadata yields no generated visual rather than a misleading image.
- The visual endpoint only serves approved synthesized lessons: `GET /chapter-lessons/{lesson_id}/visuals`.

## Verification still required

Run backend tests and Android JVM/APK/emulator checks against the exact head. In particular, confirm the API's `synthesized_visuals` and `interactive_lesson` payload is rendered inside the live tutor screen and that its layout remains compact at phone width. This feature is not considered learner-ready until those checks pass.