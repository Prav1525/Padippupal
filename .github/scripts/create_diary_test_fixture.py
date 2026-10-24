#!/usr/bin/env python3
"""Create a stable multi-date diary page for deterministic UI-test fallback."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path("ui-screenshots/padippupal-diary-fixture.jpg")
out.parent.mkdir(parents=True, exist_ok=True)
width, height = 900, 1350
image = Image.new("RGB", (width, height), (248, 244, 230))
draw = ImageDraw.Draw(image)
for y in range(90, height, 54):
    draw.line((35, y, width - 30, y), fill=(177, 202, 221), width=2)
draw.line((105, 35, 105, height - 30), fill=(220, 145, 155), width=3)
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(size, heavy=False):
    return ImageFont.truetype(bold if heavy else regular, size)

draw.text((155, 45), "Homework Diary", font=font(42, True), fill=(36, 57, 96))
draw.line((155, 102, 480, 102), fill=(36, 57, 96), width=3)
groups = [
    (155, "23/10/2026  Friday", ["English: Read lesson 4", "Maths: Questions 1 - 5"]),
    (465, "24/10/2026  Saturday", ["Science: Learn chapter 5", "Tamil: Write page 18"]),
    (775, "25/10/2026  Sunday", ["Social Studies: Revise map", "English: Workbook page 32"]),
]
for y, date, tasks in groups:
    draw.text((140, y), date, font=font(32, True), fill=(36, 57, 96))
    for index, task in enumerate(tasks):
        draw.text((170, y + 62 + index * 54), task, font=font(28), fill=(36, 57, 96))
image.save(out, "JPEG", quality=88, optimize=True)
print(f"Created diary UI fixture: {out} ({out.stat().st_size} bytes)")
