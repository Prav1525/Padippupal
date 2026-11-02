"""Protected ingestion and delivery of original embedded textbook raster images."""
from __future__ import annotations

import hashlib
import json
import os
import re
from io import BytesIO
from zipfile import BadZipFile, ZipFile

import psycopg
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from psycopg.rows import dict_row

router = APIRouter(tags=["lesson-image-assets"])
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
ADMIN_TOKEN = os.getenv("PADIPPUPAL_ADMIN_TOKEN", "").strip()
MAX_ARCHIVE_BYTES = 80 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,240}$")


def require_image_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if not ADMIN_TOKEN or not x_admin_token or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Admin authentication required.")


def connect():
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Production database is not configured.")
    return psycopg.connect(DATABASE_URL, connect_timeout=10, row_factory=dict_row)


def ensure_blob_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lesson_image_asset_blobs (
            asset_id TEXT PRIMARY KEY,
            image_bytes BYTEA NOT NULL,
            sha256 TEXT NOT NULL,
            byte_length BIGINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


@router.post("/admin/lesson-images/ingest", dependencies=[Depends(require_image_admin)])
async def ingest_lesson_images(manifest_json: str, file: UploadFile = File(...)) -> dict:
    """Ingest a ZIP of original embedded images and a validated step-mapping manifest."""
    raw = await file.read()
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise HTTPException(status_code=413, detail="Image archive exceeds 80 MB.")
    try:
        manifest = json.loads(manifest_json)
        archive = ZipFile(BytesIO(raw))
    except (ValueError, BadZipFile) as exc:
        raise HTTPException(status_code=422, detail="Invalid manifest JSON or ZIP archive.") from exc
    source_hash = str(manifest.get("source_sha256", "")).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
        raise HTTPException(status_code=422, detail="Manifest must include the verified source PDF SHA-256.")
    records = manifest.get("images")
    if not isinstance(records, list) or not records or len(records) > 300:
        raise HTTPException(status_code=422, detail="Manifest must include 1–300 image records.")
    names = {item.filename for item in archive.infolist() if not item.is_dir()}
    seen_keys = set()
    prepared = []
    for item in records:
        if not isinstance(item, dict):
            raise HTTPException(status_code=422, detail="Each image record must be an object.")
        asset_id = str(item.get("id", "")).strip()
        lesson_id = str(item.get("lesson_id", "")).strip()
        module_key = str(item.get("module_key", "")).strip()
        path = str(item.get("archive_path", "")).strip()
        content_type = str(item.get("content_type", "")).strip().lower()
        steps = item.get("step_ids")
        alt = str(item.get("alt_text", "")).strip()
        if not asset_id or len(asset_id) > 160 or not lesson_id or len(lesson_id) > 160:
            raise HTTPException(status_code=422, detail="Image and lesson IDs are required.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,120}", module_key):
            raise HTTPException(status_code=422, detail="Invalid module_key.")
        if path not in names or not SAFE_KEY.fullmatch(path) or ".." in path.split("/"):
            raise HTTPException(status_code=422, detail="Image archive path is invalid or missing.")
        if content_type not in ALLOWED_TYPES or not isinstance(steps, list) or not steps:
            raise HTTPException(status_code=422, detail="Supported image MIME type and step_ids are required.")
        if any(not isinstance(step, str) or not step.strip() or len(step) > 160 for step in steps):
            raise HTTPException(status_code=422, detail="Invalid teaching step ID.")
        if not alt:
            raise HTTPException(status_code=422, detail="alt_text is required.")
        key = (lesson_id, module_key)
        if key in seen_keys:
            raise HTTPException(status_code=422, detail="Only one image asset per lesson/module is supported by the current schema.")
        seen_keys.add(key)
        payload = archive.read(path)
        if not payload or len(payload) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Each image must be between 1 byte and 8 MB.")
        signature_ok = (
            (content_type == "image/jpeg" and payload.startswith(b"\xff\xd8\xff")) or
            (content_type == "image/png" and payload.startswith(b"\x89PNG\r\n\x1a\n")) or
            (content_type == "image/webp" and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP") or
            (content_type == "image/gif" and payload[:6] in (b"GIF87a", b"GIF89a"))
        )
        if not signature_ok:
            raise HTTPException(status_code=415, detail=f"Image bytes do not match {content_type}.")
        prepared.append({**item, "id": asset_id, "lesson_id": lesson_id, "module_key": module_key,
                         "content_type": content_type, "step_ids": list(dict.fromkeys(steps)),
                         "alt_text": alt, "payload": payload, "sha256": hashlib.sha256(payload).hexdigest()})
    conn = connect()
    try:
        ensure_blob_table(conn)
        for item in prepared:
            lesson = conn.execute(
                "SELECT id, medium, chapter, status FROM chapter_lessons WHERE id=%s",
                (item["lesson_id"],)
            ).fetchone()
            if not lesson or lesson["status"] != "approved" or lesson["chapter"].strip().casefold() != "beyond earth":
                raise HTTPException(status_code=422, detail="Images may only attach to an approved Beyond Earth lesson.")
            if item.get("medium") and str(item["medium"]).casefold() != str(lesson["medium"]).casefold():
                raise HTTPException(status_code=422, detail="Manifest medium does not match lesson medium.")
        for item in prepared:
            object_key = f"beyond-earth/{str(item.get('medium') or 'unknown').lower()}/{item['module_key']}/{item['id']}"
            conn.execute("""
                INSERT INTO lesson_image_assets
                  (id, lesson_id, module_key, title, step_ids_json, bucket_name, object_key,
                   content_type, alt_text, status, content_fingerprint, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'ready',%s,NOW(),NOW())
                ON CONFLICT (lesson_id, module_key) DO UPDATE SET
                  id=EXCLUDED.id, title=EXCLUDED.title, step_ids_json=EXCLUDED.step_ids_json,
                  bucket_name=EXCLUDED.bucket_name, object_key=EXCLUDED.object_key,
                  content_type=EXCLUDED.content_type, alt_text=EXCLUDED.alt_text,
                  status='ready', content_fingerprint=EXCLUDED.content_fingerprint, updated_at=NOW()
            """, (item["id"], item["lesson_id"], item["module_key"], item.get("title") or item["alt_text"],
                  json.dumps(item["step_ids"]), "postgres-inline-images", object_key, item["content_type"],
                  item["alt_text"], item["sha256"]))
            conn.execute("""
                INSERT INTO lesson_image_asset_blobs (asset_id,image_bytes,sha256,byte_length)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (asset_id) DO UPDATE SET image_bytes=EXCLUDED.image_bytes,
                  sha256=EXCLUDED.sha256, byte_length=EXCLUDED.byte_length, created_at=NOW()
            """, (item["id"], item["payload"], item["sha256"], len(item["payload"])))
        conn.commit()
        return {"status": "stored", "image_count": len(prepared),
                "lesson_ids": sorted({item["lesson_id"] for item in prepared}),
                "storage": "PostgreSQL bytea-backed image endpoint"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Image ingestion failed ({type(exc).__name__}).") from exc
    finally:
        conn.close()


@router.get("/chapter-lessons/{lesson_id}/images")
def list_lesson_images(lesson_id: str) -> dict:
    conn = connect()
    try:
        rows = conn.execute("""
            SELECT a.id, a.lesson_id, a.module_key, a.title, a.step_ids_json,
                   a.content_type, a.alt_text, b.sha256, b.byte_length
            FROM lesson_image_assets a JOIN lesson_image_asset_blobs b ON b.asset_id=a.id
            JOIN chapter_lessons l ON l.id=a.lesson_id
            WHERE a.lesson_id=%s AND a.status='ready' AND l.status='approved'
            ORDER BY a.module_key
        """, (lesson_id,)).fetchall()
        return {"lesson_id": lesson_id, "images": [
            {"id": row["id"], "module_key": row["module_key"], "title": row["title"],
             "step_ids": json.loads(row["step_ids_json"]), "content_type": row["content_type"],
             "alt_text": row["alt_text"], "sha256": row["sha256"], "byte_length": row["byte_length"],
             "url": f"/chapter-lessons/{lesson_id}/images/{row['id']}"} for row in rows
        ]}
    finally:
        conn.close()


@router.get("/chapter-lessons/{lesson_id}/images/{asset_id}")
def get_lesson_image(lesson_id: str, asset_id: str) -> Response:
    conn = connect()
    try:
        row = conn.execute("""
            SELECT b.image_bytes, a.content_type, a.alt_text, b.sha256
            FROM lesson_image_assets a JOIN lesson_image_asset_blobs b ON b.asset_id=a.id
            JOIN chapter_lessons l ON l.id=a.lesson_id
            WHERE a.lesson_id=%s AND a.id=%s AND a.status='ready' AND l.status='approved'
        """, (lesson_id, asset_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Lesson image not found.")
        return Response(content=bytes(row["image_bytes"]), media_type=row["content_type"],
                        headers={"Cache-Control": "public, max-age=86400", "ETag": f'"{row["sha256"]}"',
                                 "X-Content-Type-Options": "nosniff"})
    finally:
        conn.close()
