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

## Supported starter families

- Mathematics: repeating patterns, fractions, angles, symmetry.
- Science: states of water, water cycle, magnets.

These are starter renderers, not complete curriculum coverage. Unsupported topics fail closed. Add a topic-specific renderer and tests before enabling another family.

## Outputs and app integration

SVG metadata records subject/chapter/topic, medium, source, page, evidence status and renderer version. This first implementation is not yet wired to the live Neon database or Android tutor UI. Integration must persist the asset against stable synthesis/step IDs and source chunk IDs, read it back, then verify inline display. Never delete or overwrite inactive legacy visuals as part of generation.
