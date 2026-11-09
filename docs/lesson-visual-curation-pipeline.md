# Lesson visual curation pipeline

This is the operating procedure for selecting, creating, validating and ingesting
module-specific visuals. The audit tool is deliberately read-only: it never
downloads, generates, uploads, approves or publishes images.

## 1. Audit the whole curriculum before making images

Export the approved curriculum using the same source of truth as the tutor:
lesson ID, subject, chapter, ordered teaching-sequence step ID, title and caption.
The export must preserve module order because `module-N` is the current stable
manifest key. Run:

```bash
python tools/audit_lesson_visual_coverage.py \
  --curriculum approved-class6-curriculum.json \
  --manifest assets/lesson-images/authoring-manifest.json \
  --out visual-audit.json
```

Fix unknown lesson/module mappings, duplicate mappings and step-ID mismatches
before authoring. Review every item in `review_queue`; proposed routes are
triage hints, not automatic decisions. A module may correctly end with
`NO_VISUAL_NEEDED` after a human records the reason in the review ledger.

## 2. Choose the source route

### Use a web image only when a real photograph/reference adds learning value

Allowed source workflow:
- Search Wikimedia Commons or another reputable repository with an explicit
  reuse licence. Prefer CC0, public domain, or CC BY; CC BY-SA is acceptable
  only when downstream sharing obligations are recorded and compatible.
- Open the original file page, not just a search-result thumbnail.
- Verify the exact file URL, creator, licence name, licence URL, source page URL,
  attribution text and any share-alike requirements.
- Confirm the image depicts the intended object/process and is age-appropriate.
- Download only from the verified original file URL. Record a SHA-256 hash.
- Do not use Google Images thumbnails, Pinterest, textbook scans, random blogs,
  or assets with missing/unclear reuse rights. Do not remove watermarks.

A source record must include: `source_type=web`, `source_url`,
`source_page_url`, `license_name`, `license_url`, `creator`,
`attribution`, `sha256`, `lesson_id`, `module_key`, `step_ids`,
`alt_text`, and reviewer decision. If any licence/provenance field is absent,
reject the image rather than ingest it.

### Create an original diagram when the idea is abstract or explanatory

Use the Pillow renderer for geometry, number concepts, graphs, cycles,
comparisons, labelled processes and other controlled teaching diagrams.
Create a real image file, not SVG. Default canvas is 1080 × 720; use one
full-width panel, or two separate full-width panels for a genuine sequence or
comparison. Keep labels large, short, correct and inside safe margins. Do not
use decorative filler or add facts not present in the lesson.

Generated asset metadata must say `source_type=original`, name the renderer
and version, store the prompt/specification and record the SHA-256. Never
describe an original image as a web-sourced image.

### Human review / no image

If neither route clearly improves understanding, record `NO_VISUAL_NEEDED`
with a short reason. If the source or educational meaning is uncertain, leave
the item `NEEDS_HUMAN_REVIEW`; do not guess.

## 3. Validate every asset

Before ingestion:
- Exact approved lesson ID, module key and real step ID match.
- One asset teaches the mapped module, not a neighbouring module.
- No duplicate hash or duplicate lesson/module mapping unless an explicitly
  reviewed multi-panel set is intended.
- PNG/JPEG/WebP signature matches MIME; image decodes successfully.
- 1080 × 720 for original diagrams; labels are legible at phone width and not
  cropped. Web photographs may retain a different ratio when the tutor layout
  supports it.
- Check factual accuracy, spelling, contrast, age suitability and copyright.
- Store provenance and attribution with the image record.

The existing protected ingestion endpoints store assets as pending review.
A successful upload is not approval and must not make an asset learner-visible.

## 4. Ingestion and release gates

1. Produce a reviewed manifest and rendered/downloaded files.
2. Run renderer, provenance, mapping and ingestion-client tests.
3. Upload only to pending review storage after explicit operator approval.
4. Verify API response says pending and student_visible=false for every asset.
5. Review the actual Android tutor screen on API 35 for the mapped module.
6. A separate authorized approval action is required before learner visibility.
   Never merge, deploy, write production data or publish as a side effect of audit.

## 5. Coverage is a ledger, not a PNG count

Report per subject/chapter/module:
- visual decision: web / original / no visual needed / needs review
- source and licence or original specification
- mapping and validation state
- ingestion state and student visibility state

Do not report a module as complete merely because a file exists. It is complete
only after exact mapping, visual QA and the required review gates have passed.
