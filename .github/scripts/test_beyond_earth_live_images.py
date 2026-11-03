#!/usr/bin/env python3
"""Verify the live Beyond Earth image manifest and every referenced image blob.

This is a production-read-only acceptance check. It deliberately fails closed:
no fixture/generated image can satisfy this test.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin

BASE_URL = os.environ.get(
    "PADIPPUPAL_API_BASE_URL",
    "https://padippupal-curriculum-api.onrender.com",
).rstrip("/")
LESSON_ID = os.environ.get(
    "PADIPPUPAL_BEYOND_EARTH_LESSON_ID",
    "10d13a36-87e9-5f3b-8210-f62eb95e8854",
)
TIMEOUT = 20


def get(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "PadippuPal-live-image-acceptance/1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read(), response.headers.get("Content-Type", "").split(";")[0].lower()


def main() -> int:
    manifest_url = f"{BASE_URL}/chapter-lessons/{LESSON_ID}/images"
    print(f"Checking live manifest: {manifest_url}")
    try:
        raw, content_type = get(manifest_url)
        if "json" not in content_type:
            raise AssertionError(f"Manifest returned unexpected content type: {content_type!r}")
        manifest = json.loads(raw)
        assets = manifest.get("images")
        if not isinstance(assets, list) or not assets:
            raise AssertionError("Live manifest contains no images; refusing to pass with fixture or placeholder data")
        print(f"Manifest returned {len(assets)} image records")
        seen: set[str] = set()
        verified = 0
        for index, asset in enumerate(assets, start=1):
            asset_id = str(asset.get("id", "")).strip()
            path = str(asset.get("url", "")).strip()
            expected_type = str(asset.get("content_type", "")).split(";")[0].lower()
            expected_hash = str(asset.get("sha256", "")).strip().lower()
            expected_length = asset.get("byte_length")
            if not asset_id or not path:
                raise AssertionError(f"Image record {index} lacks id/url")
            if asset_id in seen:
                raise AssertionError(f"Duplicate image asset id in manifest: {asset_id}")
            seen.add(asset_id)
            blob_url = urljoin(BASE_URL + "/", path.lstrip("/"))
            blob, actual_type = get(blob_url)
            if not actual_type.startswith("image/"):
                raise AssertionError(f"{asset_id}: expected image/* response, got {actual_type!r}")
            if expected_type and actual_type != expected_type:
                raise AssertionError(f"{asset_id}: content type mismatch expected={expected_type} actual={actual_type}")
            if len(blob) < 128:
                raise AssertionError(f"{asset_id}: image blob suspiciously small ({len(blob)} bytes)")
            if isinstance(expected_length, int) and len(blob) != expected_length:
                raise AssertionError(f"{asset_id}: byte length mismatch expected={expected_length} actual={len(blob)}")
            digest = hashlib.sha256(blob).hexdigest()
            if expected_hash and digest != expected_hash:
                raise AssertionError(f"{asset_id}: SHA-256 mismatch")
            if not asset.get("module_key") and not asset.get("step_ids"):
                raise AssertionError(f"{asset_id}: image has no module_key or step_ids mapping")
            print(f"PASS {index:02d}: {asset_id} {actual_type} {len(blob)} bytes mapped={asset.get('module_key') or asset.get('step_ids')}")
            verified += 1
        print(f"PASS: verified {verified} live Beyond Earth image blobs, MIME types, hashes/lengths when supplied, and mappings")
        return 0
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, AssertionError) as exc:
        print(f"FAIL: live Beyond Earth image acceptance check: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
