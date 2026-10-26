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
# The API 35 system Photo Picker intentionally hides filesystem names and
# exposes date-based descriptions on clickable photo tiles. The fixture is the
# sole visible photo in this fresh emulator; select that one tile, failing closed
# if the picker unexpectedly shows zero or multiple selectable photos.
log "Selecting the sole visible fixture tile in the system Photo Picker"
python3 .github/scripts/ui_smoke.py tap-photo-picker-item ui-screenshots/diary-test/diary-picker.xml
sleep 1
dump_ui diary-picker-selection-result
"${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/picker-selection-result.png
returned=0
for attempt in $(seq 1 8); do
  if grep -q 'package="com.padippupal.app"' ui-screenshots/diary-test/diary-picker-selection-result.xml; then
    returned=1
    break
  fi
  sleep 1
  dump_ui diary-picker-selection-result
done
if [ "$returned" -ne 1 ]; then
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/picker-selection-stuck.png
  log "FAIL: PickVisualMedia did not return to PadippuPal after selecting the fixture; inspect selection-result XML/screenshot"
  exit 1
fi
sleep 1
dump_ui diary-picker-confirmed
cp ui-screenshots/diary-test/diary-picker-confirmed.xml ui-screenshots/diary-test/diary-picker-file-selected.xml
if grep -Eq 'package="(com\.android\.documentsui|com\.google\.android\.documentsui)"' ui-screenshots/diary-test/diary-picker-file-selected.xml; then
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/picker-selection-stuck.png
  log "FAIL: picker remained in DocumentsUI after selection confirmation; see diary-picker-confirmed.xml and picker-selection-stuck.png"
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
# The review form is taller than the compact emulator viewport. Validate the
# first visible task, scroll, then dump the newly visible second task and Save action.
assert_has ui-screenshots/diary-test/diary-review.xml "Learn chapter 5"
if grep -Eqi "Read lesson 4|Questions 1 - 5|Revise map|Workbook page 32" ui-screenshots/diary-test/diary-review.xml; then
  log "FAIL: neighboring-date homework leaked into review"
  exit 1
fi
# The review form is taller than the emulator viewport. One swipe reveals the
# second task but not the save action, so scroll in bounded increments and inspect
# a fresh accessibility tree after every gesture rather than assuming one swipe.
review_xml=ui-screenshots/diary-test/diary-review-scrolled.xml
save_visible=0
for scroll_attempt in $(seq 1 8); do
  "${ADB[@]}" shell input swipe 520 1500 520 650 450
  sleep 1
  dump_ui diary-review-scrolled
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/diary-test/review-tasks-scrolled.png
  if grep -qi "Write page 18" "$review_xml"; then
    if grep -Eqi "Read lesson 4|Questions 1 - 5|Revise map|Workbook page 32" "$review_xml"; then
      log "FAIL: neighboring-date homework leaked into scrolled review"
      exit 1
    fi
  fi
  if grep -qi "Save selected tasks" "$review_xml"; then
    save_visible=1
    log "Save action found after scroll attempt $scroll_attempt"
    break
  fi
  log "Save action not visible after scroll attempt $scroll_attempt; continuing bounded scroll"
done
if [ "$save_visible" -ne 1 ]; then
  log "FAIL: Save selected tasks did not become visible after 8 review scroll attempts; see diary-review-scrolled.xml and review-tasks-scrolled.png"
  exit 1
fi
assert_has "$review_xml" "Write page 18"
log "Saving reviewed tasks and verifying them in today planner"
tap_label "$review_xml" "Save selected tasks"
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
