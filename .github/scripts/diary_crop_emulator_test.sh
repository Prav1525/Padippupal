#!/usr/bin/env bash
# Dedicated deterministic Android emulator test for the diary scan -> crop -> rescan -> save flow.
# Gemini is deliberately mocked by tutor_smoke_api.py; this does not test live OCR.
set -Eeuo pipefail
ADB=(adb -s emulator-5554)
mkdir -p ui-screenshots/diary-test
REPORT=ui-screenshots/diary-test/report.txt
: > "$REPORT"
log(){ printf '%s\n' "$*" | tee -a "$REPORT"; }
dump_ui(){
  local name="$1"
  timeout 20s "${ADB[@]}" shell uiautomator dump "/data/local/tmp/${name}.xml" >/dev/null
  timeout 10s "${ADB[@]}" pull "/data/local/tmp/${name}.xml" "ui-screenshots/diary-test/${name}.xml" >/dev/null
}
tap_label(){
  local xml="$1" label="$2"
  python3 .github/scripts/ui_smoke.py tap "$xml" "$label"
}
assert_has(){
  local xml="$1" label="$2"
  grep -qi "$label" "$xml" || { log "FAIL: '$label' not found in $xml"; exit 1; }
}
log "Preparing deterministic diary image fixture"
python3 .github/scripts/create_diary_test_fixture.py
# Put the fixture in Downloads so Android's document picker can select it
# directly even when the emulator's MediaStore index is cold or empty.
"${ADB[@]}" shell mkdir -p /sdcard/Download
"${ADB[@]}" push ui-screenshots/padippupal-diary-fixture.jpg /sdcard/Download/PadippuPal-diary-test.jpg >/dev/null
# Android 10+ no longer reliably indexes files from the deprecated
# MEDIA_SCANNER_SCAN_FILE broadcast. Register the pushed fixture in MediaStore
# explicitly so DocumentsUI's image-filtered Downloads view can discover it.
"${ADB[@]}" shell content insert --uri content://media/external/images/media \
  --bind _data:s:/storage/emulated/0/Download/PadippuPal-diary-test.jpg \
  --bind mime_type:s:image/jpeg \
  --bind title:s:PadippuPal-diary-test
indexed=0
for attempt in $(seq 1 10); do
  if "${ADB[@]}" shell content query --uri content://media/external/images/media \
      --projection _id:_display_name:_data | grep -Fq "PadippuPal-diary-test.jpg"; then
    indexed=1
    break
  fi
  sleep 1
done
if [ "$indexed" -ne 1 ]; then
  log "FAIL: fixture exists in shared storage but is not indexed in MediaStore; DocumentsUI cannot list it"
  "${ADB[@]}" shell ls -l /sdcard/Download/PadippuPal-diary-test.jpg | tee -a "$REPORT"
  "${ADB[@]}" shell content query --uri content://media/external/images/media --projection _id:_display_name:_data | tee -a "$REPORT"
  exit 1
fi
"${ADB[@]}" shell am force-stop com.padippupal.app
"${ADB[@]}" shell am start -n com.padippupal.app/.MainActivity >/dev/null
sleep 6
# The scan tile is below the first viewport on the compact emulator. Scroll the
# actual home list so the tile is rendered and exposed to accessibility before tapping.
"${ADB[@]}" shell input swipe 520 1450 520 650 450
sleep 1
dump_ui diary-home
python3 .github/scripts/ui_smoke.py tap ui-screenshots/diary-test/diary-home.xml "Scan homework"
sleep 3
dump_ui diary-scanner
cp ui-screenshots/diary-test/diary-scanner.xml ui-screenshots/diary-test/scanner-before-camera.xml
grep -qi "Scan school diary" ui-screenshots/diary-test/diary-scanner.xml
grep -qi "Take photo" ui-screenshots/diary-test/diary-scanner.xml
grep -qi "Choose photo" ui-screenshots/diary-test/diary-scanner.xml
log "Checking camera button launches the system capture flow"
tap_label ui-screenshots/diary-test/diary-scanner.xml "Take photo"
sleep 3
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/camera-launch.png
"${ADB[@]}" shell input keyevent KEYCODE_BACK
sleep 2
dump_ui diary-scanner-return
assert_has ui-screenshots/diary-test/diary-scanner-return.xml "Choose photo"
log "Opening gallery/photo picker"
tap_label ui-screenshots/diary-test/diary-scanner-return.xml "Choose photo"
sleep 3
dump_ui diary-picker
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/photo-picker.png
# The AOSP picker can show "No items" under Recent even when a file was pushed
# successfully. Open its storage roots and select the fixture from Downloads;
# never tap the Gallery provider tile as if it were an image.
"${ADB[@]}" shell input tap 94 147
sleep 1
dump_ui diary-picker-roots
if grep -qi "Downloads" ui-screenshots/diary-test/diary-picker-roots.xml; then
  tap_label ui-screenshots/diary-test/diary-picker-roots.xml "Downloads"
