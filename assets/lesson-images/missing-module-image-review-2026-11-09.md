# Class 6 missing-module image review — production cross-check

Date: 2026-11-09
Branch: `feat/lesson-visual-curation-pipeline`
Scope: 88 modules unmapped by the current 82-entry authoring manifest.

## Evidence checked

- Production curriculum: approved Class 6 Mathematics and Science teaching sequences, 170 modules across 22 chapters.
- Feature-branch authoring manifest: 82 mappings; no duplicate mappings, unknown lesson/module IDs, or step-ID mismatches in the earlier audit.
- Production `lesson_image_assets` table: 20 records covering 8 distinct lesson/module combinations.
- Production records: 19 JPEG records have no `source_url`, `source_page_url`, `license_name`, `license_url`, `creator`, or `attribution`; 1 PNG is pending with provenance recorded.
- The pending PNG is a constellation chart for Beyond Earth module 2: Emagone, CC BY-SA 4.0. It is pending, not learner-approved.
- The 19 JPEG records cannot be counted as verified/licensed web assets. Their image bytes were not downloaded/visually inspected during this audit.

## Key distinction

The 82 manifest mappings are in the feature branch and are not equivalent to production image records. In production, only 8 module combinations currently have records. Do not claim the feature-branch images are live in the tutor.

## Module-by-module queue

All rows below are review proposals, not final approvals. The caption excerpt is the basis for the initial route; full lesson context and visual accuracy must be checked before generating or ingesting. "No image" is an acceptable outcome where a visual adds no instructional value.

