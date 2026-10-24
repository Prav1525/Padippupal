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
"${ADB[@]}" shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Download/PadippuPal-diary-test.jpg >/dev/null || true
sleep 2
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
# DocumentsUI initially opens Downloads in a thumbnail grid. Switch to
# list view first, then select the actual file row; the previous revision tried
# to parse a list-view dump that had never been created.
python3 - <<'PY'
import re, subprocess, xml.etree.ElementTree as ET
p="ui-screenshots/diary-test/diary-picker-downloads.xml"
root=ET.parse(p).getroot()
button=next((n for n in root.iter("node") if n.attrib.get("content-desc")=="List view"),None)
if button is None: raise SystemExit("DocumentsUI list-view control missing")
m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",button.attrib.get("bounds",""))
if not m: raise SystemExit("DocumentsUI list-view control has invalid bounds")
x1,y1,x2,y2=map(int,m.groups())
subprocess.run(["adb","-s","emulator-5554","shell","input","tap",str((x1+x2)//2),str((y1+y2)//2)],check=True,timeout=20)
PY
sleep 1
dump_ui diary-picker-list
python3 - <<'PY'
import re, subprocess, xml.etree.ElementTree as ET
path="ui-screenshots/diary-test/diary-picker-list.xml"
root=ET.parse(path).getroot()
file_node=next((n for n in root.iter("node") if "PadippuPal-diary-test.jpg" in (n.attrib.get("text","")+" "+n.attrib.get("content-desc",""))),None)
if file_node is None: raise SystemExit("Diary fixture missing from DocumentsUI list view")
parents={child:node for node in root.iter() for child in node}
row=file_node
ancestor=parents.get(file_node)
while ancestor is not None:
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",ancestor.attrib.get("bounds",""))
    if ancestor.attrib.get("resource-id")=="com.android.documentsui:id/item_root" and m:
        row=ancestor
        break
    ancestor=parents.get(ancestor)
m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",row.attrib.get("bounds",""))
if not m: raise SystemExit("Diary filename/row has no valid bounds")
# Tap the filename node itself, not the far-right side of the row.
# On this DocumentsUI build, tapping the row's right side can select/check
# the row without opening the file, leaving the test stuck in Downloads.
fm=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",file_node.attrib.get("bounds",""))
if not fm: raise SystemExit("Diary filename node has invalid bounds")
fx1,fy1,fx2,fy2=map(int,fm.groups())
x=(fx1+fx2)//2
y=(fy1+fy2)//2
print(f"Tap diary filename at {x},{y}; filename bounds={fm.group(0)}, row bounds={m.group(0)}")
subprocess.run(["adb","-s","emulator-5554","shell","input","tap",str(x),str(y)],check=True,timeout=20)
PY
sleep 1
dump_ui diary-picker-row-selected
# DocumentsUI's Open/Select action is more reliable than a fast double-tap,
# which can be interpreted as a row selection on some emulator/API versions.
python3 - <<'PY'
import re, subprocess, xml.etree.ElementTree as ET
p="ui-screenshots/diary-test/diary-picker-row-selected.xml"
root=ET.parse(p).getroot()
actions=[]
for n in root.iter("node"):
    label=(n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip()
    if re.search(r"^(Open|Select|Use this file)$",label,re.I):
        m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",n.attrib.get("bounds",""))
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            if x2>x1 and y2>y1: actions.append((label,(x1+x2)//2,(y1+y2)//2))
if actions:
    label,x,y=actions[-1]
    print(f"Confirm selected diary image using {label} at {x},{y}")
    subprocess.run(["adb","-s","emulator-5554","shell","input","tap",str(x),str(y)],check=True,timeout=20)
else:
    # On API 30 DocumentsUI, tapping the filename may only focus/select the row.
    # Press Enter to activate that focused document instead of repeating a tap
    # (which can toggle selection or hit the row checkbox on some builds).
    print("No explicit Open/Select action exposed; activating focused file with ENTER")
    subprocess.run(["adb","-s","emulator-5554","shell","input","keyevent","KEYCODE_ENTER"],check=True,timeout=20)
PY
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