else
  log "FAIL: Downloads root not exposed by Android photo picker"
  exit 1
fi
sleep 2
dump_ui diary-picker-downloads
if ! grep -qi "PadippuPal-diary-test.jpg" ui-screenshots/diary-test/diary-picker-downloads.xml; then
  log "FAIL: diary fixture is not listed in Downloads; refusing to tap a provider/app tile"
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/picker-downloads-empty.png
  exit 1
fi
# In this emulator's image-filtered DocumentsUI grid, the file row and its
# thumbnail are not exposed as clickable accessibility nodes, and long-pressing
# the row does not enter selection mode. The separate preview icon is a different
# action. Tap the actual thumbnail bounds from the live hierarchy, then verify
# the picker returns the selected content URI to PadippuPal.
python3 - <<'PY'
import re, subprocess, time, xml.etree.ElementTree as ET
path="ui-screenshots/diary-test/diary-picker-downloads.xml"
root=ET.parse(path).getroot()
nodes=list(root.iter("node"))
def bounds(n):
 m=re.fullmatch(r"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]",n.attrib.get("bounds",""))
 return tuple(map(int,m.groups())) if m else None
name=next((n for n in nodes if "padippupal-diary-test.jpg" in (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()),None)
if name is None: raise SystemExit("Fixture filename disappeared from DocumentsUI")
# Prefer the thumbnail child, not the distinct 'Preview the file' action.
thumb=next((n for n in name.iter("node") if n.attrib.get("resource-id","").endswith(":id/thumbnail")),None)
if thumb is None:
 thumb=next((n for n in name.iter("node") if n.attrib.get("resource-id","").endswith(":id/icon_thumb")),None)
b=bounds(thumb) if thumb is not None else None
if b is None: raise SystemExit("Fixture thumbnail bounds not found in DocumentsUI hierarchy")
x=(b[0]+b[2])//2; y=(b[1]+b[3])//2
print(f"Tap fixture thumbnail at {x},{y}, bounds={b}; avoid the separate preview icon")
subprocess.run(["adb","-s","emulator-5554","shell","input","tap",str(x),str(y)],check=True,timeout=20)
PY
# Give the picker time to deliver the selected URI and verify the owning package.
for attempt in $(seq 1 8); do
  sleep 1
  dump_ui diary-picker-selection-result
done
if grep -q 'package="com.android.documentsui"' ui-screenshots/diary-test/diary-picker-selection-result.xml; then
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/picker-selection-stuck.png
  log "FAIL: tapping the fixture thumbnail did not return from DocumentsUI; see diary-picker-selection-result.xml and picker-selection-stuck.png"
  exit 1
fi
sleep 1
dump_ui diary-picker-row-selected
# Give DocumentsUI time to return the selected content URI to PadippuPal.
sleep 2
dump_ui diary-picker-confirmed
cp ui-screenshots/diary-test/diary-picker-confirmed.xml ui-screenshots/diary-test/diary-picker-file-selected.xml
if grep -q 'package="com.android.documentsui"' ui-screenshots/diary-test/diary-picker-file-selected.xml; then
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/picker-selection-stuck.png
  log "FAIL: picker remained in DocumentsUI after filename tap/explicit confirmation; see diary-picker-confirmed.xml and picker-selection-stuck.png"
  exit 1
fi
sleep 3
dump_ui diary-photo-selected
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/photo-selected.png
# Prove the picker returned to our app before asserting crop UI. This guards
# against the prior false positive where the Gallery provider was opened.
if ! grep -q 'package="com.padippupal.app"' ui-screenshots/diary-test/diary-photo-selected.xml; then
  log "FAIL: picker did not return to PadippuPal after confirming the fixture"
  exit 1
fi
assert_has ui-screenshots/diary-test/diary-photo-selected.xml "Crop this photo and rescan"
log "Opening crop editor and dragging a selection across the diary page"
tap_label ui-screenshots/diary-test/diary-photo-selected.xml "Crop this photo and rescan"
sleep 2
dump_ui diary-crop-dialog
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/crop-dialog.png
python3 - <<'PY'
import re, subprocess, xml.etree.ElementTree as ET
root=ET.parse("ui-screenshots/diary-test/diary-crop-dialog.xml").getroot()
nodes=list(root.iter("node"))
target=next((n for n in nodes if "diary crop" in n.attrib.get("content-desc","").lower()),None)
if target is None:
    candidates=[]
    for n in nodes:
        m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.attrib.get("bounds",""))
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            if x2-x1>180 and y2-y1>250: candidates.append((n,(x2-x1)*(y2-y1)))
    target=max(candidates,key=lambda z:z[1])[0] if candidates else None