| Subject | Chapter | Module / step | Proposed route | Module |
|---|---|---|---|---|
| Mathematics | Data Handling and Presentation | module-1 (step_1) | ORIGINAL_DIAGRAM | Data Handling and Presentation — Part 1 |
| Mathematics | Data Handling and Presentation | module-2 (step_2) | ORIGINAL_DIAGRAM | Data Handling and Presentation — Part 2 |
| Mathematics | Data Handling and Presentation | module-5 (step_5) | ORIGINAL_DIAGRAM | Data Handling and Presentation — Part 5 |
| Mathematics | Data Handling and Presentation | module-6 (step_6) | ORIGINAL_DIAGRAM | Data Handling and Presentation — Part 6 |
| Mathematics | Data Handling and Presentation | module-7 (step_7) | ORIGINAL_DIAGRAM | Data Handling and Presentation — Part 7 |
| Mathematics | Data Handling and Presentation | module-8 (step_8) | ORIGINAL_DIAGRAM | Data Handling and Presentation — Part 8 |
| Mathematics | Fractions | module-4 (step_4) | ORIGINAL_DIAGRAM | Fractions — Part 4 |
| Mathematics | Fractions | module-6 (step_6) | ORIGINAL_DIAGRAM | Fractions — Part 6 |
| Mathematics | Fractions | module-7 (step_7) | ORIGINAL_DIAGRAM | Fractions — Part 7 |
| Mathematics | Lines and Angles | module-3 (step_3) | ORIGINAL_DIAGRAM | Lines and Angles — Part 3 |
| Mathematics | Number Play | module-1 (step_1) | HUMAN_REVIEW | Number Play — Part 1 |
| Mathematics | Number Play | module-2 (step_2) | ORIGINAL_DIAGRAM | Number Play — Part 2 |
| Mathematics | Number Play | module-3 (step_3) | ORIGINAL_DIAGRAM | Number Play — Part 3 |
| Mathematics | Number Play | module-4 (step_4) | HUMAN_REVIEW | Number Play — Part 4 |
| Mathematics | Number Play | module-5 (step_5) | ORIGINAL_DIAGRAM | Number Play — Part 5 |
| Mathematics | Number Play | module-7 (step_7) | ORIGINAL_DIAGRAM | Number Play — Part 7 |
| Mathematics | Patterns in Mathematics | module-5 (step_5) | ORIGINAL_DIAGRAM | Patterns in Mathematics — Part 5 |
| Mathematics | Perimeter and Area | module-7 (step_7) | ORIGINAL_DIAGRAM | Perimeter and Area — Part 7 |
| Mathematics | Playing with Constructions | module-1 (step_1) | ORIGINAL_DIAGRAM | Playing with Constructions — Part 1 |
| Mathematics | Playing with Constructions | module-3 (step_3) | ORIGINAL_DIAGRAM | Playing with Constructions — Part 3 |
| Mathematics | Playing with Constructions | module-4 (step_4) | ORIGINAL_DIAGRAM | Playing with Constructions — Part 4 |
| Mathematics | Playing with Constructions | module-5 (step_5) | ORIGINAL_DIAGRAM | Playing with Constructions — Part 5 |
| Mathematics | Playing with Constructions | module-6 (step_6) | ORIGINAL_DIAGRAM | Playing with Constructions — Part 6 |
| Mathematics | Playing with Constructions | module-7 (step_7) | ORIGINAL_DIAGRAM | Playing with Constructions — Part 7 |
| Mathematics | Playing with Constructions | module-8 (step_8) | ORIGINAL_DIAGRAM | Playing with Constructions — Part 8 |
| Mathematics | Prime Time | module-3 (step_3) | ORIGINAL_DIAGRAM | Prime Time — Part 3 |
| Mathematics | Prime Time | module-6 (step_6) | ORIGINAL_DIAGRAM | Prime Time — Part 6 |
| Mathematics | Prime Time | module-7 (step_7) | ORIGINAL_DIAGRAM | Prime Time — Part 7 |
| Mathematics | Symmetry | module-2 (step_2) | ORIGINAL_DIAGRAM | Symmetry — Part 2 |
| Mathematics | Symmetry | module-4 (step_4) | ORIGINAL_DIAGRAM | Symmetry — Part 4 |
| Mathematics | Symmetry | module-5 (step_5) | ORIGINAL_DIAGRAM | Symmetry — Part 5 |
| Mathematics | Symmetry | module-6 (step_6) | ORIGINAL_DIAGRAM | Symmetry — Part 6 |
| Mathematics | Symmetry | module-7 (step_7) | ORIGINAL_DIAGRAM | Symmetry — Part 7 |
| Mathematics | Symmetry | module-8 (step_8) | ORIGINAL_DIAGRAM | Symmetry — Part 8 |
| Mathematics | The Other Side of Zero | module-5 (step_5) | HUMAN_REVIEW | The Other Side of Zero — Part 5 |
| Mathematics | The Other Side of Zero | module-7 (step_7) | HUMAN_REVIEW | The Other Side of Zero — Part 7 |
| Mathematics | The Other Side of Zero | module-8 (step_8) | ORIGINAL_DIAGRAM | The Other Side of Zero — Part 8 |
| Science | A Journey through States of Water | module-7 (step_7) | ORIGINAL_DIAGRAM | A Journey through States of Water — Part 7 |
| Science | A Journey through States of Water | module-8 (step_8) | ORIGINAL_DIAGRAM | A Journey through States of Water — Part 8 |
| Science | Beyond Earth | module-1 (step_1) | WEB_PHOTO_OR_ORIGINAL | Beyond Earth — Part 1 |
| Science | Beyond Earth | module-5 (step_5) | WEB_PHOTO_OR_ORIGINAL | Beyond Earth — Part 5 |
| Science | Beyond Earth | module-7 (step_7) | WEB_PHOTO_OR_ORIGINAL | Beyond Earth — Part 7 |
| Science | Beyond Earth | module-8 (step_8) | WEB_PHOTO_OR_ORIGINAL | Beyond Earth — Part 8 |
| Science | Diversity in the Living World | module-1 (step_1) | WEB_PHOTO_OR_ORIGINAL | Diversity in the Living World — Part 1 |
| Science | Diversity in the Living World | module-2 (step_2) | WEB_PHOTO_OR_ORIGINAL | Diversity in the Living World — Part 2 |
| Science | Diversity in the Living World | module-3 (step_3) | WEB_PHOTO_OR_ORIGINAL | Diversity in the Living World — Part 3 |
| Science | Diversity in the Living World | module-5 (step_5) | WEB_PHOTO_OR_ORIGINAL | Diversity in the Living World — Part 5 |
| Science | Diversity in the Living World | module-6 (step_6) | WEB_PHOTO_OR_ORIGINAL | Diversity in the Living World — Part 6 |
| Science | Diversity in the Living World | module-7 (step_7) | WEB_PHOTO_OR_ORIGINAL | Diversity in the Living World — Part 7 |
| Science | Diversity in the Living World | module-8 (step_8) | WEB_PHOTO_OR_ORIGINAL | Diversity in the Living World — Part 8 |
| Science | Exploring Magnets | module-1 (step_1) | ORIGINAL_DIAGRAM | Exploring Magnets — Part 1 |
| Science | Exploring Magnets | module-6 (step_6) | ORIGINAL_DIAGRAM | Exploring Magnets — Part 6 |
| Science | Exploring Magnets | module-7 (step_7) | ORIGINAL_DIAGRAM | Exploring Magnets — Part 7 |
| Science | Living Creatures: Exploring their Characteristics | module-1 (step_1) | ORIGINAL_DIAGRAM | Living Creatures: Exploring their Characteristics — Part 1 |
| Science | Living Creatures: Exploring their Characteristics | module-3 (step_3) | WEB_PHOTO_OR_ORIGINAL | Living Creatures: Exploring their Characteristics — Part 3 |
| Science | Living Creatures: Exploring their Characteristics | module-6 (step_6) | WEB_PHOTO_OR_ORIGINAL | Living Creatures: Exploring their Characteristics — Part 6 |
| Science | Living Creatures: Exploring their Characteristics | module-7 (step_7) | WEB_PHOTO_OR_ORIGINAL | Living Creatures: Exploring their Characteristics — Part 7 |
| Science | Living Creatures: Exploring their Characteristics | module-8 (step_8) | WEB_PHOTO_OR_ORIGINAL | Living Creatures: Exploring their Characteristics — Part 8 |
| Science | Materials Around Us | module-1 (step_1) | WEB_PHOTO_OR_ORIGINAL | Materials Around Us — Part 1 |
| Science | Materials Around Us | module-2 (step_2) | WEB_PHOTO_OR_ORIGINAL | Materials Around Us — Part 2 |
| Science | Materials Around Us | module-3 (step_3) | WEB_PHOTO_OR_ORIGINAL | Materials Around Us — Part 3 |
| Science | Materials Around Us | module-5 (step_5) | WEB_PHOTO_OR_ORIGINAL | Materials Around Us — Part 5 |
| Science | Materials Around Us | module-6 (step_6) | WEB_PHOTO_OR_ORIGINAL | Materials Around Us — Part 6 |
| Science | Materials Around Us | module-7 (step_7) | WEB_PHOTO_OR_ORIGINAL | Materials Around Us — Part 7 |
| Science | Measurement of Length and Motion | module-1 (step_1) | ORIGINAL_DIAGRAM | Measurement of Length and Motion — Part 1 |
| Science | Measurement of Length and Motion | module-2 (step_2) | ORIGINAL_DIAGRAM | Measurement of Length and Motion — Part 2 |
| Science | Measurement of Length and Motion | module-4 (step_4) | ORIGINAL_DIAGRAM | Measurement of Length and Motion — Part 4 |
| Science | Measurement of Length and Motion | module-5 (step_5) | ORIGINAL_DIAGRAM | Measurement of Length and Motion — Part 5 |
| Science | Measurement of Length and Motion | module-6 (step_6) | ORIGINAL_DIAGRAM | Measurement of Length and Motion — Part 6 |
| Science | Measurement of Length and Motion | module-7 (step_7) | ORIGINAL_DIAGRAM | Measurement of Length and Motion — Part 7 |
| Science | Measurement of Length and Motion | module-8 (step_8) | ORIGINAL_DIAGRAM | Measurement of Length and Motion — Part 8 |
| Science | Methods of Separation in Everyday Life | module-5 (step_5) | ORIGINAL_DIAGRAM | Methods of Separation in Everyday Life — Part 5 |
| Science | Methods of Separation in Everyday Life | module-7 (step_7) | ORIGINAL_DIAGRAM | Methods of Separation in Everyday Life — Part 7 |
| Science | Methods of Separation in Everyday Life | module-8 (step_8) | ORIGINAL_DIAGRAM | Methods of Separation in Everyday Life — Part 8 |
| Science | Mindful Eating: A Path to a Healthy Body | module-1 (step_1) | WEB_PHOTO_OR_ORIGINAL | Mindful Eating: A Path to a Healthy Body — Part 1 |
| Science | Mindful Eating: A Path to a Healthy Body | module-2 (step_2) | WEB_PHOTO_OR_ORIGINAL | Mindful Eating: A Path to a Healthy Body — Part 2 |
| Science | Mindful Eating: A Path to a Healthy Body | module-3 (step_3) | WEB_PHOTO_OR_ORIGINAL | Mindful Eating: A Path to a Healthy Body — Part 3 |
| Science | Mindful Eating: A Path to a Healthy Body | module-5 (step_5) | WEB_PHOTO_OR_ORIGINAL | Mindful Eating: A Path to a Healthy Body — Part 5 |
| Science | Mindful Eating: A Path to a Healthy Body | module-6 (step_6) | WEB_PHOTO_OR_ORIGINAL | Mindful Eating: A Path to a Healthy Body — Part 6 |
| Science | Mindful Eating: A Path to a Healthy Body | module-7 (step_7) | WEB_PHOTO_OR_ORIGINAL | Mindful Eating: A Path to a Healthy Body — Part 7 |
| Science | Mindful Eating: A Path to a Healthy Body | module-8 (step_8) | WEB_PHOTO_OR_ORIGINAL | Mindful Eating: A Path to a Healthy Body — Part 8 |
| Science | Nature's Treasures | module-7 (step_7) | WEB_PHOTO_OR_ORIGINAL | Nature's Treasures — Part 7 |
| Science | The Wonderful World of Science | module-1 (step_1) | ORIGINAL_DIAGRAM | The Wonderful World of Science — Part 1 |
| Science | The Wonderful World of Science | module-2 (step_2) | ORIGINAL_DIAGRAM | The Wonderful World of Science — Part 2 |
| Science | The Wonderful World of Science | module-3 (step_3) | ORIGINAL_DIAGRAM | The Wonderful World of Science — Part 3 |
| Science | The Wonderful World of Science | module-5 (step_5) | ORIGINAL_DIAGRAM | The Wonderful World of Science — Part 5 |
| Science | The Wonderful World of Science | module-6 (step_6) | ORIGINAL_DIAGRAM | The Wonderful World of Science — Part 6 |
| Science | The Wonderful World of Science | module-7 (step_7) | ORIGINAL_DIAGRAM | The Wonderful World of Science — Part 7 |

