# Unified lesson visual coverage and curation

The curriculum export is the authoritative inventory. One module ledger reconciles
all visual-source and lifecycle records against that inventory; a PNG count or a
single manifest is never treated as coverage.

## Run the unified audit

```bash
python tools/audit_lesson_visual_coverage.py \
  --curriculum approved-class6-curriculum.json \
  --manifest assets/lesson-images/authoring-manifest.json \
  --web-manifest assets/lesson-images/web-source-manifest.json \
  --decision-ledger assets/lesson-images/coverage-decision-ledger.json \
  --ingestion-ledger production-image-record-export.json \
  --render-ledger tutor-render-verification.json \
  --out visual-coverage-ledger.json
```

Only the curriculum and authoring manifest are required. Optional exports join
web candidates, curator decisions, stored image records and tutor-screen checks.
The ingestion and render exports each use an `images` array containing exact
`lesson_id`, `module_key`, and `step_ids`. The decision ledger uses an `items`
array with exact module keys and curator decision fields. Missing optional
exports are reported as unknown/not yet evidenced, never inferred as complete.

## Canonical module states

- `NEEDS_WEB_SOURCE`: a real-world photo is useful, but no reviewed source is mapped.
- `NEEDS_ORIGINAL_PNG`: an original child-friendly diagram is needed.
- `NEEDS_REVIEW`: the teaching content/source choice is ambiguous, or a web candidate awaits review.
- `READY`: an authoring-manifest mapping exists; this is not an ingestion claim.
- `INGESTED`: a stored image record is confirmed; this is not a rendering claim.
- `RENDER_VERIFIED`: the exact module has been checked on the tutor screen.

The ledger includes every module, its subject/chapter, route, decision metadata,
counts from each evidence source, and a subject/status summary. Unknown IDs,
duplicate mappings/decisions and step-ID mismatches fail the audit.

## Source selection and child-safety requirements

Use an existing approved asset first. For real objects, search reputable
repositories (prefer CC0, public domain or CC BY), inspect the original file
page, and record source URL, creator, licence, licence URL, attribution,
SHA-256, exact module IDs and alt text. Reject unclear rights, watermarks,
textbook scans and thumbnail-only sources. For abstract ideas, sequences,
graphs and labelled explanations, create an original PNG with the Pillow
renderer (1080x720; one full-width panel or two separate full-width panels
when pedagogically justified). Keep labels simple, correct and legible on a
phone. Record renderer/version, visual specification and SHA-256.

Validate every asset against its exact module and step ID; check decoding,
dimensions, duplicates, spelling, factual accuracy, contrast, age suitability,
licence and attribution. A human may record `NO_VISUAL_NEEDED` with a reason;
do not leave a module silently omitted.

## Safety gates

The audit is read-only. It does not download, generate, upload, approve,
deploy or publish. Uploads go only to pending review after explicit approval.
A successful pending upload is not learner-visible approval. Production writes,
deployment, PR merge and public release remain separate explicit approval gates.
