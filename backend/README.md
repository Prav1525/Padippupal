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