## Source candidates verified on original Wikimedia Commons file pages

1. **Water cycle flowchart** — Entropyrider, CC0 1.0, 1154×600 PNG. Potential reference only for a module that actually teaches the complete water cycle. It is not automatically a fit for a module specifically about condensation or cooling by evaporation. https://commons.wikimedia.org/wiki/File:Water_cycle_flowchart.png
2. **Iodine food tests** — RailwayEnthusiast2025, public-domain dedication, 1321×743 JPEG. Strong topical match for Mindful Eating module 5's food-component test activity; still needs visual inspection and module-specific caption check. https://commons.wikimedia.org/wiki/File:Iodine_food_tests.jpg
3. **Feeling magnetic attraction** — Pieter Kuiper, public domain, 2575×2022 JPEG. Potentially relevant to Exploring Magnets, but only if the module caption teaches attraction/repulsion; not a general-purpose magnet illustration. https://commons.wikimedia.org/wiki/File:Feeling_magnetic_attraction.jpg
4. **Water Cycle Diagram** — Ehud Tal, CC BY-SA 4.0, 1920×1200 JPEG. Potential alternative for a whole-cycle lesson; share-alike obligations must be preserved. https://commons.wikimedia.org/wiki/File:Diagram_of_the_Water_Cycle.jpg

