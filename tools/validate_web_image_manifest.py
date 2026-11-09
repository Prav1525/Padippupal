#!/usr/bin/env python3
"""Validate curated web-image candidates before any pending-only ingestion."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_IMAGE_HOSTS = {"upload.wikimedia.org"}
ALLOWED_PAGE_HOSTS = {"commons.wikimedia.org"}
ALLOWED_LICENSES = {"CC BY 4.0", "CC BY-SA 4.0", "Public domain (USDA)", "Public domain (USDA ARS)"}

def read(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate(web: dict, authored: dict) -> list[str]:
    errors: list[str] = []
    records = web.get("images")
    if not isinstance(records, list) or not records:
        return ["web source manifest must contain image records"]
    authored_keys = {(x.get("lesson_id"), x.get("module_key")) for x in authored.get("images", [])}
    seen = set()
    for index, item in enumerate(records, 1):
        prefix = f"image {index}"
        required = ("title", "lesson_id", "module_key", "step_ids", "image_url",
                    "source_page_url", "license_name", "license_url", "creator",
                    "attribution", "alt_text")
        for field in required:
            if not item.get(field):
                errors.append(f"{prefix}: missing {field}")
        if any(not item.get(field) for field in required):
            continue
        key = (item["lesson_id"], item["module_key"])
        if key in seen:
            errors.append(f"{prefix}: duplicate web mapping")
        seen.add(key)
        if key in authored_keys:
            errors.append(f"{prefix}: duplicates an original PNG mapping")
        steps = item["step_ids"]
        expected = [f"step_{item['module_key'].removeprefix('module-')}"]
        if not isinstance(steps, list) or steps != expected:
            errors.append(f"{prefix}: module_key and step_ids do not match")
        for field, allowed in (("image_url", ALLOWED_IMAGE_HOSTS), ("source_page_url", ALLOWED_PAGE_HOSTS)):
            parsed = urlsplit(item[field])
            if parsed.scheme != "https" or parsed.hostname not in allowed or parsed.username or parsed.password:
                errors.append(f"{prefix}: {field} host/scheme is not allow-listed")
        license_url = urlsplit(item["license_url"])
        if license_url.scheme != "https" or not license_url.hostname:
            errors.append(f"{prefix}: license_url must be HTTPS")
        if item["license_name"] not in ALLOWED_LICENSES:
            errors.append(f"{prefix}: license requires manual legal review")
        if len(item["alt_text"]) < 20 or len(item["attribution"]) < 15:
            errors.append(f"{prefix}: alt text or attribution is too short")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-manifest", required=True)
    parser.add_argument("--authoring-manifest", required=True)
    args = parser.parse_args()
    errors = validate(read(args.web_manifest), read(args.authoring_manifest))
    if errors:
        raise SystemExit("\\n".join(errors))
    print(f"PASS: {len(read(args.web_manifest)['images'])} web image candidates have module, source and licence metadata.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
