import unittest

import fitz

from lesson_image_quality import is_decorative_warm_texture


def _jpeg_fixture(paper: bool) -> bytes:
    width = height = 64
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            if paper:
                # Pale-yellow paper with subtle texture, matching the bad source blobs.
                delta = (x * 3 + y * 2) % 9 - 4
                rgb = (max(0, min(255, 253 + delta)),
                       max(0, min(255, 208 + delta)),
                       max(0, min(255, 116 + delta)))
            else:
                # A dark star-field-like image must not be rejected for low entropy.
                rgb = (5 + (x * y) % 10, 8 + (x + y) % 10, 15 + (x * y) % 15)
            pixels.extend(rgb)
    pixmap = fitz.Pixmap(fitz.csRGB, width, height, bytes(pixels), False)
    return pixmap.tobytes("jpeg")


class ImageQualityTests(unittest.TestCase):
    def test_decorative_yellow_paper_texture_is_rejected(self):
        self.assertTrue(is_decorative_warm_texture(_jpeg_fixture(paper=True)))

    def test_dark_low_entropy_astronomy_image_is_not_rejected(self):
        self.assertFalse(is_decorative_warm_texture(_jpeg_fixture(paper=False)))


if __name__ == "__main__":
    unittest.main()
