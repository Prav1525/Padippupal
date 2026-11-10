#!/usr/bin/env bash
set -Eeuo pipefail

ADB=(adb -s emulator-5554)
mkdir -p ui-screenshots/production-image
REPORT=ui-screenshots/production-image/test-report.txt
: > "$REPORT"
capture() {
  local name="$1"
  local remote="/data/local/tmp/${name}.xml"
  local local_file="ui-screenshots/production-image/${name}.xml"
  local attempt
  rm -f "$local_file"
  for attempt in 1 2 3 4 5; do
    timeout 10s "${ADB[@]}" shell rm -f "$remote" >/dev/null 2>&1 || true
    # UIAutomator occasionally starts before the Compose accessibility root is
    # attached on a cold emulator. Never reuse stale XML; retry a fresh dump.
    if timeout 15s "${ADB[@]}" shell uiautomator dump --compressed "$remote" >/dev/null 2>&1 &&
       timeout 10s "${ADB[@]}" pull "$remote" "$local_file" >/dev/null 2>&1 &&
       [ -s "$local_file" ] &&
       python3 - "$local_file" <<'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
raise SystemExit(0 if root.tag == "hierarchy" and len(list(root.iter("node"))) else 1)
PY
    then
      echo "Captured fresh accessibility tree: $name (attempt $attempt)"
      return 0
    fi
    rm -f "$local_file"
    sleep 2
  done
  timeout 10s "${ADB[@]}" exec-out screencap -p > "ui-screenshots/production-image/${name}-failure.png" 2>/dev/null || true
  timeout 10s "${ADB[@]}" shell service check accessibility > "ui-screenshots/production-image/accessibility-service.txt" 2>&1 || true
  echo "FAIL: UIAutomator returned no usable hierarchy for $name after 5 fresh attempts" >&2
  return 1
}
tap() {
  local xml="$1" action="$2" label="${3:-}"
  python3 .github/scripts/ui_smoke.py "$action" "$xml" "$label"
}
fail_diagnostics() {
  rc=$?
  timeout 15s "${ADB[@]}" logcat -d > ui-screenshots/production-image/logcat.txt 2>&1 || true
  timeout 15s "${ADB[@]}" shell dumpsys activity activities > ui-screenshots/production-image/activities.txt 2>&1 || true
  echo "RESULT: $([ "$rc" -eq 0 ] && echo PASS || echo FAIL)" | tee -a "$REPORT"
  exit "$rc"
}
trap fail_diagnostics EXIT

