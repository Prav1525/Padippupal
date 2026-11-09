# Phone-first lesson visual authoring

## Screen-fit rules
- Canvas: 1080 × 720 px (3:2 landscape), designed to render edge-to-edge at the tutor content width.
- Never bake in a fake phone frame, large outer whitespace, or tiny diagram in the middle.
- Use `single` for one concept that reads cleanly as one wide teaching panel.
- Use `pair` when a concept benefits from a before/after, compare/contrast, or two-step explanation. A pair is two separate 1080 × 720 PNGs, each displayed at full content width in sequence—not two tiny side-by-side cards on a phone.
- Keep labels inside safe margins. Prefer short words, clear arrows, large shapes, and high contrast.
- Preserve the image aspect ratio; do not crop labels. Tutor UI should use width=match-parent and height=wrap-content / fit-center.
- If a concept needs more than two panels, split it across distinct relevant teaching steps or omit the visual rather than cram it.

## Curation rules
- Map each asset to the approved lesson ID and real teaching_sequence step ID.
- Read the step's explanation/caption and make the diagram teach that exact concept.
- Do not add decorative filler or force an image into every module.
- Do not alter synthesis lesson text or module structure.
- Prefer original Pillow-rendered diagrams for maths and abstract processes; use appropriately licensed external photos where a real-world photograph adds value.
- All assets enter review as pending and stay hidden from students until separately approved.

## Render
```bash
python -m pip install Pillow
python tools/render_lesson_visuals.py --manifest assets/lesson-images/authoring-manifest.json
```

The script emits individual PNGs and `rendered-manifest.json` with exact lesson/module/step mappings. It does not invent lesson content: each panel's labels and explanatory lines must be reviewed before rendering.

## Original diagram library
The current Class 6 authoring manifest selects a first reviewed set of 23 visuals across all 22 approved Mathematics and Science chapters. Supported original diagram families include fractions, angles, area/perimeter, symmetry, number lines, bar graphs, triangle patterns, prime-factor trees, rectangle properties, water states, constellations, the solar system, leaf venation, magnets, seedling growth, solubility, ruler measurement, decantation, balanced food groups, Sun-to-Earth energy, thermometers, and the scientific method.

The manifest is a curated starter set, not a rule that every chapter or every teaching module must have an image. A visual is retained only where it clarifies the exact mapped teaching step. The render test creates each PNG at exactly 1080 × 720 and archives the rendered set for visual review. Recheck label fit and concept accuracy whenever a panel is edited.

Curation note: the Prime Time factor tree is explicitly based on 72 = 2 × 2 × 2 × 3 × 3; the mindful-eating visual names food groups without prescribing serving ratios.

Food-group artwork uses simple hand-drawn fruit, vegetable, grain and egg icons; it does not suggest fixed serving proportions.

Graph bars are illustrative sample values, not presented as measured class survey results; the magnet graphic uses simple iron nail shapes as attracted objects.

The complete 72 factor tree is kept within the 1080 × 720 canvas with a clear gap below the heading band.

Backend ingestion tests cover actual binary signatures, authenticated upload, lesson-step validation and pending-only persistence; see the dedicated GitHub Actions check.

The optional production uploader is workflow-dispatch only, requires an explicit confirmation input and admin secret, verifies every response is pending and not student-visible, and is never run by the renderer CI.

The upload-client test suite also checks that a non-pending or student-visible API response aborts the batch.

The upload-client mocked-response test has a variadic request stub so it exercises the actual requests.post call signature.

Android tutor integration now requests mapped lesson images for every approved chapter, matches an exact step ID first, and falls back to the existing synthesized visual when no ready asset exists. PNGs are displayed at their intrinsic aspect ratio across the available content width.

Android CI now includes the stacked visual PR base branch so the inline tutor layout change receives an API 35 emulator acceptance run before merge.

The Android API 35 smoke fixture now serves a real 1080 × 720 PNG through the same lesson-image manifest and byte endpoint; the UI smoke asserts that its mapped alt/title is present on the tutor screen.

All `synthesis_static` lesson visuals now pass through the mapped-image loader; when no ready image is returned, the existing synthesized drawing remains the fallback.

The UI smoke helper XML fixtures now include the mapped image's accessible label so unit-level assertions remain aligned with the live tutor acceptance check.