Wikimedia policy requires evidence for the licence, source and creator on each file page; the Commons reuse guidance also says to verify each file's conditions and attribution rather than assuming all Commons content has identical terms.

## Immediate review decisions

- Do not ingest the water-cycle candidate into a water module until its caption confirms a full-cycle learning objective; otherwise create a simpler original evaporation/condensation illustration.
- Mindful Eating module 5 is a high-confidence candidate for the iodine food-test photo, subject to inspection and exact lesson-step mapping.
- The magnet photo is a conditional candidate only; prefer an original labelled pole-interaction diagram if the module explains like/unlike poles.
- Beyond Earth modules 1, 5, 7 and 8 should not receive generic astronomy stock images. Module 1 can use a real dark-sky/Nubra scene; module 5 needs a planet-vs-star comparison; module 7 needs an Orion/Sirius/planet identification activity; module 8 is reflective/inquiry text and may need no image.
- Number Play modules 1 and 4, and The Other Side of Zero modules 5 and 7, remain no-image-or-human-review candidates until their full activity context is checked.
- Existing Beyond Earth production JPEGs are unverified provenance; do not duplicate them or describe them as licensed until source evidence is recovered.

## Licence and ingestion guardrails

- Preserve the original file page URL, direct source URL, exact licence name and URL, creator, attribution, and a cryptographic hash for each downloaded web image.
- Convert SVG/PDF sources to PNG only after checking the source licence and rendering output; do not commit SVG to the app's image pipeline.
- Original diagrams must be created as phone-readable PNGs, tied to exact approved lesson IDs and real step IDs.
- Upload only through the protected original-image ingestion route when its deployed availability is confirmed. Successful ingestion means pending review, not learner visibility.
- No production database writes, approval, merge, or deployment were performed by this review.


## Follow-on authoring pass — 2026-11-09

Added four exact lesson/step mappings to `assets/lesson-images/authoring-manifest.json` (manifest now has 86 unique mappings; zero duplicate mappings):
- Mathematics / Fractions / module-4 / step_4 — equivalent fractions and simplest form.
- Mathematics / The Other Side of Zero / module-8 / step_8 — movement left on the number line.
- Science / A Journey through States of Water / module-8 / step_8 — condensation and droplet formation.
- Science / Exploring Magnets / module-6 / step_6 — two phone-width panels: pole attraction/repulsion and compass direction.

The selected diagram types (`equivalent_fractions`, `integer_movement`, `condensation`, `magnet_poles`, `compass`) are all implemented in the existing Pillow renderer. This is a static source-level compatibility check, not a completed render/test run.

Updated coverage against the 88-item missing queue:
- 4 now mapped in the authoring manifest.
- 84 remain unmapped: 51 original-diagram proposals, 29 web-photo/original candidates, 4 human-review items.
- The 86 manifest mappings remain branch-only; no images were rendered or ingested by this commit.
- Renderer workflow checks did not trigger for this commit; zero check-runs were returned.
- Direct-original ingestion endpoint PR #276 remains open and unmerged; no production pending uploads were attempted.
