#!/usr/bin/env python3
"""Upload the approved Beyond Earth lesson images to Neon branchable storage.

Run from the repository root. This script is deliberately pinned to the three
development assets and refuses production-looking database targets.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import struct
import sys
from pathlib import Path

import boto3
import psycopg
from botocore.config import Config

PROJECT_LESSON_ID = "10d13a36-87e9-5f3b-8210-f62eb95e8854"
BUCKET = "padippupal-science-visuals"
ASSETS = (
    ("beyond-earth-solar-system-v1", "solar-system-v1.png", "beyond-earth/class-6/solar-system-v1.png"),
    ("beyond-earth-day-night-v1", "day-and-night-v1.png", "beyond-earth/class-6/day-and-night-v1.png"),
    ("beyond-earth-moon-phases-v1", "moon-phases-v1.png", "beyond-earth/class-6/moon-phases-v1.png"),
)


def png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Asset is not a valid PNG")
    return struct.unpack(">II", data[16:24])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-dir", type=Path, default=Path("backend/assets/beyond-earth"))
    parser.add_argument("--apply", action="store_true", help="Actually upload and update development DB rows")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing objects only when explicitly requested")
    args = parser.parse_args()

    if not args.apply:
        print("DRY RUN: pass --apply to upload files and update database statuses.")
        return 0

    database_url = os.environ.get("DATABASE_URL", "")
    endpoint = os.environ.get("AWS_ENDPOINT_URL_S3", "")
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    if not all((database_url, endpoint, access_key, secret_key)):
        raise SystemExit("Missing DATABASE_URL, AWS_ENDPOINT_URL_S3, AWS_ACCESS_KEY_ID, or AWS_SECRET_ACCESS_KEY")
    if any(word in database_url.lower() for word in ("prod", "production")):
        raise SystemExit("Refusing to write to a production-looking DATABASE_URL")

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    verified: list[tuple[str, str, str, int, int, int]] = []
    for asset_id, filename, key in ASSETS:
        path = args.assets_dir / filename
        if not path.is_file():
            raise SystemExit(f"Missing asset file: {path}")
        payload = path.read_bytes()
        width, height = png_dimensions(payload)
        digest = hashlib.sha256(payload).hexdigest()
        try:
            head = s3.head_object(Bucket=BUCKET, Key=key)
            same = head.get("Metadata", {}).get("sha256") == digest and head.get("ContentLength") == len(payload)
            if not same and not args.overwrite:
                raise SystemExit(f"Object already exists with different content: s3://{BUCKET}/{key}; rerun with --overwrite")
            if not same:
                s3.put_object(Bucket=BUCKET, Key=key, Body=payload, ContentType="image/png", Metadata={"sha256": digest})
        except s3.exceptions.ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code not in ("404", "NoSuchKey", "NotFound"):
                raise
            s3.put_object(Bucket=BUCKET, Key=key, Body=payload, ContentType="image/png", Metadata={"sha256": digest})

        head = s3.head_object(Bucket=BUCKET, Key=key)
        if head.get("Metadata", {}).get("sha256") != digest or head.get("ContentLength") != len(payload):
            raise RuntimeError(f"Post-upload verification failed for {key}")
        verified.append((asset_id, key, digest, len(payload), width, height))
        print(f"VERIFIED s3://{BUCKET}/{key} bytes={len(payload)} sha256={digest}")

    # Update only the exact development lesson rows after every object is verified.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for asset_id, key, digest, size, width, height in verified:
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
                    (digest, width, height, asset_id, PROJECT_LESSON_ID, BUCKET, key),
                )
                if cur.fetchone() is None:
                    raise RuntimeError(f"Expected development metadata row not found or not eligible: {asset_id}")
        conn.commit()

    print(f"SUCCESS: uploaded and verified {len(verified)} images; matching DB rows set to uploaded.")
    print("TutorScreen consumption/readiness is a separate integration and is not asserted by this script.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
