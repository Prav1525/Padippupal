#!/usr/bin/env python3
"""Assert the live tutor exposes the mapped textbook image as an accessible image node."""
from __future__ import annotations
import re, sys, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: assert_beyond_earth_image_ui.py UI_XML SCREENSHOT")
    xml_path, screenshot_path = map(Path, sys.argv[1:])
    root = ET.parse(xml_path).getroot()
    nodes = list(root.iter("node"))
    labels = [node.attrib.get("content-desc", "").strip() for node in nodes]
    image_labels = [label for label in labels if label and "Beyond Earth" not in label]
    text = " ".join(node.attrib.get("text", "") for node in nodes)
    match = re.search(r"(\d+) original textbook images?", text, re.IGNORECASE)
    if not match or int(match.group(1)) < 1:
        raise SystemExit("FAIL: tutor UI has no positive original textbook image count label")
    if not image_labels:
        raise SystemExit("FAIL: tutor UI has no accessible image contentDescription node")
    if not screenshot_path.is_file():
        raise SystemExit("FAIL: tutor screenshot was not captured")
    with Image.open(screenshot_path) as screenshot:
        screenshot.load()
        width, height = screenshot.size
        if width < 300 or height < 500:
            raise SystemExit("FAIL: screenshot dimensions are not a usable emulator capture")
    print(f"PASS: UI reports {match.group(1)} original textbook image(s)")
    print(f"PASS: {len(image_labels)} accessible image node(s) are present")
    print(f"PASS: actual emulator screenshot decoded ({width}x{height})")

if __name__ == "__main__":
    main()
