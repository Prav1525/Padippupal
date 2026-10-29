# PadippuPal Topic-Aware Visual Engine

A deterministic, source-gated drawing program for curriculum visuals. It combines three tools with distinct roles:

1. Custom SVG renderer — production-ready, scalable 2D drawings for inline Android display.
2. Excalidraw export — editable hand-drawn-style storyboard/prototype for teacher review.
3. Manim scene export — optional math/process animation source; render it in a separate build environment when animation adds genuine teaching value.

AI may help draft a storyboard, but must not invent evidence. The CLI rejects missing source references and unsupported topic families rather than silently drawing a generic scene.

## Usage

Python 3.10+; no third-party dependencies for SVG and Excalidraw exports.

    python tools/visual_engine/visual_engine.py list
    python tools/visual_engine/visual_engine.py render --subject Mathematics --chapter "Patterns in Mathematics" --topic "Repeating patterns" --medium English --source-id "NCERT-C6-MATH-PATTERNS" --source-page 12 --evidence-status source_verified --out /tmp/pattern.svg

Use --format excalidraw for editable Excalidraw JSON or --format manim for a Manim Python scene. Manim itself is optional.

## Evidence contract

- source_verified: a reviewer inspected the cited source page.
- concept_source_verified: checked against a reputable concept reference, but exact textbook page/visual not verified.
- needs_review and text_only_inference: blocked from learner-facing output.

The program checks that a source ID and page are supplied and blocks unreviewed evidence. It cannot independently prove a citation is genuine; the review workflow must do that.

## Supported topic-specific families

- Mathematics: repeating patterns, fractions, angles, symmetry.
- Science: states of water, water cycle, magnets, curiosity, knowledge jigsaw, everyday objects, pen inquiry, scientific inquiry, and daily-life problem solving.

Unsupported topics fail closed. Add a tested renderer before enabling another family. The backend visual engine also uses `backend/lesson_visuals.py`, which builds compact inline SVG blueprints from synthesis text plus the exact cited source chunks.

## Automatic synthesis-to-visual pipeline

`backend/app.py` calls `_generate_synthesis_visual_candidates(round_id)` after it persists a synthesis round and topic rows. The same hook runs for a reused synthesis round, making retries idempotent. The pipeline:

1. Reads each topic, its explanation/objectives/examples and exact cited source-chunk IDs.
2. Resolves every cited chunk against the same source. If any citation is missing, it skips the topic instead of drawing from neighbouring content.
3. Passes the synthesis and cited text to the shared topic-aware renderer; generic keyword cards are not used as a fallback.
4. Records the renderer family, source IDs, evidence status, quality flags, SVG and content fingerprint in the visual blueprint.
5. Persists candidates to `tutor_topic_visual_assets` with `active=0`. Approved-topic backfill may promote assets only through the existing approval path. OCR/header/timestamp contamination stays flagged for review.

This creates draft visuals automatically whenever a new synthesis is generated; it does not automatically publish unreviewed drawings to learners. The tutor still needs an end-to-end inline-render verification before a chapter is considered complete.

## Tests and evidence contract

Run `python -m pytest -q backend/test_lesson_visuals.py backend/test_syllabus_synthesis.py` and the visual-engine workflow. Tests cover topic-family selection, SVG generation, source-chunk mapping and contamination flags.

- `source_verified`: a reviewer inspected the cited source page.
- `concept_source_verified`: checked against a reputable concept reference, but exact textbook page/visual not verified.
- `needs_review` and `text_only_inference`: blocked from learner-facing output.

The CLI checks that a source ID and page are supplied and blocks unreviewed evidence. It cannot independently prove a citation is genuine; the review workflow must do that. Never delete or overwrite inactive legacy visuals as part of generation.
