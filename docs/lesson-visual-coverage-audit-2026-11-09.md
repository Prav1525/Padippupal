# Class 6 lesson visual coverage audit — 2026-11-09

## Source of truth
Compared the approved Class 6 curriculum in the production Neon branch `br-jolly-haze-azhqgco9` with `assets/lesson-images/authoring-manifest.json`.

## Reconciliation
- Approved curriculum modules: 170
- Manifest module mappings: 170
- Missing module mappings: 0
- Duplicate mappings: 0
- Unknown lesson/module mappings: 0
- Unsupported renderer diagram types: 0

Subject totals:
- Mathematics: 78 modules; 78 mapped.
- Science: 92 modules; 92 mapped.

## Asset status
A manifest mapping is not proof that a PNG has been rendered, ingested, reviewed, or published. The renderer CI artifact available at the time of this audit was generated from an earlier 101-image manifest. The current 170-image manifest must pass a fresh renderer run and all image files must be decoded and checked before this batch is described as generated.

## Publication gates
- Do not write to the production database as part of this audit.
- Do not approve or publish pending assets.
- Verify image-to-lesson/step IDs, dimensions, image decoding, duplicate hashes, factual accuracy, child readability, and provenance.
- Keep the four human-review items explicitly pending reviewer approval.
- For web-sourced images, retain the original file page, creator, exact license, attribution, source URL, and SHA-256. Prefer CC0, public domain, and CC BY/CC BY-SA when compatible. Never infer a file's license from a search snippet.

## Important distinction
`MAPPED_IN_AUTHORING_MANIFEST_NOT_INGESTED` means only that a module has a proposed visual mapping. It does not mean that an image is in production or visible to learners.
