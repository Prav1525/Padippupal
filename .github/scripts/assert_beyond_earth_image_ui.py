#!/usr/bin/env python3
"""Assert the live tutor exposes a production-mapped textbook image."""
from __future__ import annotations
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: assert_beyond_earth_image_ui.py UI_XML SCREENSHOT MANIFEST")
    xml_path, screenshot_path, manifest_path = map(Path, sys.argv[1:])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_labels = {str(item.get("title") or item.get("alt_text") or "").strip()
                       for item in manifest.get("images", [])}
    expected_labels.discard("")
    root = ET.parse(xml_path).getroot()
    nodes = list(root.iter("node"))
    labels = [node.attrib.get("content-desc", "").strip() for node in nodes]
    image_labels = [label for label in labels if label in expected_labels]
    text = " ".join(node.attrib.get("text", "") for node in nodes)
    match = re.search(r"(\d+) original textbook images?", text, re.IGNORECASE)
    if not match or int(match.group(1)) < 1:
        raise SystemExit("FAIL: tutor UI has no positive original textbook image count label")
    if not image_labels:
        raise SystemExit("FAIL: no image contentDescription matches a production manifest title/alt_text")
    if not screenshot_path.is_file():
        raise SystemExit("FAIL: tutor screenshot was not captured")
    with Image.open(screenshot_path) as screenshot:
        screenshot.load()
        width, height = screenshot.size
        if width < 300 or height < 500:
            raise SystemExit("FAIL: screenshot dimensions are not a usable emulator capture")
    print(f"PASS: UI reports {match.group(1)} original textbook image(s)")
    print(f"PASS: {len(image_labels)} accessible image node(s) match production manifest labels")
    print(f"PASS: actual emulator screenshot decoded ({width}x{height})")

if __name__ == "__main__":
    main()
