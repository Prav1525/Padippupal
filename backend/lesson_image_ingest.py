"""Protected ingestion and delivery of original embedded textbook raster images."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
from io import BytesIO
from zipfile import BadZipFile, ZipFile
import http.client
import ssl
from urllib.parse import urlsplit

import psycopg
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

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
    # A module may contain multiple individual PDF images. Keep the asset ID and
    # object key unique; module_key is a grouping/filtering field, not an asset key.
    conn.execute("""
        ALTER TABLE lesson_image_assets
        DROP CONSTRAINT IF EXISTS lesson_image_assets_lesson_id_module_key_key
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS lesson_image_assets_lesson_module_idx
        ON lesson_image_assets (lesson_id, module_key)
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
    source_id = str(manifest.get("source_id", "")).strip()
    if not re.fullmatch(r"[0-9a-f]{64}", source_hash) or not source_id:
        raise HTTPException(status_code=422, detail="Manifest must include source_id and the verified source PDF SHA-256.")
    records = manifest.get("images")
    if not isinstance(records, list) or not records or len(records) > 300:
        raise HTTPException(status_code=422, detail="Manifest must include 1–300 image records.")
    names = {item.filename for item in archive.infolist() if not item.is_dir()}
    seen_ids = set()
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
        if asset_id in seen_ids:
            raise HTTPException(status_code=422, detail="Duplicate image asset ID in manifest.")
        seen_ids.add(asset_id)
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
        source = conn.execute(
            "SELECT id, sha256, status FROM sources WHERE id=%s",
            (source_id,)
        ).fetchone()
        if not source or source["status"] != "ready" or str(source["sha256"]).lower() != source_hash:
            raise HTTPException(status_code=422, detail="Source PDF ID/hash does not match a ready production source.")
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
                ON CONFLICT (id) DO UPDATE SET
                  lesson_id=EXCLUDED.lesson_id, module_key=EXCLUDED.module_key,
                  title=EXCLUDED.title, step_ids_json=EXCLUDED.step_ids_json,
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


# URL ingestion is deliberately limited to known public educational image hosts.
# Redirects are disabled so an allow-listed URL cannot redirect to an internal host.
URL_IMAGE_HOSTS = {"upload.wikimedia.org", "images.nasa.gov", "hk.space.museum"}
MAX_REMOTE_IMAGE_BYTES = 8 * 1024 * 1024


class RemoteImageInput(BaseModel):
    image_url: str = Field(min_length=12, max_length=2048)
    lesson_id: str = Field(min_length=8, max_length=160)
    module_key: str = Field(min_length=1, max_length=120)
    step_ids: list[str] = Field(min_length=1, max_length=8)
    alt_text: str = Field(min_length=5, max_length=500)
    title: str = Field(default="", max_length=200)
    source_page_url: str = Field(min_length=12, max_length=2048)
    license_name: str = Field(min_length=3, max_length=120)
    license_url: str = Field(min_length=12, max_length=2048)
    creator: str = Field(min_length=2, max_length=200)
    attribution: str = Field(min_length=3, max_length=500)


