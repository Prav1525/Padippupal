"""Curated web-image ingestion for approved PadippuPal lessons.

Accepts a ZIP of reviewed image files plus provenance/licence metadata. Assets
are stored as pending and cannot be served to learners until an admin approves.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import ipaddress
import json
import re
import socket
import threading
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile

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
    total_batch_bytes = 0
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
        supersedes_ids = item.get("supersedes_asset_ids", [])
        if not isinstance(supersedes_ids, list) or len(supersedes_ids) > 20:
            raise HTTPException(status_code=422, detail="supersedes_asset_ids must be a list of at most 20 asset IDs.")
        if any(not isinstance(old_id, str) or not SAFE_ID.fullmatch(old_id) or old_id == asset_id for old_id in supersedes_ids):
            raise HTTPException(status_code=422, detail="Invalid asset ID in supersedes_asset_ids.")
        if len(set(supersedes_ids)) != len(supersedes_ids):
            raise HTTPException(status_code=422, detail="Duplicate asset ID in supersedes_asset_ids.")
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
            "supersedes_asset_ids": supersedes_ids,
        })

    conn = connect()
    try:
        lesson = conn.execute(
            "SELECT id, board, class_level, subject, chapter, status, lesson_json FROM chapter_lessons WHERE id=%s",
            (lesson_id,),
        ).fetchone()
        if not lesson or lesson["status"] != "approved":
            raise HTTPException(status_code=404, detail="Approved lesson not found.")
        if (
            str(lesson["chapter"]).strip().casefold() != "beyond earth"
            or str(lesson["subject"]).strip().casefold() != "science"
            or int(lesson["class_level"]) != 6
            or str(lesson["board"]).strip().casefold() != "cbse"
        ):
            raise HTTPException(status_code=422, detail="This curated batch is restricted to the approved CBSE Class 6 Science Beyond Earth lesson.")
        lesson_json = json.loads(lesson["lesson_json"] or "{}")
        known_steps = {str(s.get("id")) for s in lesson_json.get("teaching_sequence", []) if isinstance(s, dict)}
        expected_modules = {f"step_{number}": f"module-{number}" for number in range(1, 9)}
        superseded_ids_seen = set()
        for item in prepared:
            if not set(item["step_ids"]).issubset(known_steps):
                raise HTTPException(status_code=422, detail="An image references a step outside this approved lesson.")
            if any(expected_modules.get(step) != item["module_key"] for step in item["step_ids"]):
                raise HTTPException(status_code=422, detail="Image module_key does not match its teaching step.")
            old_ids = item["supersedes_asset_ids"]
            if superseded_ids_seen.intersection(old_ids):
                raise HTTPException(status_code=422, detail="An existing image cannot be superseded by multiple replacements.")
            superseded_ids_seen.update(old_ids)
            if old_ids:
                old_rows = conn.execute(
                    "SELECT id, step_ids_json, status FROM lesson_image_assets WHERE lesson_id=%s AND id = ANY(%s)",
                    (lesson_id, old_ids),
                ).fetchall()
                if len(old_rows) != len(old_ids):
                    raise HTTPException(status_code=422, detail="A replacement target is not part of this lesson.")
                for old_row in old_rows:
                    old_steps = json.loads(old_row["step_ids_json"] or "[]")
                    if old_row["status"] != "ready" or old_steps != item["step_ids"]:
                        raise HTTPException(status_code=422, detail="Only ready images mapped to the same teaching step can be superseded.")
        ensure_blob_table(conn)
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_url TEXT")
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_creator TEXT")
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_license TEXT")
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS source_attribution TEXT")
        conn.execute("ALTER TABLE lesson_image_assets ADD COLUMN IF NOT EXISTS supersedes_asset_ids_json TEXT")
        ensure_superseded_status(conn)
        stored = []
        for item in prepared:
            object_key = f"curated-web/{lesson_id}/{item['id']}"
            conn.execute(
                """INSERT INTO lesson_image_assets
                   (id,lesson_id,module_key,title,step_ids_json,bucket_name,object_key,
                    content_type,alt_text,status,content_fingerprint,source_url,source_creator,
                    source_license,source_attribution,supersedes_asset_ids_json,created_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,'postgres-inline-images',%s,%s,%s,'pending',%s,%s,%s,%s,%s,%s,NOW(),NOW())
                   ON CONFLICT (id) DO UPDATE SET
                    lesson_id=EXCLUDED.lesson_id,module_key=EXCLUDED.module_key,title=EXCLUDED.title,
                    step_ids_json=EXCLUDED.step_ids_json,object_key=EXCLUDED.object_key,
                    content_type=EXCLUDED.content_type,alt_text=EXCLUDED.alt_text,
                    status=CASE WHEN lesson_image_assets.status='ready' AND lesson_image_assets.content_fingerprint=EXCLUDED.content_fingerprint THEN 'ready' ELSE 'pending' END,
                    content_fingerprint=EXCLUDED.content_fingerprint,source_url=EXCLUDED.source_url,
                    source_creator=EXCLUDED.source_creator,source_license=EXCLUDED.source_license,
                    source_attribution=EXCLUDED.source_attribution,
                    supersedes_asset_ids_json=EXCLUDED.supersedes_asset_ids_json,updated_at=NOW()""",
                (item["id"], lesson_id, item["module_key"], item["title"],
                 json.dumps(item["step_ids"]), object_key, item["content_type"], item["alt_text"],
                 item["sha256"], item["source_url"], item["creator"], item["license"], item["attribution"],
                 json.dumps(item["supersedes_asset_ids"])),
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


# Direct URL ingestion: the server fetches curated NASA image URLs, so an admin
# submits metadata only; no ZIP or local file upload is required.
ALLOWED_IMAGE_HOSTS = {
    "images-assets.nasa.gov",
    "images.nasa.gov",
    "spaceplace.nasa.gov",
    "svs.gsfc.nasa.gov",
    "photojournal.jpl.nasa.gov",
    "science.nasa.gov",
    "assets.science.nasa.gov",
    "nasa.gov",
    "www.nasa.gov",
    "jpl.nasa.gov",
}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAX_CURATED_BATCH_BYTES = MAX_ARCHIVE_BYTES


def validate_source_url(source_url: str) -> str:
    """Allow HTTPS image URLs on explicitly approved NASA hosts only."""
    if not isinstance(source_url, str) or len(source_url) > 2000:
        raise ValueError("source_url must be a URL no longer than 2000 characters.")
    parsed = urlsplit(source_url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or not host
        or host not in ALLOWED_IMAGE_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.fragment
    ):
        raise ValueError("Only HTTPS URLs on approved NASA image hosts are accepted.")
    # Check every resolved address before making a request. The allowlist and
    # TLS verification remain in force for the actual HTTP request as well.
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("The approved image host could not be resolved.") from exc
    if not addresses:
        raise ValueError("The approved image host has no public address.")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("The image host resolved to a non-public network address.")
    return source_url


def sniff_image_type(payload: bytes) -> str | None:
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        return "image/webp"
    return None


def ensure_superseded_status(conn) -> None:
    """Allow reviewed replacements to hide only the exact assets they replace."""
    row = conn.execute(
        """SELECT pg_get_constraintdef(oid) AS definition
           FROM pg_constraint
           WHERE conrelid='lesson_image_assets'::regclass
             AND conname='lesson_image_assets_status_check'"""
    ).fetchone()
    definition = str(row["definition"] or "") if row else ""
    if "superseded" in definition:
        return
    if row:
        conn.execute("ALTER TABLE lesson_image_assets DROP CONSTRAINT lesson_image_assets_status_check")
    conn.execute(
        """ALTER TABLE lesson_image_assets
           ADD CONSTRAINT lesson_image_assets_status_check
           CHECK (status IN ('pending','uploaded','ready','failed','superseded'))"""
    )


async def fetch_approved_image(source_url: str) -> tuple[bytes, str]:
    """Fetch a bounded image from an allowlisted host, validating every redirect."""
    current_url = validate_source_url(source_url)
    timeout = httpx.Timeout(15.0, connect=8.0)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
        verify=True,
        headers={"User-Agent": "PadippuPal-LessonImageIngest/1.0"},
    ) as client:
        for redirect_count in range(4):
            # Re-check DNS and policy for each hop; redirects never bypass the allowlist.
            current_url = validate_source_url(current_url)
            async with client.stream("GET", current_url) as response:
                if response.status_code in REDIRECT_STATUSES:
                    location = response.headers.get("location")
                    if not location or redirect_count == 3:
                        raise ValueError("Image source redirected too many times or omitted Location.")
                    current_url = urljoin(current_url, location)
                    continue
                if response.status_code != 200:
                    raise ValueError(f"Image source returned HTTP {response.status_code}.")
                declared_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if declared_type not in MIME_SIGNATURES:
                    raise ValueError("Image source did not return JPEG, PNG or WebP.")
                length = response.headers.get("content-length")
                if length:
                    try:
                        if int(length) > MAX_IMAGE_BYTES:
                            raise ValueError("Image exceeds the 8 MB limit.")
                    except ValueError as exc:
                        if "8 MB" in str(exc):
                            raise
                        raise ValueError("Image source returned an invalid Content-Length.") from exc
                chunks, total = [], 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > MAX_IMAGE_BYTES:
                        raise ValueError("Image exceeds the 8 MB limit.")
                    chunks.append(chunk)
                payload = b"".join(chunks)
                actual_type = sniff_image_type(payload)
                if not payload or actual_type != declared_type:
                    raise ValueError("Downloaded image bytes do not match the declared image type.")
                return payload, actual_type
    raise ValueError("Image source redirect handling failed.")


@router.post("/admin/lesson-images/ingest-curated-urls", dependencies=[Depends(require_image_admin)])
async def ingest_curated_web_image_urls(manifest: dict = Body(...)) -> dict:
    """Fetch curated NASA image URLs server-side and store them pending review."""
    if not isinstance(manifest, dict):
        raise HTTPException(status_code=422, detail="Manifest must be a JSON object.")
    lesson_id = str(manifest.get("lesson_id", "")).strip()
    records = manifest.get("images")
    if not lesson_id or len(lesson_id) > 160 or not isinstance(records, list) or not records or len(records) > 100:
        raise HTTPException(status_code=422, detail="Manifest needs lesson_id and 1–100 image records.")

    prepared, seen = [], set()
    total_batch_bytes = 0
    for item in records:
        if not isinstance(item, dict):
            raise HTTPException(status_code=422, detail="Each image entry must be an object.")
        asset_id = str(item.get("id", "")).strip()
        module_key = str(item.get("module_key", "")).strip()
        step_ids = item.get("step_ids")
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
        if any(not isinstance(step, str) or not SAFE_ID.fullmatch(step) for step in step_ids):
            raise HTTPException(status_code=422, detail="Invalid teaching step ID.")
        if not title or len(title) > 240 or not alt or len(alt) > 1000:
            raise HTTPException(status_code=422, detail="A concise title and descriptive alt_text are required.")
        if not creator or len(creator) > 300 or license_name not in ALLOWED_LICENSES or not attribution:
            raise HTTPException(status_code=422, detail="Creator, supported reuse licence and attribution are required.")
        try:
            validate_source_url(source_url)
            payload, content_type = await fetch_approved_image(source_url)
            total_batch_bytes += len(payload)
            if total_batch_bytes > MAX_CURATED_BATCH_BYTES:
                raise ValueError("Curated batch exceeds the 80 MB total limit.")
        except (ValueError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=422, detail=f"Image source rejected: {str(exc)[:240]}") from exc
        prepared.append({
            "id": asset_id, "module_key": module_key,
            "step_ids": list(dict.fromkeys(step_ids)), "title": title,
            "alt_text": alt, "content_type": content_type, "payload": payload,
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
        known_steps = {str(step.get("id")) for step in lesson_json.get("teaching_sequence", []) if isinstance(step, dict)}
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
                    content_type=EXCLUDED.content_type,alt_text=EXCLUDED.alt_text,
                    status=CASE WHEN lesson_image_assets.status='ready' AND lesson_image_assets.content_fingerprint=EXCLUDED.content_fingerprint THEN 'ready' ELSE 'pending' END,
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
            stored.append({
                "asset_id": item["id"], "module_key": item["module_key"],
                "step_ids": item["step_ids"], "status": "pending",
                "byte_length": len(item["payload"]), "sha256": item["sha256"],
                "source_url": item["source_url"], "license": item["license"],
            })
        conn.commit()
        return {
            "status": "stored_pending_review", "image_count": len(stored),
            "lesson_id": lesson_id, "images": stored,
            "storage": "PostgreSQL BYTEA; source provenance retained",
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Curated image ingestion failed ({type(exc).__name__}).") from exc
    finally:
        conn.close()


# Production startup ingestion for the one founder-approved, reviewed manifest.
# This removes the admin ZIP/API-trigger step. A PostgreSQL advisory lock prevents
# multiple Render instances from fetching/storing the same batch concurrently.
_AUTO_CURATED_LESSON_ID = "10d13a36-87e9-5f3b-8210-f62eb95e8854"
_AUTO_CURATED_LOCK_KEY = (7142026, 7)
_auto_curated_thread: threading.Thread | None = None
_auto_curated_logger = logging.getLogger("padippupal.curated_web_image_ingest")


def _run_auto_curated_ingestion() -> None:
    lock_conn = None
    try:
        # Never run this production content job against a local SQLite database.
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url.startswith(("postgres://", "postgresql://")):
            _auto_curated_logger.info("Automatic curated image ingestion skipped: a PostgreSQL DATABASE_URL is not configured")
            return
        manifest_path = Path(__file__).with_name("curated_beyond_earth_manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("lesson_id") != _AUTO_CURATED_LESSON_ID:
            raise ValueError("Curated manifest lesson allowlist does not match the approved Beyond Earth lesson.")
        lock_conn = connect()
        lock_row = lock_conn.execute(
            "SELECT pg_try_advisory_lock(%s, %s) AS locked",
            _AUTO_CURATED_LOCK_KEY,
        ).fetchone()
        if not lock_row or not lock_row["locked"]:
            _auto_curated_logger.info("Automatic curated image ingestion skipped: another instance owns the lock")
            return
        result = asyncio.run(ingest_curated_web_image_urls(manifest))
        _auto_curated_logger.info(
            "Automatic curated image ingestion finished: lesson_id=%s count=%s status=%s",
            result.get("lesson_id"), result.get("image_count"), result.get("status"),
        )
    except Exception:
        # Do not prevent API startup; the next process start safely retries.
        _auto_curated_logger.exception("Automatic curated image ingestion failed; API startup continues")
    finally:
        if lock_conn is not None:
            lock_conn.close()


def start_auto_curated_ingestion() -> None:
    """Start the approved, idempotent Beyond Earth image fetch after API startup."""
    global _auto_curated_thread
    if _auto_curated_thread is not None and _auto_curated_thread.is_alive():
        return
    _auto_curated_thread = threading.Thread(
        target=_run_auto_curated_ingestion,
        name="curated-beyond-earth-image-ingest",
        daemon=True,
    )
    _auto_curated_thread.start()
