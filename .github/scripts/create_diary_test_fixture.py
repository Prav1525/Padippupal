#!/usr/bin/env python3
"""Create a syllabus-aligned, multi-date Class 6 CBSE diary image for UI tests.

The current-day row is placed in the crop band's center. The API smoke fixture
returns matching deterministic tasks; it does not perform OCR on these pixels.
"""
from datetime import date, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path("ui-screenshots/padippupal-diary-fixture.jpg")
out.parent.mkdir(parents=True, exist_ok=True)
width, height = 900, 1350
image = Image.new("RGB", (width, height), (250, 247, 237))
draw = ImageDraw.Draw(image)
for y in range(90, height, 54):
    draw.line((35, y, width - 30, y), fill=(185, 205, 221), width=2)
draw.line((105, 35, 105, height - 30), fill=(220, 145, 155), width=3)
regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(size, heavy=False):
    return ImageFont.truetype(bold if heavy else regular, size)

today = date.today()
draw.text((145, 35), "CLASS VI  |  CBSE HOMEWORK DIARY", font=font(31, True), fill=(30, 55, 91))
draw.text((145, 82), "Student: Aarav     Section: A", font=font(24), fill=(50, 70, 100))
draw.line((140, 125, 850, 125), fill=(50, 70, 100), width=3)

groups = [
    (250, today - timedelta(days=1), [
        "English: Read lesson 4",
        "Mathematics: Finish worksheet 2",
    ]),
    (598, today, [
        "Mathematics: Complete Q1-5",
        "Science: Revise Components of Food",
    ]),
    (930, today + timedelta(days=1), [
        "Social Science: Label India map",
        "English: Write a short paragraph",
    ]),
]
for y, day, tasks in groups:
    draw.rounded_rectangle((130, y - 12, 860, y + 160), radius=12,
                           outline=(104, 137, 170), width=2)
    draw.text((150, y), f"{day.strftime('%d/%m/%Y')}  {day.strftime('%A')}",
              font=font(29, True), fill=(30, 55, 91))
    for index, task in enumerate(tasks):
        draw.text((165, y + 62 + index * 54), task, font=font(25),
                  fill=(35, 61, 102))
image.save(out, "JPEG", quality=92, optimize=True)
print(f"Created syllabus-aligned Class 6 CBSE diary fixture: {out} ({out.stat().st_size} bytes)")
print(f"Current diary row: {today.isoformat()} -> Complete Q1-5; Revise Components of Food")