def _validate_public_image_url(value: str) -> tuple[str, str, str]:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise HTTPException(status_code=422, detail="Image URL must be a credential-free HTTPS URL.")
    host = parsed.hostname.lower().rstrip(".")
    if host not in URL_IMAGE_HOSTS or parsed.port not in (None, 443):
        raise HTTPException(status_code=422, detail="Image host is not on the approved source allow-list.")
    try:
        addresses = {
            str(ipaddress.ip_address(item[4][0]))
            for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Image source DNS lookup failed.") from exc
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise HTTPException(status_code=422, detail="Image source resolved to a non-public network address.")
    # Pin the actual TCP connection to an address from the validated DNS result.
    # TLS still verifies the allow-listed hostname and sends it as SNI.
    return value, host, sorted(addresses)[0]


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, resolved_ip: str, timeout: float = 15):
        super().__init__(host=host, port=443, timeout=timeout, context=ssl.create_default_context())
        self._resolved_ip = resolved_ip

    def connect(self) -> None:
        raw_socket = socket.create_connection((self._resolved_ip, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)
        except Exception:
            raw_socket.close()
            raise


def _image_signature_matches(payload: bytes, content_type: str) -> bool:
    return (
        (content_type == "image/jpeg" and payload.startswith(b"\xff\xd8\xff")) or
        (content_type == "image/png" and payload.startswith(b"\x89PNG\r\n\x1a\n")) or
        (content_type == "image/webp" and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP") or
        (content_type == "image/gif" and payload[:6] in (b"GIF87a", b"GIF89a"))
    )


def _validate_module_step_mapping(module_key: str, step_ids: list[str]) -> None:
    expected_module_keys = {f"module-{step.split('_', 1)[1]}" for step in step_ids}
    if len(expected_module_keys) != 1 or module_key not in expected_module_keys:
        raise HTTPException(
            status_code=422,
            detail="module_key must match the mapped teaching step (for example, step_2 uses module-2).",
        )

def _validate_lesson_step_mapping(lesson_json: str, module_key: str, step_ids: list[str]) -> None:
    """Ensure requested visual mappings refer to real steps in this approved lesson."""
    try:
        lesson = json.loads(lesson_json or "{}")
        sequence = lesson.get("teaching_sequence", [])
        available_steps = {
            item.get("id") for item in sequence
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Approved lesson has an invalid teaching sequence.")
    if not step_ids or any(step not in available_steps for step in step_ids):
        raise HTTPException(status_code=422, detail="Image step_ids must match existing teaching steps in the approved lesson.")
    _validate_module_step_mapping(module_key, step_ids)


def _fetch_remote_image(url: str, host: str, resolved_ip: str) -> tuple[bytes, str]:
    parsed = urlsplit(url)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    connection = _PinnedHTTPSConnection(host, resolved_ip, timeout=15)
    try:
        connection.request(
            "GET",
            target,
            headers={
                "Host": host,
                "User-Agent": "PadippuPal-LessonImageIngest/1.0",
                "Accept": "image/png,image/jpeg,image/webp,image/gif",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        if 300 <= response.status < 400:
            raise HTTPException(status_code=422, detail="Image redirects are not accepted; use the final approved HTTPS image URL.")
        if response.status != 200:
            raise HTTPException(status_code=502, detail=f"Image source returned HTTP {response.status}.")
        content_type = (response.getheader("Content-Type") or "").split(";", 1)[0].strip().lower()
        if content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=415, detail="Remote source did not return a supported image MIME type.")
        length = response.getheader("Content-Length")
        if length and int(length) > MAX_REMOTE_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Remote image exceeds the 8 MB limit.")
        payload = response.read(MAX_REMOTE_IMAGE_BYTES + 1)
    except HTTPException:
        raise
    except (OSError, http.client.HTTPException, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not retrieve the remote image.") from exc
    finally:
        connection.close()
    if not payload or len(payload) > MAX_REMOTE_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Remote image must be between 1 byte and 8 MB.")
    if not _image_signature_matches(payload, content_type):
        raise HTTPException(status_code=415, detail="Downloaded bytes do not match the declared image MIME type.")
    return payload, content_type


@router.post("/admin/lesson-images/ingest-url", dependencies=[Depends(require_image_admin)])
def ingest_lesson_image_url(payload: RemoteImageInput) -> dict:
    """Fetch one allow-listed HTTPS image and store it for review, not student delivery."""
    image_url, image_host, resolved_ip = _validate_public_image_url(payload.image_url)
    for field_name in ("source_page_url", "license_url"):
        value = getattr(payload, field_name)
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise HTTPException(status_code=422, detail=f"{field_name} must be a valid HTTPS URL.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,120}", payload.module_key):
        raise HTTPException(status_code=422, detail="Invalid module_key.")
    if any(not re.fullmatch(r"step_[1-9][0-9]{0,2}", step) for step in payload.step_ids):
        raise HTTPException(status_code=422, detail="step_ids must use the lesson step_N format.")
    if len(set(payload.step_ids)) != len(payload.step_ids):
        raise HTTPException(status_code=422, detail="Duplicate step_ids are not allowed.")
    _validate_module_step_mapping(payload.module_key, payload.step_ids)

    image_bytes, content_type = _fetch_remote_image(image_url, image_host, resolved_ip)
    fingerprint = hashlib.sha256(image_bytes).hexdigest()
    asset_id = "remote-" + hashlib.sha256(
        f"{payload.lesson_id}|{payload.module_key}|{fingerprint}".encode("utf-8")
    ).hexdigest()[:32]
    conn = connect()
    try:
        lesson = conn.execute(
            "SELECT id, board, class_level, subject, chapter, medium, status, lesson_json FROM chapter_lessons WHERE id=%s",
            (payload.lesson_id,)
        ).fetchone()
        if not lesson or lesson["status"] != "approved":
            raise HTTPException(status_code=422, detail="Images may only attach to an approved lesson.")
        _validate_lesson_step_mapping(lesson["lesson_json"], payload.module_key, payload.step_ids)
        object_key = "lesson-images/{}/{}/{}/{}/{}/{}".format(lesson["board"], lesson["class_level"], lesson["subject"], payload.lesson_id, payload.module_key, asset_id)
        conn.execute("""
            INSERT INTO lesson_image_assets
              (id, lesson_id, module_key, title, step_ids_json, bucket_name, object_key,
               content_type, alt_text, status, content_fingerprint, source_url,
               source_page_url, license_name, license_url, creator, attribution,
               created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
            ON CONFLICT (id) DO UPDATE SET
              title=EXCLUDED.title, step_ids_json=EXCLUDED.step_ids_json,
              content_type=EXCLUDED.content_type, alt_text=EXCLUDED.alt_text,
              status='pending', content_fingerprint=EXCLUDED.content_fingerprint,
              source_url=EXCLUDED.source_url, source_page_url=EXCLUDED.source_page_url,
              license_name=EXCLUDED.license_name, license_url=EXCLUDED.license_url,
              creator=EXCLUDED.creator, attribution=EXCLUDED.attribution, updated_at=NOW()
        """, (asset_id, payload.lesson_id, payload.module_key, payload.title or payload.alt_text,
              json.dumps(payload.step_ids), "postgres-inline-images", object_key, content_type,
              payload.alt_text, fingerprint, image_url, payload.source_page_url,
              payload.license_name, payload.license_url, payload.creator, payload.attribution))
        conn.execute("""
            INSERT INTO lesson_image_asset_blobs (asset_id,image_bytes,sha256,byte_length)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (asset_id) DO UPDATE SET image_bytes=EXCLUDED.image_bytes,
              sha256=EXCLUDED.sha256, byte_length=EXCLUDED.byte_length, created_at=NOW()
        """, (asset_id, image_bytes, fingerprint, len(image_bytes)))
        conn.commit()
        return {"status": "pending", "asset_id": asset_id,
                "lesson_id": payload.lesson_id, "module_key": payload.module_key,
                "step_ids": payload.step_ids, "sha256": fingerprint,
                "byte_length": len(image_bytes), "content_type": content_type,
                "student_visible": False}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Remote image ingestion failed ({type(exc).__name__}).") from exc
    finally:
        conn.close()
