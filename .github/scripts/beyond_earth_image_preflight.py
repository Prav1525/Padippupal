#!/usr/bin/env python3
"""Read-only production preflight for the Beyond Earth textbook image pipeline."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen
from io import BytesIO

from PIL import Image


LESSON_ID = "10d13a36-87e9-5f3b-8210-f62eb95e8854"


def fetch(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"Accept": "*/*", "User-Agent": "PadippuPal-BeyondEarth-CI/1.0"})
    with urlopen(request, timeout=25) as response:
        return response.read(), response.headers.get("Content-Type", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://padippupal-curriculum-api.onrender.com")
    parser.add_argument("--manifest-output", default="beyond-earth-image-manifest.json")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    manifest_bytes, _ = fetch(f"{base}/chapter-lessons/{LESSON_ID}/images")
    manifest = json.loads(manifest_bytes)
    images = manifest.get("images")
    if manifest.get("lesson_id") != LESSON_ID:
        raise SystemExit(f"FAIL: manifest lesson_id mismatch: {manifest.get('lesson_id')!r}")
    if not isinstance(images, list) or len(images) != 19:
        raise SystemExit(f"FAIL: expected 19 production image assets; received {len(images) if isinstance(images, list) else 'invalid'}")
    ids = [str(item.get("id", "")) for item in images]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise SystemExit("FAIL: manifest contains missing or duplicate image IDs")
    module_counts = Counter(str(item.get("module_key", "")) for item in images)
    if "" in module_counts:
        raise SystemExit("FAIL: at least one image has no module_key")
    verified_bytes = 0
    for index, item in enumerate(images, start=1):
        steps = item.get("step_ids")
        if not isinstance(steps, list) or not steps or not all(isinstance(step, str) and step.strip() for step in steps):
            raise SystemExit(f"FAIL: image {item.get('id')} has no valid step_ids mapping")
        image_url = str(item.get("url", ""))
        if not image_url.startswith(f"/chapter-lessons/{LESSON_ID}/images/"):
            raise SystemExit(f"FAIL: image {item.get('id')} has an unsafe/unexpected URL: {image_url!r}")
        payload, content_type = fetch(base + image_url)
        if not payload:
            raise SystemExit(f"FAIL: image {item.get('id')} returned an empty body")
        with Image.open(BytesIO(payload)) as image:
            image.verify()
        verified_bytes += len(payload)
        print(f"PASS image {index:02d}/19: id={item['id']} module={item['module_key']} steps={len(steps)} bytes={len(payload)} type={content_type or item.get('content_type')}")
    Path(args.manifest_output).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS: {len(images)} production images fetched and decoded; {len(module_counts)} module keys; {verified_bytes} total bytes")
    print(f"PASS: read-only manifest fixture saved to {args.manifest_output}")


if __name__ == "__main__":
    main()