if target is None: raise SystemExit("Crop image node not found; see diary-crop-dialog.xml")
m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",target.attrib.get("bounds",""))
if not m: raise SystemExit("Crop image bounds are invalid")
x1,y1,x2,y2=map(int,m.groups())
sx,ex=x1+int((x2-x1)*.12),x1+int((x2-x1)*.88)
sy,ey=y1+int((y2-y1)*.48),y1+int((y2-y1)*.58)
print(f"Drag crop selection {sx},{sy} -> {ex},{ey} over image {m.group(0)}")
subprocess.run(["adb","-s","emulator-5554","shell","input","swipe",str(sx),str(sy),str(ex),str(ey),"700"],check=True,timeout=45)
PY
sleep 1
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/crop-selected.png
dump_ui diary-crop-selected
assert_has ui-screenshots/diary-test/diary-crop-selected.xml "Rescan crop"
log "Submitting cropped image to deterministic /diary/parse mock"
tap_label ui-screenshots/diary-test/diary-crop-selected.xml "Rescan crop"
for attempt in $(seq 1 20); do
  sleep 1
  dump_ui diary-review
  if grep -qi "Learn chapter 5" ui-screenshots/diary-test/diary-review.xml; then break; fi
done
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/review-tasks.png
assert_has ui-screenshots/diary-test/diary-review.xml "Learn chapter 5"
assert_has ui-screenshots/diary-test/diary-review.xml "Write page 18"
if grep -Eqi "Read lesson 4|Questions 1 - 5|Revise map|Workbook page 32" ui-screenshots/diary-test/diary-review.xml; then
  log "FAIL: neighboring-date homework leaked into review"
  exit 1
fi
log "Saving reviewed tasks and verifying they appear in today's planner"
tap_label ui-screenshots/diary-test/diary-review.xml "Save selected tasks"
for attempt in $(seq 1 20); do
  sleep 1
  dump_ui diary-planner
  if grep -qi "Today's homework" ui-screenshots/diary-test/diary-planner.xml; then break; fi
done
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/saved-planner.png
assert_has ui-screenshots/diary-test/diary-planner.xml "Today's homework"
assert_has ui-screenshots/diary-test/diary-planner.xml "Learn chapter 5"
assert_has ui-screenshots/diary-test/diary-planner.xml "Write page 18"
if grep -Eqi "Read lesson 4|Questions 1 - 5|Revise map|Workbook page 32" ui-screenshots/diary-test/diary-planner.xml; then
  log "FAIL: neighboring-date homework was saved to planner"
  exit 1
fi
log "PASS: diary scanner -> gallery -> crop selection -> rescan -> review -> save -> today's planner"