timeout 30s "${ADB[@]}" wait-for-device
ready=0
for attempt in $(seq 1 36); do
  if [ "$(timeout 5s "${ADB[@]}" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] &&
     timeout 10s "${ADB[@]}" shell cmd package list packages >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 5
done
test "$ready" -eq 1

timeout 60s "${ADB[@]}" install -r app/build/outputs/apk/debug/app-debug.apk
timeout 15s "${ADB[@]}" shell run-as com.padippupal.app rm -f shared_prefs/padippupal_profile.xml
"${ADB[@]}" shell run-as com.padippupal.app rm -f shared_prefs/padippupal_tutor_sessions.xml
PROFILE_XML='<?xml version="1.0" encoding="utf-8" standalone="yes" ?><map><string name="grade">6</string><string name="board">CBSE</string><string name="medium">English</string><string name="language">English</string></map>'
PROFILE_B64="$(printf '%s' "$PROFILE_XML" | base64 -w0)"
timeout 15s "${ADB[@]}" shell "run-as com.padippupal.app sh -c 'mkdir -p shared_prefs && echo $PROFILE_B64 | base64 -d > shared_prefs/padippupal_profile.xml'"
timeout 10s "${ADB[@]}" shell am force-stop com.padippupal.app
timeout 15s "${ADB[@]}" shell am start -n com.padippupal.app/.MainActivity
sleep 12

capture home
tap ui-screenshots/production-image/home.xml assert-home
tap ui-screenshots/production-image/home.xml tap "Start learning"
sleep 5
capture lesson-setup
tap ui-screenshots/production-image/lesson-setup.xml tap "Science"
sleep 5
capture science-setup
tap ui-screenshots/production-image/science-setup.xml tap "Choose chapter"
sleep 2
capture chapter-menu
tap ui-screenshots/production-image/chapter-menu.xml tap-numbered "1"
sleep 4
capture chapter-selected
tap ui-screenshots/production-image/chapter-selected.xml tap-exact "Done"
sleep 4
capture ready-to-teach
tap ui-screenshots/production-image/ready-to-teach.xml tap-exact "▶ Teach"

echo "Waiting for both production image descriptions and both verified production PNG downloads (max 120s)" | tee -a "$REPORT"
success=0
for attempt in $(seq 1 60); do
  capture live-image-screen
  if python3 - <<'PY'
import json
import urllib.request
import xml.etree.ElementTree as ET

report = json.load(urllib.request.urlopen("http://127.0.0.1:8765/__test/report", timeout=5))
titles = report.get("expected_titles", [])
verified = set(report.get("verified_image_ids", []))
if len(titles) != 2 or len(verified) != 2 or report.get("errors"):
    raise SystemExit(1)
root = ET.parse("ui-screenshots/production-image/live-image-screen.xml").getroot()
labels = "\n".join(
    value for node in root.iter("node")
    for value in (node.attrib.get("text", ""), node.attrib.get("content-desc", ""))
    if value
)
if not all(title in labels for title in titles):
    raise SystemExit(1)
PY
  then
    success=1
    break
  fi
  sleep 2
done

if [ "$success" -ne 1 ]; then
  curl --max-time 5 --fail --silent http://127.0.0.1:8765/__test/report > ui-screenshots/production-image/proxy-report-on-failure.json || true
  echo "FAIL: both production paired-image descriptions and PNG downloads did not appear together on the live tutor screen" | tee -a "$REPORT"
  exit 1
fi

curl --fail --silent http://127.0.0.1:8765/__test/report > ui-screenshots/production-image/proxy-report.json
# Scroll the teaching canvas so the full paired diagrams can be inspected
# together; this proves the content remains reachable without being squeezed.
timeout 10s "${ADB[@]}" shell input swipe 540 1680 540 650 600
sleep 1
capture live-image-screen-scrolled
timeout 10s "${ADB[@]}" exec-out screencap -p > ui-screenshots/production-image/live-image-screen.png
python3 .github/scripts/ui_smoke.py assert-production-pair-layout ui-screenshots/production-image/live-image-screen-scrolled.xml
python3 - <<'PY'
from PIL import Image
from pathlib import Path
path = Path("ui-screenshots/production-image/live-image-screen.png")
image = Image.open(path).convert("RGB")
if image.width < 400 or image.height < 700:
    raise SystemExit(f"Unexpected emulator screenshot dimensions: {image.size}")
if len(set(image.resize((80, 140)).getdata())) < 30:
    raise SystemExit("Tutor screenshot appears blank or visually uniform")
print(f"PASS: captured non-blank tutor screen screenshot {image.width}x{image.height}")
PY

python3 - <<'PY' | tee -a "$REPORT"
import json
from pathlib import Path
report = json.loads(Path("ui-screenshots/production-image/proxy-report.json").read_text())
ids = set(report.get("verified_image_ids", []))
titles = report.get("expected_titles", [])
if report.get("manifest_requests", 0) < 1:
    raise SystemExit("Production image manifest was not fetched")
if len(ids) != 2 or len(titles) != 2:
    raise SystemExit(f"Expected both production paired images; ids={len(ids)}, titles={len(titles)}")
if report.get("errors"):
    raise SystemExit("Production image proxy recorded errors: " + "; ".join(report["errors"]))
if report.get("production_writes") != 0:
    raise SystemExit("A write was attempted against the production service")
print("PASS: both production PNGs were fetched, SHA-256/size/dimensions verified, and exposed by the Android tutor screen")
print("Verified production image IDs:", ", ".join(sorted(ids)))
print("Visible image descriptions:", " | ".join(titles))
print("Production upstream requests were GET-only; production_writes=0")
PY

echo "PASS: Android tutor rendered both live production Exploring Magnets paired images inline." | tee -a "$REPORT"
