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


## Beyond Earth development image upload

The Beyond Earth manifest defines three pinned image assets. Upload them only to
the development Neon branch/bucket; this helper refuses missing credentials and
does not change production. Place the validated PNGs at:

- `backend/assets/beyond-earth/solar-system-v1.png`
- `backend/assets/beyond-earth/day-and-night-v1.png`
- `backend/assets/beyond-earth/moon-phases-v1.png`

Install backend requirements, then export the development branch's
`DATABASE_URL` and Neon Object Storage S3 credentials
(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ENDPOINT_URL_S3`,
and optionally `AWS_REGION`, default `ap-southeast-1`). Run a dry run first:

```bash
python backend/scripts/upload_beyond_earth_assets.py
```

Then explicitly upload and verify:

```bash
python backend/scripts/upload_beyond_earth_assets.py --apply
```

The script is pinned to the three approved object keys and the development
lesson UUID. It verifies each stored object's byte count and SHA-256 metadata
before changing the matching `lesson_image_assets` row from `pending` to
`uploaded`. It does not mark assets `ready`, publish a release, or deploy the
Android app. If an object already exists with different bytes, the script
stops; use `--overwrite` only after reviewing the replacement.

## Free-tier lesson visual generation (development only)

The admin-only `POST /admin/visuals/generate/{asset_id}` endpoint generates one of the three allow-listed CBSE Class 6 Beyond Earth visuals with Cloudflare Workers AI `@cf/black-forest-labs/flux-1-schnell`, converts the result to PNG, writes it directly to Neon Object Storage, verifies the stored SHA-256 and byte length, and only then updates the matching `lesson_image_assets` row to `uploaded`.

This endpoint is intentionally disabled unless `PADIPPUPAL_VISUALS_ENV=development`. It also refuses database URLs containing `prod` or `production`. It is not a student-facing endpoint and does not generate on lesson reads.

Configure these variables only on a development deployment:
- `PADIPPUPAL_ADMIN_TOKEN` — strong server-side admin secret.
- `PADIPPUPAL_VISUALS_ENV=development` — explicit development-only guard.
- `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` — Workers AI inference access.
- `DATABASE_URL` — development Neon branch only.
- `AWS_ENDPOINT_URL_S3`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_REGION=ap-southeast-1` — development Neon Object Storage access.

Call one asset at a time with the `x-admin-token` header:
```http
POST /admin/visuals/generate/beyond-earth-solar-system-v1
x-admin-token: <admin-secret>
```
The other approved IDs are `beyond-earth-day-night-v1` and `beyond-earth-moon-phases-v1`.

Workers AI has a published 10,000-Neuron daily free allocation on Workers Free. Calls beyond the free allocation fail on the Free plan; this integration has no paid fallback. Monitor usage in Cloudflare. Free quota is shared with other Workers AI tasks in the account, and the daily allowance can change under Cloudflare's terms. The endpoint does not automatically retry provider failures or generate more than the requested single image.

The endpoint is code-only until deployed with development credentials and tested against the development Neon branch. It does not set assets to `ready`, deploy the Android app, or write production storage/database.

