#!/usr/bin/env python3
"""Create a deterministic diary-page image for UI-only tests; OCR is mocked."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path("ui-screenshots/padippupal-diary-fixture.jpg")
out.parent.mkdir(parents=True, exist_ok=True)
w, h = 900, 1350
im = Image.new("RGB", (w, h), (248, 244, 230))
d = ImageDraw.Draw(im)
# Notebook ruling and margin.
for y in range(90, h, 54):
    d.line((35, y, w-30, y), fill=(177, 202, 221), width=2)
d.line((105, 35, 105, h-30), fill=(220, 145, 155), width=3)
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(size, bold=False):
    return ImageFont.truetype(bold_path if bold else font_path, size)
d.text((155, 45), "Homework Diary", font=font(42, True), fill=(36, 57, 96))
d.line((155, 102, 480, 102), fill=(36, 57, 96), width=3)
entries = [
    ("23/10/2026  Friday", ["English: Read lesson 4", "Maths: Questions 1 - 5"]),
    ("24/10/2026  Saturday", ["Science: Learn chapter 5", "Tamil: Write page 18"]),
    ("25/10/2026  Sunday", ["Social Studies: Revise map", "English: Workbook page 32"]),
]
y = 155
for date, tasks in entries:
    d.text((140, y), date, font=font(32, True), fill=(36, 57, 96))
    y += 62
    for task in tasks:
        d.text((170, y), task, font=font(28), fill=(36, 57, 96))
        y += 54
    y += 75
im.save(out, "JPEG", quality=88, optimize=True)
print(f"Created deterministic diary UI fixture: {out} ({out.stat().st_size} bytes)")
