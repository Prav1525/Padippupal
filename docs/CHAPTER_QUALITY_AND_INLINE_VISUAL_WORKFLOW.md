# PadippuPal Chapter Synthesis + Inline Visual Quality Standard

**Status:** Required workflow for every chapter before learner release  
**Applies to:** All boards, classes, subjects, media/languages and every chapter delivered in the PadippuPal tutor  
**Source of truth:** The approved lesson/synthesis and source references stored in the curriculum database. Static JSON blueprints are implementation aids, not proof of database coverage.

## Non-negotiable learner experience

1. Teach the exact concept in the selected synthesis topic; do not choose a drawing from chapter name or keyword alone.
2. Place each drawing at the relevant point in the explanation's reading/narration flow. It must not be a popup, overlay, separate visual card, or disconnected mini-game.
3. Eliminate unexplained large blank spaces. Text and drawings share one continuous lesson layout; drawing height is content-driven and bounded. Do not stretch a tiny diagram just to fill the screen. If there is no useful visual for a passage, use a well-designed text/diagram-free layout rather than an irrelevant picture.
4. Drawings must be simple, legible, child-friendly 2D teacher sketches with accurate labels, relationships, units, direction arrows and proportions where they matter.
5. Never mark a visual “textbook verified” unless the exact textbook edition/page/figure was inspected. Record whether it is textbook-derived, source-text-derived, or a teacher-created explanatory sketch.
6. Keep the selected language consistent across lesson text, labels, captions and speech. Tanglish is not a translation of English-only captions; it must explain the same concept naturally.
7. A build passing is not proof of educational correctness or screen quality. No chapter is “complete” until the chapter gates below pass.

## Repeatable chapter workflow

### Gate 0 — Identify the canonical records
- Query the curriculum database for board, class, subject, medium, chapter, topic syntheses, lesson record, approval/validation status, source records, source chunks/pages, and current visual asset rows.
- Record the database project/branch, query date, row counts and stable record IDs in the chapter audit.
- Treat the database as the source of truth. Reconcile duplicate rounds, stale drafts and approved versions; never silently select a stale record.
- If a topic has no usable source reference, mark it **source gap** and ask for/re-ingest the source rather than inventing textbook claims.

### Gate 1 — Re-read and quality-check every synthesis topic
For every topic and teaching step, compare the synthesis to its cited source chunks and, where available, the exact textbook page:
- scientific/factual correctness and completeness;
- age-appropriate, clear teaching language;
- logical teaching order and prerequisite concepts;
- OCR/header/footer/page-number contamination, broken words, repeated passages and truncated sentences;
- examples and worked steps supported by the source;
- assessment/checkpoint alignment with what was actually taught;
- language parity, including natural Tanglish when selected.
Log each defect with record ID, topic, source/page reference, severity and proposed correction. Do not publish content with critical factual errors, unexplained OCR debris or templated filler.

### Gate 2 — Write a visual storyboard from the verified synthesis
For each teaching step, specify:
- exact lesson/topic/step key;
- learning objective and the misconception the visual should prevent;
- visual type and what it depicts;
- labels, units, arrows, ordering and states;
- which details are explicitly source-backed versus explanatory additions;
- source chunk IDs and textbook page/figure where inspected;
- spoken/caption beat at which it appears.
Choose “no visual needed” only with a brief pedagogical reason. Never invent a result, material property, scientific relationship, number, or label to make the drawing look complete.

### Gate 3 — Create the drawing
- Prefer deterministic Compose Canvas/SVG/vector primitives for crisp labels and repeatable layout.
- Use dedicated concept renderers; do not let generic keyword matching or OCR fragments decide the lesson concept.
- Use image/vision tools only as aids for inspecting an approved source page or proposing a storyboard. A generated/AI-interpreted image is not authoritative without review.
- For each visual, create a compact, accurate drawing that works on narrow mobile screens, with adequate contrast, accessible text sizes and no clipping.
- Keep drawing metadata (type, exact topic/step key, source refs, provenance, version/fingerprint and review status) alongside the asset.

### Gate 4 — Persist and map to the database
- Save each approved visual using the application's existing visual-asset schema and exact lesson/topic/step foreign key or canonical key.
- Preserve source chunk IDs/page refs and provenance; never attach an image merely by chapter title or broad keyword.
- Use an idempotent upsert/fingerprint so retries do not create duplicate active assets.
- Validate the persisted rows by reading them back. Confirm one intended active asset per visualized step, no stale conflicting asset, and no orphaned lesson/topic key.
- Do not claim persistence from code or a blueprint file alone.

### Gate 5 — Inline tutor integration and spacing
- Render the drawing directly in the continuous lesson content, in sequence with the relevant paragraph/narration beat.
- No overlay, modal, floating window, detached border/card, or separate interaction surface for ordinary explanatory drawings.
- Use a single vertical flow. Measure actual content height; avoid a fixed large canvas or spacer that creates blank bands.
- Check small and large Android screens, font scaling, long captions, portrait mode, scrolling, and loading/error states.
- If a drawing cannot fit legibly inline, simplify/reflow it; do not silently move it to an overlay.

### Gate 6 — Verify and sign off
Automated:
- unit tests for each visual family and topic-to-visual mapping;
- regression test for OCR/date/header false positives;
- source-ID preservation and persistence/read-back tests;
- no duplicate/orphan active visual assets;
- curriculum API and Android build/tests;
- Tanglish selection and narration-path tests where available.

Manual:
- inspect a fresh emulator screenshot/video of every chapter's lesson flow;
- verify diagram matches the text at the exact moment it appears;
- inspect label legibility, crop/clipping, overlap, blank space and no-overlay rule;
- listen to the selected-language narration and compare it with on-screen text;
- review scientific claims against cited source pages.
Save screenshot references and reviewer notes in the chapter audit.

## Severity and release decision

- **Blocker:** wrong concept/diagram, unsupported factual claim, source mismatch, missing required citation, Tanglish/English mode mismatch, detached overlay/card, clipped/illegible labels, or major blank layout gap.
- **Major:** broken/truncated synthesis, OCR contamination, missing key steps, generic filler, wrong source mapping, stale/duplicate asset.
- **Minor:** nonessential spacing/wording issue that does not change meaning or block reading.

A chapter is **ready** only when all blockers and majors are closed, visual rows have been read back from the database, tests pass on the exact commit, and a human has inspected the actual tutor rendering. Otherwise label it **in progress**, **source gap**, or **blocked**—never imply completion.

## Required chapter audit template

For every chapter, commit an audit containing:
1. scope and database evidence (project/branch, query timestamp, canonical IDs, counts);
2. topic-by-topic synthesis table: source refs/pages, approval status, defects, correction and reviewer status;
3. teaching-step storyboard: objective, inline visual, labels, narration beat, source refs and provenance;
4. asset persistence table: topic/step key, asset ID, active/version/fingerprint, source refs and read-back result;
5. automated test results and exact commit SHA;
6. fresh emulator screenshot references and manual layout/audio checklist;
7. outstanding blockers and explicit release decision.

## Consistency rule

Use this standard unchanged for every chapter. Chapters may have different visual styles because concepts differ, but the evidence, synthesis review, source mapping, persistence, inline layout, tests and release gates must be identical. Work in small reviewable PR commits; do not merge or deploy without the owner's explicit authorization.
