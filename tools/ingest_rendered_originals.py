#!/usr/bin/env python3
"""Upload rendered original lesson PNGs to protected pending-review storage.

This script refuses to run unless PADIPPUPAL_CONFIRM_PENDING_INGESTION=true.
It never approves or publishes assets.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import requests


def main() -> int:
    if os.environ.get("PADIPPUPAL_CONFIRM_PENDING_INGESTION", "").lower() != "true":
        raise SystemExit("Refusing upload: set PADIPPUPAL_CONFIRM_PENDING_INGESTION=true only after explicit approval.")
    base_url = os.environ.get("PADIPPUPAL_API_BASE_URL", "").rstrip("/")
    token = os.environ.get("PADIPPUPAL_ADMIN_TOKEN", "")
    if not base_url.startswith("https://") or not token:
        raise SystemExit("PADIPPUPAL_API_BASE_URL (HTTPS) and PADIPPUPAL_ADMIN_TOKEN are required.")
    manifest_path = Path(sys.argv[1] if len(sys.argv) > 1 else "")
    if not manifest_path.is_file():
        raise SystemExit("Rendered manifest file was not found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest.get("images", [])
    if not isinstance(records, list) or not records:
        raise SystemExit("Rendered manifest contains no images.")
    root = manifest_path.resolve().parent
    endpoint = base_url + "/admin/lesson-images/ingest-original"
    uploaded = []
    for record in records:
        for file_name in record.get("files", []):
            path = Path(file_name).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise SystemExit(f"Refusing file outside rendered output directory: {path}")
            data = {
                "lesson_id": record["lesson_id"],
                "module_key": record["module_key"],
                "step_ids_json": json.dumps(record["step_ids"]),
                "alt_text": record["alt_text"],
                "title": record["title"],
            }
            with path.open("rb") as image_file:
                response = requests.post(
                    endpoint,
                    headers={"x-admin-token": token},
                    data=data,
                    files={"file": (path.name, image_file, "image/png")},
                    timeout=45,
                )
            response.raise_for_status()
            result = response.json()
            if (result.get("status") != "pending_review"
                    or result.get("student_visible") is not False
                    or result.get("lesson_id") != record["lesson_id"]
                    or result.get("module_key") != record["module_key"]):
                raise SystemExit(f"Server did not confirm safe pending storage for {path.name}: {result}")
            uploaded.append({"asset_id": result.get("asset_id"), "lesson_id": record["lesson_id"],
                             "module_key": record["module_key"], "file": path.name})
    print(json.dumps({"uploaded_pending": len(uploaded), "published": 0, "assets": uploaded}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
