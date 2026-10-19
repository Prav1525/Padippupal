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

## API

- `GET /health` — service health.
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

- The worker runs in-process and its queue state is stored in SQLite, but uploaded text is temporarily staged in memory. A restart during processing can require re-submission. For production, replace this with a durable queue and durable source-file storage.
- PDF text extraction supports text-based PDFs. Scanned-PDF OCR, page-level chunk mapping, heading/chapter extraction, vector embeddings/semantic search, edition approval workflow and automated official-source synchronization are not implemented yet.
- Retrieval is a transparent keyword baseline, not an LLM answer generator. The Android app is not connected to this API yet.
- No official textbook files are bundled. Only ingest documents whose provenance and usage rights have been reviewed.
- Do not treat content as an official curriculum source just because it has been ingested; the source approval workflow is still an operational responsibility.

This is a working starter engine, not a production deployment. It does not train the model; it retrieves relevant approved passages for later use by the tutoring model.
