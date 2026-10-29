# Grade 6 Science Chapter 1 — Visual candidates

Source record: `28077c43-b7fe-4a40-85c8-663b8ac326a2` — NCERT Curiosity Class 6 Science, `fecu101.pdf`, Reprint 2026–27.

The seven SVG files are original draft drawings mapped to the seven approved synthesis records and their cited source-chunk IDs. Filenames use source page numbers, so `part-4.svg` maps to synthesis **Part 3** (textbook page 4), and similarly for later files. See `manifest.json` for the authoritative mapping.

## Draft set

| Synthesis topic | Source page | Drawing intent | Review state |
|---|---:|---|---|
| Part 1 | 1 | Curiosity: notice and ask why | Needs review: malformed OCR sentence |
| Part 2 | 2–3 | Science as a growing jigsaw | Needs review: running-header fragment |
| Part 3 | 4–5 | Named everyday objects prompt a materials question | Draft candidate |
| Part 4 | 5–6 | Pen problem → possible guess → test | Needs review: OCR word splits |
| Part 5 | 6–7 | Observe → ask → guess → test → analyse | Needs review: timestamp/header contamination |
| Part 6 | 7 | Apply questions and evidence to daily-life problems | Draft candidate |
| Part 7 | 8 | Continue exploring and asking questions | Draft candidate |

## Run the database-connected generator

The pipeline reads only approved synthesis rows for the selected source, resolves `citation_refs_json` to the `chunks` table, selects a topic-specific SVG scene, and emits a JSON manifest with source IDs, evidence flags, renderer version and content fingerprint. It never writes to the database.

Install the optional read-only DB dependency and set a read-only Neon connection string:

```bash
python -m pip install 'psycopg[binary]'
export DATABASE_URL='postgresql://...'
python tools/visual_engine/generate_science_chapter1.py --dry-run
python tools/visual_engine/generate_science_chapter1.py --out-dir build/visuals/science-chapter-1
```

## Safety

- These files are **candidate drawings, not published assets**.
- All JSON records set `active=false` and `database_written=false`.
- The script detects known OCR contamination and marks the corresponding output for review.
- Do not persist as active until the page and drawing are reviewed together, the synthesis text is corrected, and the Android inline tutor layout is verified.
- No synthesis/source rows or legacy visual records were changed by generating these candidates.
