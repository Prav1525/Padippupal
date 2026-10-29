# PadippuPal Visual Teaching and Drawing Generation Standard

## Non-negotiable learner experience
- Teach in one continuous tutor flow. A sketch belongs immediately beside/below the exact sentence it explains, inside the same scrolling lesson content.
- Never use a floating overlay, modal, separate drawing window, detached interactive mini-game, or independent visual card.
- Draw simple, original, flat 2D teacher sketches. Prefer clear shapes, arrows, labels and a few meaningful objects over decorative circles, emoji-only diagrams, or generic placeholders.
- A diagram must explain the concept. If the evidence is insufficient, show no diagram and record the topic as needing review; never invent textbook facts.
- Use readable Tamil/Tanglish/English text from the selected lesson medium. Keep labels short and check for clipping/overlap.

## Source and evidence policy
1. Resolve the exact saved lesson by board, grade, subject, medium, chapter and topic.
2. Read its saved teaching sequence and source-chunk/page references before planning visuals.
3. For textbook-specific diagrams, inspect the permitted, correct-edition textbook page first. NCERT's current official portal is https://ncert.nic.in/ . Record edition/year, page, and what was actually observed. Never label a drawing "textbook-verified" based only on a topic title or OCR text.
4. Research a concept with primary educational sources. NotebookLM/Gemini Notebook (https://notebooklm.google.com/) can help ground research in uploaded sources; verify important facts against the actual source.
5. Use PhET (https://phet.colorado.edu/) for research-based science/math behaviour and GeoGebra (https://www.geogebra.org/) for mathematical relationships. These are reference/validation aids, not assets to blindly copy.
6. Excalidraw (https://excalidraw.com/) is a useful hand-drawn-style reference/prototyping tool. Final app assets should be original, lightweight vector drawings implemented in the project renderer, not screenshots or copied textbook pages.

## Per-topic workflow
1. Inventory every approved synthesized lesson. Deduplicate by exact board/grade/subject/medium/chapter/topic key.
2. Write one child-friendly learning objective and list the 2–5 facts the drawing must communicate.
3. Create a visual plan for each narration beat: scene type, objects, spatial relationships, arrows, labels, and what changes from one step to the next.
4. Match the renderer to the concept (e.g. particle spacing, labelled plant, water-cycle arrows, material sorting, magnetic poles, thermometer scale, filtration layers, Sun–Earth–Moon). Do not route unrelated topics to one generic fallback.
5. Draw a static, accessible 2D scene. Keep one main idea per frame, strong contrast, short labels, adequate touch-independent legibility, and no misleading scale/orbits unless stated as schematic.
6. Add exact source-chunk IDs, page references, lesson key, version and evidence status to the asset record.
7. Persist and map the visual to the exact lesson/teaching step. Avoid topic-name substring matching when a stable ID exists.
8. Test at least one screenshot per visual family and all high-risk concepts (e.g. circuits, phases, day/night, water cycle, particle states). Verify the sketch progresses in sync with narration.
9. Audit every chapter. Track counts for reviewed, source-verified, implemented, tested, and blocked. Do not call the catalogue complete until each item has evidence and a passing screenshot test.

## Inline layout contract
- Explanation text and its corresponding drawing are siblings in the same vertically scrolling content column.
- Do not place the drawing in a separate Surface/card solely to display it. Use no elevation, floating window, overlay, or independent pane.
- Avoid nested weighted columns that stretch content and leave a blank band. Let lesson content wrap naturally; keep transport controls in the normal screen layout.
- The drawing must not push the narration caption off-screen. Use a single scroll owner for the lesson body, predictable content sizing, and responsive canvas height.
- A screenshot acceptance test must inspect the actual rendered UI, not only test strings or successful APK compilation.

## Required asset fields
`board`, `class_level`, `subject`, `medium`, `chapter`, `topic`, stable lesson/step IDs, `visual_kind`, `visual_subtype`, `nodes`, `actions`, `spatial_relationships`, `teaching_order`, `source_chunk_ids`, `reference_page_numbers`, `source_edition`, `evidence_status`, `content_fingerprint`, `review_status`, and renderer version.

Allowed evidence statuses: `source_verified`, `concept_source_verified`, `text_only_inference`, `needs_review`. Never upgrade evidence status automatically.

## Release gate
- Correct concept and topic mapping; no generic fallback presented as a finished science illustration.
- Text and drawing agree with the selected lesson language and source.
- No overlay, modal, detached card, blank lower band, clipping, or overlap.
- Drawing appears inline at the intended narration beat.
- Android build, unit tests, API tests and emulator screenshot review all pass on the exact commit.
- If a check was not run, state that plainly. A passing build is not proof of educational quality.

## Current science scope
The first CBSE Class 6 science blueprint catalogue in `SCIENCE_VISUAL_BLUEPRINTS.md` covers 36 initial topics across 11 chapters. These are design plans, not claims that live database assets are already synthesized, persisted, textbook-verified, or deployed. Verify against the exact current NCERT Curiosity edition before marking any chapter complete.
