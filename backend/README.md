# PadippuPal Curriculum Engine (prototype)

A small FastAPI service that keeps curriculum preparation out of the student experience. It supports an admin-only text/PDF ingestion endpoint, asynchronous chunk indexing, a source catalog, and profile-filtered retrieval.

## Run locally

Python 3.11+ recommended.

```bash
cd backend
python -m venv .venv
# activate the environment, then:
pip install -r requirements.txt
export PADIPPUPAL_ADMIN_TOKEN='replace-with-a-long-random-secret'
uvicorn app:app --host 127.0.0.1 --port 8000
```

Use HTTPS and a secret manager before any network deployment. Admin ingestion fails closed until `PADIPPUPAL_ADMIN_TOKEN` is configured. Do not put this token in the Android app.

## Official-source registry

- `GET /sources/registry` lists curated official source authorities, the evidence checked, and reuse/ingestion status.
- The initial registry records NCERT textbooks, CBSE's 2026-27 curriculum page, and Tamil Nadu Textbook and Educational Services Corporation.
- **No source is approved for automatic ingestion yet.** NCERT's own notice prohibits online-service hosting/republication without the required permission. CBSE reuse terms still need review. For Tamil Nadu, the publisher is verified but exact downloadable files and reuse permissions are not yet verified.
- The registry deliberately does not fetch URLs or crawl external websites. Official publisher identity and permission to reuse content are separate checks. Keep source links available while rights review is pending.

## API

- `GET /health` — service health.
- `GET /sources/registry` — public, read-only source provenance and approval status.
- `GET /catalog?board=CBSE&class_level=7&subject=Science&medium=English` — approved, indexed catalog entries.
- `POST /admin/ingest-text` — authenticated admin-only text ingestion; sends source metadata plus text.
- `POST /admin/ingest-pdf` — authenticated admin-only PDF ingestion; `metadata_json` is a JSON string form field and `file` is the PDF. Record provenance and permission in `license_note`.
- `GET /admin/jobs/{job_id}` — authenticated job status.
- `POST /retrieve` — retrieve relevant text filtered strictly by board, class, subject and medium, optionally academic year and edition. Responses include source metadata.

Example retrieval request:

```json
{
  "board": "CBSE",
  "class_level": 7,
  "subject": "Science",
  "medium": "English",
  "query": "Why is soil prepared before sowing?",
  "academic_year": "2026-27",
  "limit": 4
}
```

## Current limitations (must not be hidden)

- Source text and job state are now persisted in SQLite, so queued work can survive a process restart. The worker itself is in-process; for production deployments with multiple instances, use a dedicated durable queue and durable object storage for original PDFs.
- PDF text extraction supports text-based PDFs. Scanned-PDF OCR, page-level chunk mapping, heading/chapter extraction, vector embeddings/semantic search, edition approval workflow and automated official-source synchronization are not implemented yet. A curated official-source registry is now included, but all entries remain blocked from automated ingestion pending rights and exact-file verification.
- Retrieval is a transparent keyword baseline, not an LLM answer generator. The Android app includes a curriculum connection screen that can call `/health` and `/retrieve` when configured with a deployed HTTPS API base URL. The service is not deployed automatically by this repository.
- No official textbook files are bundled. Only ingest documents whose provenance and usage rights have been reviewed.
- Do not treat content as an official curriculum source just because it has been ingested; the source approval workflow is still an operational responsibility.

This is a working starter engine, not a production deployment. The Android app accepts an HTTPS endpoint in its curriculum screen or through the `PADIPPUPAL_API_BASE_URL` Gradle property. No live endpoint is supplied by default, and the service must be deployed and populated with approved documents before live retrieval can work. It does not train the model; it retrieves relevant approved passages for later use by the tutoring model.


## Gentle AI tutor

- POST /tutor/chat — child-friendly, class-aware teaching through Gemini (`GEMINI_API_KEY`); accepts board, class, subject, textbook medium, preferred explanation language (English, Tanglish, or Tamil), selected chapter/topic, current question and recent turns.
- The endpoint retrieves up to four keyword-matched passages for the exact board/class/subject/medium before generating an answer. If no passage matches, it can explain general concepts but must not claim the answer came from the official textbook.
- Configure `GEMINI_API_KEY` only in the Render service environment; never put it in Android, GitHub, or the APK. `PADIPPUPAL_GEMINI_CHAT_MODEL` overrides the default `gemini-2.5-flash` model.
- Natural speech provider order: configure SARVAM_API_KEY in the Render service environment for primary Sarvam TTS (`PADIPPUPAL_SARVAM_TTS_MODEL`, default `bulbul:v3`). If Sarvam is unavailable, the backend tries Gemini TTS when GEMINI_API_KEY is configured (`PADIPPUPAL_GEMINI_TTS_MODEL` overrides its model); if both cloud providers fail, the Android app uses the device's installed TTS engine. Keep all keys server-side. Provider quotas, model availability, and billing vary by account; do not assume unlimited free usage.
- Voice requests send the tutor reply text and selected explanation language to Google. Avoid including a child's identifying or sensitive information in prompts, and review Google's current data terms before production use.
- The tutor prompt constrains teaching to the selected chapter/topic and matching interactive lesson blueprint. If approved source passages are unavailable, the model must not claim textbook verification or invent official NCERT details.
- The Android tutor uses the phone's installed Android text-to-speech engine for spoken replies. English, Tanglish (Indian English voice) and Tamil voice availability/quality depends on installed voices. No cloud TTS credentials are bundled into the app.
- API calls are not stored as a student transcript by this endpoint. The last few turns are sent with each request to keep the conversation coherent.


