#!/usr/bin/env python3
"""Regression tests for the Beyond Earth production-image UI assertion."""
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from assert_beyond_earth_image_ui import inspect_ui

class BeyondEarthImageUiAssertionTest(unittest.TestCase):
    def test_accepts_real_tutor_heading_and_manifest_accessibility_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xml = root / "ui.xml"
            screenshot = root / "screen.png"
            manifest = root / "manifest.json"
            xml.write_text('''<hierarchy><node text="Beyond Earth — original textbook images" class="android.widget.TextView" content-desc=""/><node text="" class="android.widget.ImageView" content-desc="Stars in the night sky"/></hierarchy>''', encoding="utf-8")
            manifest.write_text(json.dumps({"images":[{"title":"Stars in the night sky"}]}), encoding="utf-8")
            Image.new("RGB", (1080, 1920)).save(screenshot)
            label, count, dimensions = inspect_ui(xml, screenshot, manifest)
            self.assertEqual(label, "Stars in the night sky")
            self.assertEqual(count, 1)
            self.assertEqual(dimensions, (1080, 1920))

    def test_rejects_unmapped_image_accessibility_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xml = root / "ui.xml"
            screenshot = root / "screen.png"
            manifest = root / "manifest.json"
            xml.write_text('''<hierarchy><node text="Beyond Earth — original textbook images"/><node class="android.widget.ImageView" content-desc="Placeholder image"/></hierarchy>''', encoding="utf-8")
            manifest.write_text(json.dumps({"images":[{"title":"Stars in the night sky"}]}), encoding="utf-8")
            Image.new("RGB", (1080, 1920)).save(screenshot)
            with self.assertRaisesRegex(SystemExit, "does not match a production manifest"):
                inspect_ui(xml, screenshot, manifest)

if __name__ == "__main__":
    unittest.main()
