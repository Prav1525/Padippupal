#!/usr/bin/env python3
"""Assert the live tutor exposes an image whose accessible label is in the production manifest."""
from __future__ import annotations
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

EXPECTED_HEADING = "Beyond Earth — original textbook images"

def inspect_ui(xml_path: Path, screenshot_path: Path, manifest_path: Path) -> tuple[str, int, tuple[int, int]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_labels = {
        str(item.get("title") or item.get("alt_text") or "").strip()
        for item in manifest.get("images", [])
    }
    expected_labels.discard("")
    if not expected_labels:
        raise SystemExit("FAIL: production manifest contains no accessible image labels")

    root = ET.parse(xml_path).getroot()
    nodes = list(root.iter("node"))
    text = " ".join(node.attrib.get("text", "").strip() for node in nodes)
    if EXPECTED_HEADING.casefold() not in text.casefold():
        raise SystemExit(f"FAIL: tutor UI is missing the '{EXPECTED_HEADING}' section heading")

    matching_images = [
        node for node in nodes
        if node.attrib.get("class") == "android.widget.ImageView"
        and node.attrib.get("content-desc", "").strip() in expected_labels
    ]
    if not matching_images:
        raise SystemExit("FAIL: no accessible ImageView label matches a production manifest title/alt_text")

    if not screenshot_path.is_file():
        raise SystemExit("FAIL: tutor screenshot was not captured")
    try:
        with Image.open(screenshot_path) as screenshot:
            screenshot.load()
            dimensions = screenshot.size
    except Exception as exc:
        raise SystemExit(f"FAIL: emulator screenshot cannot be decoded: {exc}") from exc
    if dimensions[0] < 300 or dimensions[1] < 500:
        raise SystemExit(f"FAIL: screenshot dimensions are not a usable emulator capture: {dimensions}")
    return matching_images[0].attrib["content-desc"].strip(), len(manifest.get("images", [])), dimensions

def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: assert_beyond_earth_image_ui.py UI_XML SCREENSHOT MANIFEST")
    label, manifest_count, (width, height) = inspect_ui(*map(Path, sys.argv[1:]))
    print(f"PASS: tutor UI exposes the original textbook image section ({manifest_count} manifest assets)")
    print(f"PASS: accessible ImageView label matches production manifest: {label}")
    print(f"PASS: actual emulator screenshot decoded ({width}x{height})")

if __name__ == "__main__":
    main()