## Release and source-trust gates

The lesson catalog is a teaching/visual blueprint, not an authoritative substitute for the current official textbook. `source_registry.json` currently marks all source entries as not approved for automatic ingestion. Before describing an answer as NCERT-grounded, verify the exact official syllabus/textbook edition, chapter and medium and ensure the required usage rights are in place. Gemini Live is intentionally not part of the current release; add it only after the request/response tutor, session restoration, visual lesson and speech paths pass phone testing.

## Multi-board syllabus synthesis engine (review-first release)

The `syllabus_synthesis.py` pipeline prepares source-grounded packages in this hierarchy:

`board / academic-year / medium / standard / subject / textbook-edition / source-id/`

Each package keeps the original PDF, page-level extracted text, embedded images (when PyMuPDF can extract them), a source manifest, and per-topic evidence packages. Each topic records candidate page matches, matched terms, evidence excerpts, a synthesis prompt contract, coverage status, and a review status. Topics with no matching evidence are explicitly marked `missing_source`.

### Admin API

`POST /admin/syllabus/ingest-pdf` accepts multipart fields:
- `file`: a PDF (maximum 25 MiB)
- `metadata_json`: JSON for board, academic_year, medium, standard, subject, textbook_title, edition, source_authority, source_url, rights_reviewed and rights_note
- `syllabus_json`: JSON array of topic objects (`id`, `title`, optional `chapter`, `keywords`, `syllabus_reference`)

The endpoint requires `x-admin-token` and the existing server-side `PADIPPUPAL_ADMIN_TOKEN`. Source ingestion fails closed unless `rights_reviewed=true` and a non-empty `rights_note` are supplied. This is an explicit operator attestation, not a legal determination; only process materials whose usage rights have actually been reviewed.

After ingestion, call `POST /admin/syllabus/sources/{source_id}/topics/{topic_id}/synthesize` with `x-admin-token` and optional JSON `{ "max_rounds": 3 }`. The endpoint uses the existing `GEMINI_API_KEY` and `PADIPPUPAL_GEMINI_CHAT_MODEL` settings, runs bounded draft/refine passes, checks required teaching sections, 2–3 understanding checks and citations against matched PDF pages, and stores each round in `topics/{topic-id}/synthesis.json`. Results can be `ready_for_review`, `needs_review`, or `blocked_missing_evidence`; **none is auto-approved**. A citation passing the page-membership check is a structural gate, not proof that the claim is factually supported by that page.

**Reuse books already in the DB:** call `POST /admin/syllabus/sources/from-curriculum-db/{existing_source_id}` with `x-admin-token` and optional multipart `syllabus_json`. This reads a source whose existing `sources.status` is `ready` from `sources` + `source_content` + `chunks`, builds page-level evidence from the stored `[Page N]` markers or chunk page ranges, and does not require uploading the same PDF again. If `syllabus_json` is `[]`, it can use the existing Class 6 CBSE Science/Mathematics topic scaffold. This scaffold is only topic routing metadata; the actual book evidence must come from the ready database source. Existing source license notes are preserved but are not silently upgraded to a rights approval.

**Database storage:** synthesis uses the same `DATABASE_URL` (Postgres/Neon) or `PADIPPUPAL_DB` SQLite database as the existing curriculum API. It stores source hierarchy in `syllabus_sources` (board/year/medium/standard/subject/book/edition/rights/provenance), extracted page text in `syllabus_source_pages`, figure metadata in `syllabus_source_images`, topic/chapter/evidence mappings in `syllabus_topics`, the current unapproved synthesis in `syllabus_topic_syntheses`, and each draft/refinement plus validation issues in `syllabus_synthesis_rounds`. The source PDF and image files remain in the existing review package directory; the DB contains metadata, evidence text and synthesis JSON so the records can be queried with the rest of the backend data. Existing Class 6 CBSE Science/Mathematics scaffold topic IDs can seed topic mapping when `syllabus_json` is an empty array; they are routing metadata, not textbook content or proof of official syllabus coverage.

Install `pymupdf` (included in backend requirements) to extract embedded figures. Text extraction uses the existing `pypdf` dependency. Scanned pages are flagged for OCR and are not silently treated as readable. PDF images retain source page numbers and checksums; topic links/captions remain pending review.

**Trust boundary:** this first release does not claim that lexical matching is complete syllabus coverage, does not auto-approve AI-generated synthesis, and does not fetch arbitrary publisher URLs. Every package remains `needs_review` until source pages, image links and topic coverage are checked. Multi-board/all-standard support is in the schema; actual curriculum coverage depends on supplying each board's official syllabus and textbook sources.
