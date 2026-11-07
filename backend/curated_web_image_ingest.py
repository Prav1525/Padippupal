"""Curated web-image ingestion for approved PadippuPal lessons.

Accepts a ZIP of reviewed image files plus provenance/licence metadata. Assets
are stored as pending and cannot be served to learners until an admin approves.
"""
from __future__ import annotations

import hashlib
import json
import re
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from lesson_image_ingest import (
    MAX_IMAGE_BYTES,
    MAX_ARCHIVE_BYTES,
    connect,
    ensure_blob_table,
    require_image_admin,
)

router = APIRouter(tags=["curated-web-images"])
SAFE_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,240}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,120}$")
MIME_SIGNATURES = {
    "image/jpeg": lambda b: b.startswith(b"\\xff\\xd8\\xff"),
    "image/png": lambda b: b.startswith(b"\\x89PNG\\r\\n\\x1a\\n"),
    "image/webp": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP",
}
ALLOWED_LICENSES = {"Public Domain", "CC0-1.0", "CC-BY-4.0", "CC-BY-3.0"}


@router.post("/admin/lesson-images/ingest-curated", dependencies=[Depends(require_image_admin)])
async def ingest_curated_web_images(
    manifest_json: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    """Store vetted web images with provenance. Never publishes them automatically."""
    raw = await file.read()
    if not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise HTTPException(status_code=413, detail="Image archive must be between 1 byte and 80 MB.")
    try:
        manifest = json.loads(manifest_json)
        archive = ZipFile(BytesIO(raw))
    except (ValueError, BadZipFile) as exc:
        raise HTTPException(status_code=422, detail="Invalid manifest JSON or ZIP archive.") from exc
    if not isinstance(manifest, dict):
        raise HTTPException(status_code=422, detail="Manifest must be a JSON object.")
    lesson_id = str(manifest.get("lesson_id", "")).strip()
    records = manifest.get("images")
    if not lesson_id or len(lesson_id) > 160 or not isinstance(records, list) or not records or len(records) > 100:
        raise HTTPException(status_code=422, detail="Manifest needs lesson_id and 1–100 image records.")
    archive_names = {i.filename for i in archive.infolist() if not i.is_dir()}
    prepared, seen = [], set()
    for item in records:
        if not isinstance(item, dict):
            raise HTTPException(status_code=422, detail="Each image entry must be an object.")
        asset_id = str(item.get("id", "")).strip()
        module_key = str(item.get("module_key", "")).strip()
        step_ids = item.get("step_ids")
        path = str(item.get("archive_path", "")).strip()
        mime = str(item.get("content_type", "")).strip().lower()
        title = str(item.get("title", "")).strip()
        alt = str(item.get("alt_text", "")).strip()
        source_url = str(item.get("source_url", "")).strip()
        creator = str(item.get("creator", "")).strip()
        license_name = str(item.get("license", "")).strip()
        attribution = str(item.get("attribution", "")).strip()
        if not SAFE_ID.fullmatch(asset_id) or asset_id in seen:
            raise HTTPException(status_code=422, detail="Invalid or duplicate asset ID.")
        seen.add(asset_id)
        if not SAFE_ID.fullmatch(module_key) or not isinstance(step_ids, list) or not step_ids:
            raise HTTPException(status_code=422, detail="A valid module_key and step_ids are required.")
        if any(not isinstance(s, str) or not SAFE_ID.fullmatch(s) for s in step_ids):
            raise HTTPException(status_code=422, detail="Invalid teaching step ID.")
        if path not in archive_names or not SAFE_PATH.fullmatch(path) or ".." in path.split("/"):
            raise HTTPException(status_code=422, detail="Image archive path is invalid or missing.")
        if mime not in MIME_SIGNATURES or not title or not alt:
            raise HTTPException(status_code=422, detail="Only JPEG, PNG and WebP with title and alt_text are accepted.")
        if not source_url.startswith("https://") or len(source_url) > 2000:
            raise HTTPException(status_code=422, detail="A valid HTTPS source_url is required.")
        if not creator or license_name not in ALLOWED_LICENSES or not attribution:
            raise HTTPException(status_code=422, detail="Creator, supported reuse licence and attribution are required.")
        payload = archive.read(path)
        if not payload or len(payload) > MAX_IMAGE_BYTES or not MIME_SIGNATURES[mime](payload):
            raise HTTPException(status_code=415, detail="Image bytes are invalid, unsupported or exceed 8 MB.")
        prepared.append({
            "id": asset_id, "module_key": module_key, "step_ids": list(dict.fromkeys(step_ids)),
            "title": title, "alt_text": alt, "content_type": mime, "payload": payload,
            "sha256": hashlib.sha256(payload).hexdigest(), "source_url": source_url,
            "creator": creator, "license": license_name, "attribution": attribution,
        })

    conn = connect()
    try:
        lesson = conn.execute(
            "SELECT id, chapter, status, lesson_json FROM chapter_lessons WHERE id=%s",
            (lesson_id,),
        ).fetchone()
        if not lesson or lesson["status"] != "approved":
            raise HTTPException(status_code=404, detail="Approved lesson not found.")
        if str(lesson["chapter"]).strip().casefold() != "beyond earth":
            raise HTTPException(status_code=422, detail="This curated batch is currently restricted to Beyond Earth.")
        lesson_json = json.loads(lesson["lesson_json"] or "{}")
        known_steps = {str(s.get("id")) for s in lesson_json.get("teaching_sequence", []) if isinstance(s, dict)}
        for item in prepared:
            if not set(item["step_ids"]).issubset(known_steps):
                raise HTTPException(status_code=422, detail="An image references a step outside this approved lesson.")
        ensure_blob_table(conn)
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_url TEXT")
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_creator TEXT")
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_license TEXT")
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_attribution TEXT")
        stored = []
        for item in prepared:
            object_key = f"curated-web/{lesson_id}/{item['id']}"
            conn.execute(
                """INSERT INTO lesson_image_assets
                   (id,lesson_id,module_key,title,step_ids_json,bucket_name,object_key,
                    content_type,alt_text,status,content_fingerprint,source_url,source_creator,
                    source_license,source_attribution,created_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,'postgres-inline-images',%s,%s,%s,'pending',%s,%s,%s,%s,%s,NOW(),NOW())
                   ON CONFLICT (id) DO UPDATE SET
                    lesson_id=EXCLUDED.lesson_id,module_key=EXCLUDED.module_key,title=EXCLUDED.title,
                    step_ids_json=EXCLUDED.step_ids_json,object_key=EXCLUDED.object_key,
                    content_type=EXCLUDED.content_type,alt_text=EXCLUDED.alt_text,status='pending',
                    content_fingerprint=EXCLUDED.content_fingerprint,source_url=EXCLUDED.source_url,
                    source_creator=EXCLUDED.source_creator,source_license=EXCLUDED.source_license,
                    source_attribution=EXCLUDED.source_attribution,updated_at=NOW()""",
                (item["id"], lesson_id, item["module_key"], item["title"],
                 json.dumps(item["step_ids"]), object_key, item["content_type"], item["alt_text"],
                 item["sha256"], item["source_url"], item["creator"], item["license"], item["attribution"]),
            )
            conn.execute(
                """INSERT INTO lesson_image_asset_blobs(asset_id,image_bytes,sha256,byte_length)
                   VALUES (%s,%s,%s,%s)
                   ON CONFLICT(asset_id) DO UPDATE SET image_bytes=EXCLUDED.image_bytes,
                    sha256=EXCLUDED.sha256,byte_length=EXCLUDED.byte_length,created_at=NOW()""",
                (item["id"], item["payload"], item["sha256"], len(item["payload"])),
            )
            stored.append({"asset_id": item["id"], "module_key": item["module_key"],
                           "step_ids": item["step_ids"], "status": "pending",
                           "byte_length": len(item["payload"]), "sha256": item["sha256"]})
        conn.commit()
        return {"status": "stored_pending_review", "image_count": len(stored),
                "lesson_id": lesson_id, "images": stored,
                "storage": "PostgreSQL BYTEA; provenance and licence metadata retained"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Curated image ingestion failed ({type(exc).__name__}).") from exc
    finally:
        conn.close()
