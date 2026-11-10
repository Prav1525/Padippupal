#!/usr/bin/env python3
"""Unit checks for the read-only production paired-image proxy."""
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("production_image_smoke_proxy.py")
SPEC = importlib.util.spec_from_file_location("production_image_smoke_proxy", MODULE_PATH)
proxy = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(proxy)


def item(asset_id: str, title: str) -> dict:
    return {
        "id": asset_id,
        "module_key": proxy.TARGET_MODULE_KEY,
        "step_ids": [proxy.TARGET_STEP_ID],
        "title": title,
        "url": f"/chapter-lessons/{proxy.TARGET_LESSON_ID}/images/{asset_id}",
        "sha256": "a" * 64,
        "byte_length": 4096,
    }


class ProductionImageProxyTests(unittest.TestCase):
    def test_accepts_exact_two_images_for_approved_paired_step(self):
        payload = {
            "lesson_id": proxy.TARGET_LESSON_ID,
            "images": [
                item("magnet-poles", "Magnet poles"),
                item("compass", "Compass direction"),
            ],
        }
        selected = proxy.validate_pair_manifest(payload)
        self.assertEqual(len(selected), 2)
        self.assertEqual(set(proxy.ALLOWED_IMAGES), {
            f"/chapter-lessons/{proxy.TARGET_LESSON_ID}/images/magnet-poles",
            f"/chapter-lessons/{proxy.TARGET_LESSON_ID}/images/compass",
        })

    def test_rejects_missing_paired_image(self):
        payload = {
            "lesson_id": proxy.TARGET_LESSON_ID,
            "images": [item("magnet-poles", "Magnet poles")],
        }
        with self.assertRaisesRegex(ValueError, "exactly two"):
            proxy.validate_pair_manifest(payload)

    def test_rejects_wrong_lesson_id(self):
        payload = {
            "lesson_id": "another-lesson",
            "images": [
                item("magnet-poles", "Magnet poles"),
                item("compass", "Compass direction"),
            ],
        }
        with self.assertRaisesRegex(ValueError, "wrong lesson_id"):
            proxy.validate_pair_manifest(payload)

    def test_rejects_wrong_step_mapping(self):
        wrong = item("magnet-poles", "Magnet poles")
        wrong["step_ids"] = ["step_5"]
        payload = {
            "lesson_id": proxy.TARGET_LESSON_ID,
            "images": [wrong, item("compass", "Compass direction")],
        }
        with self.assertRaisesRegex(ValueError, "exactly two"):
            proxy.validate_pair_manifest(payload)

    def test_lesson_plan_targets_the_production_pair(self):
        payload = proxy.build_lesson_plan()
        visual = payload["interactive_lesson"]
        self.assertEqual(payload["lesson_id"], proxy.TARGET_LESSON_ID)
        self.assertEqual(visual["lesson_id"], proxy.TARGET_LESSON_ID)
        self.assertEqual(visual["module_key"], proxy.TARGET_MODULE_KEY)
        self.assertEqual(visual["steps"][0]["id"], proxy.TARGET_STEP_ID)
        self.assertGreaterEqual(len(payload["segments"][0]["spoken_text"]), 220)


if __name__ == "__main__":
    unittest.main(verbosity=2)
