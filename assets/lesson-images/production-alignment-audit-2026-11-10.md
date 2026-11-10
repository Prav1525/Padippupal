# Production lesson image alignment audit — 2026-11-10

## Scope and integrity
- Read-only inspection of every `ready` production lesson-image blob.
- 172 PNGs across 170 lesson/module pairs and 22 lessons.
- All 172 blobs have a valid PNG signature, unique SHA-256 hashes, and actual PNG dimensions of 1080×720 (3:2).
- Two module mappings intentionally contain two images each.
- The Android issue is separate: the production emulator screenshot showed paired image views constrained to 986×445 and 986×523 rather than the source 3:2 ratio. PR #305 makes the live tutor teaching column scrollable and adds an emulator assertion.

## Source-PNG alignment defects found
These defects are inside the PNG content itself; changing Compose image sizing cannot repair them.

| Lesson / module | Asset title | Observed issue |
|---|---|---|
| `105a95da` / `module-8` | Same Area, Different Perimeters | The `42 ft × 25 ft` measurement label collides with the rectangle edge. |
| `10d13a36` / `module-5` | Earth and Moon in Orbit | The explanatory subtitle overlaps the lower edge of the title band. |
| `4eebec1b` / `module-1` | Plants and Their Features | Flower petals overlap the title band. |
| `5176cc88` / `module-4` | Filtering Tea with a Cloth | The `FILTERED TEA` caption is too close to / clipped by the bottom frame. |
| `5311db95` / `module-7` | Place Value and Large Numbers | The `Above ground: positive` and `Below ground: negative` labels extend past the right edge. |
| `a52d8c99` / `module-1` | Plants and Their Features | Flower petals overlap the title band. |
| `a5eda399` / `module-6` | Cooling Water in an Earthen Pot | The bottom caption touches the frame and is partially clipped. |
| `a5eda399` / `module-8` | Condensation Forms Tiny Water Droplets | The `TINY DROPLETS` label extends past the right edge. |
| `b26a6b0c` / `module-2` | Floors Above and Below Ground | The positive / negative explanation labels extend past the right edge. |
| `eae02149` / `module-1` | Line of Symmetry | Fold-line label and line intrude into the title band. |
| `eae02149` / `module-2` | Paper Folding and Reflection Symmetry | Fold-line label and line intrude into the title band. |
| `eae02149` / `module-3` | Reflection Symmetry | Fold-line label and line intrude into the title band. |

## Separate content-mapping observations
Repeated diagrams were visually present under multiple module keys in several lessons (for example, the food-group diagram, thermometer diagram, plant-parts diagram, number-line diagram, and rectangle construction diagram). These are **not counted as alignment defects** and are not changed by this PR. They need a separate module-relevance review against the lesson text before any asset replacement.

## Recommended correction standard
1. Reserve a clear title safe-area; no diagram shape or subtitle may overlap it.
2. Keep all text at least 48 px from the left/right edges and 36 px from the bottom edge.
3. Keep labels adjacent to, not on top of, measurement lines, shape borders, arrows, or other key marks.
4. Recheck at phone display width after downscaling; no label may be clipped or become unreadable.
5. Preserve the 1080×720 PNG canvas and the existing lesson/module/step mapping.
6. Replace only the explicitly audited asset IDs; do not modify synthesis lesson text.

## Change control
This report is read-only. It does not alter any production blob or lesson mapping. Replacing these source PNGs requires an approved asset replacement and ingestion step; no production database write is part of PR #305.
