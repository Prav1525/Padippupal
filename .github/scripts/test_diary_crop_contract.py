#!/usr/bin/env python3
"""Regression contract for diary capture/crop wiring; not a substitute for device OCR."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / "app/src/main/java/com/padippupal/app/StudyFeatures.kt").read_text(encoding="utf-8")

required = {
    "camera launcher": "ActivityResultContracts.TakePicturePreview()",
    "visible camera action": 'Text("  Take photo")',
    "camera button invokes launcher": "onClick = { camera.launch(null) }",
    "gallery image decoded for crop": "BitmapFactory.decodeByteArray(bytes, 0, bytes.size)",
    "gallery image retained": "sourceBitmap = bitmap",
    "crop action visible": "Crop this photo and rescan",
    "crop dialog": "Crop today's diary row",
    "crop overlay layers on image": "Box(Modifier.fillMaxWidth().aspectRatio(bitmap.width.toFloat()/bitmap.height))",
    "selection canvas overlays image": "Canvas(Modifier.fillMaxSize())",
    "crop rescan action": 'Text("Rescan crop")',
    "crop uses same date-guarded scan path": 'scanImage(out.toByteArray(),"image/jpeg","Cropped diary row")',
    "date sent to parser": '"today_date"',
}
missing = [label for label, token in required.items() if token not in source]
for label in required:
    print(("FAIL: " if label in missing else "PASS: ") + label)
if missing:
    raise SystemExit("Diary UI contract failed: " + ", ".join(missing))
print("PASS: diary capture/crop source contract (interactive device test still required)")
