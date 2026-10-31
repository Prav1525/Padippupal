"""Admin-only, free-tier image generation for approved lesson visuals.

Uses Cloudflare Workers AI FLUX.1 Schnell and writes generated PNGs directly
to the configured Neon S3-compatible object store. This endpoint is disabled
unless an explicit development-only environment flag is set.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import os
import re
import struct
from typing import Any

import boto3
import httpx
import psycopg
from botocore.config import Config
from fastapi import APIRouter, Header, HTTPException, Depends
from PIL import Image

router = APIRouter(prefix="/admin/visuals", tags=["admin-visual-generation"])

LESSON_ID = "10d13a36-87e9-5f3b-8210-f62eb95e8854"
BUCKET = "padippupal-science-visuals"
MODEL = "@cf/black-forest-labs/flux-1-schnell"
ASSETS: dict[str, dict[str, str]] = {
    "beyond-earth-solar-system-v1": {
        "filename": "solar-system-v1.png",
        "key": "beyond-earth/class-6/solar-system-v1.png",
        "prompt": (
            "A clear CBSE class 6 science teaching illustration, hand-drawn with "
            "pencil and coloured crayon on a clean white classroom board, friendly "
            "teacher-sketch style. Show the Sun, Earth and Moon with scientifically "
            "clear relative positions and separate labelled orbital paths. Use "
            "simple legible labels: Sun, Earth, Moon, Earth's orbit, Moon's orbit. "
            "Keep the composition spacious, accurate and child-friendly. No extra "
            "planets, no decorative border, no watermark, no paragraphs."
        ),
    },
    "beyond-earth-day-night-v1": {
        "filename": "day-and-night-v1.png",
        "key": "beyond-earth/class-6/day-and-night-v1.png",
        "prompt": (
            "A clear CBSE class 6 science teaching illustration, hand-drawn pencil "
            "and coloured crayon classroom-board style on white. Show sunlight "
            "travelling from a Sun at left toward Earth. Earth is a sphere with "
            "the half facing the Sun illuminated and labelled DAY, the opposite "
            "half dark and labelled NIGHT. Add a simple tilted axis and a curved "
            "rotation arrow around Earth. Scientific geometry must be clear; "
            "child-friendly, uncluttered, no watermark or extra text."
        ),
    },
    "beyond-earth-moon-phases-v1": {
        "filename": "moon-phases-v1.png",
        "key": "beyond-earth/class-6/moon-phases-v1.png",
        "prompt": (
            "A clear CBSE class 6 science teaching illustration, hand-drawn pencil "
            "and coloured crayon classroom-board style on white. Explain Moon "
            "phases with a consistent sunlight direction from the Sun. Show and "
            "label New Moon, Crescent, First Quarter, Gibbous, Full Moon, Last "
            "Quarter and Crescent in a clean sequence. Keep phase shapes accurate, "
            "labels short and readable, child-friendly, no watermark or paragraphs."
        ),
    },
}


def _require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("PADIPPUPAL_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Admin API is disabled.")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid admin token.")


def _development_config() -> tuple[str, str, str, str, str]:
    if os.getenv("PADIPPUPAL_VISUALS_ENV") != "development":
        raise HTTPException(status_code=503, detail="Image generation is enabled only for the development environment.")
    database_url = os.getenv("DATABASE_URL", "")
    endpoint = os.getenv("AWS_ENDPOINT_URL_S3", "")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
    if not all((database_url, endpoint, access_key, secret_key, account_id, api_token)):
        raise HTTPException(status_code=503, detail="Image generation or development storage credentials are not configured.")
    if re.search(r"prod|production", database_url, re.IGNORECASE):
        raise HTTPException(status_code=403, detail="Refusing to write to a production-looking database.")
    return database_url, endpoint, access_key, secret_key, account_id + ":" + api_token


def _png_bytes(raw: bytes) -> tuple[bytes, int, int]:
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            image = image.convert("RGB")
            if image.width < 512 or image.height < 512 or image.width > 2048 or image.height > 2048:
                raise ValueError("Generated image dimensions are outside the accepted range.")
            output = io.BytesIO()
            image.save(output, format="PNG", optimize=True)
            png = output.getvalue()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Image provider returned an invalid image.") from exc
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=502, detail="Image conversion did not produce a PNG.")
    width, height = struct.unpack(">II", png[16:24])
    return png, width, height


@router.post("/generate/{asset_id}", dependencies=[Depends(_require_admin)])
async def generate_lesson_visual(asset_id: str) -> dict[str, Any]:
    """Generate one allow-listed Beyond Earth visual and store it directly in dev Neon."""
    asset = ASSETS.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Unknown visual asset.")
    database_url, endpoint, access_key, secret_key, cloudflare = _development_config()
    account_id, api_token = cloudflare.split(":", 1)

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=15.0)) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_token}"},
                json={"prompt": asset["prompt"], "steps": 4},
            )
        response.raise_for_status()
        payload = response.json()
        encoded = payload.get("result", {}).get("image") or payload.get("image")
        if not encoded:
            raise ValueError("Image provider response did not contain image data.")
        raw = base64.b64decode(encoded, validate=True)
    except httpx.HTTPStatusError as exc:
        # Never return provider response bodies, which may contain account details.
        raise HTTPException(status_code=502, detail=f"Image provider request failed ({exc.response.status_code}).") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Image provider response could not be decoded.") from exc

    png, width, height = _png_bytes(raw)
    digest = hashlib.sha256(png).hexdigest()
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=os.getenv("AWS_REGION", "ap-southeast-1"),
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=asset["key"],
            Body=png,
            ContentType="image/png",
            CacheControl="public, max-age=31536000, immutable",
            Metadata={"sha256": digest, "generator": "cloudflare-flux-1-schnell"},
        )
        head = s3.head_object(Bucket=BUCKET, Key=asset["key"])
        if head.get("Metadata", {}).get("sha256") != digest or head.get("ContentLength") != len(png):
            raise RuntimeError("Stored object checksum verification failed.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Neon object upload or verification failed.") from exc

    try:
        with psycopg.connect(database_url, connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE lesson_image_assets
                       SET status = 'uploaded',
                           content_fingerprint = %s,
                           width_px = %s,
                           height_px = %s,
                           updated_at = now()
                     WHERE id = %s
                       AND lesson_id = %s
                       AND bucket_name = %s
                       AND object_key = %s
                       AND status IN ('pending', 'uploaded')
                    RETURNING id
                    """,
                    (digest, width, height, asset_id, LESSON_ID, BUCKET, asset["key"]),
                )
                if cur.fetchone() is None:
                    raise RuntimeError("Matching pending development metadata row was not found.")
            conn.commit()
    except Exception as exc:
        # The uploaded object remains unreferenced if metadata update fails; do not mark it ready.
        raise HTTPException(status_code=409, detail="Image stored but lesson metadata update failed; asset is not marked ready.") from exc

    return {
        "asset_id": asset_id,
        "status": "uploaded",
        "bucket": BUCKET,
        "object_key": asset["key"],
        "content_type": "image/png",
        "width": width,
        "height": height,
        "bytes": len(png),
        "sha256": digest,
        "model": MODEL,
        "billing_policy": "Cloudflare Workers AI free daily allocation; no paid fallback",
    }
