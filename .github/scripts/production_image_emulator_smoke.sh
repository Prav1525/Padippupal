#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p ui-screenshots/production-image
ADB=(adb -s emulator-5554)
OUT=ui-screenshots/production-image
fail() { echo "FAIL: $*" | tee "$OUT/result.txt"; "\${ADB[@]}" logcat -d > "$OUT/logcat.txt" 2>&1 || true; exit 1; }
dump() {
  local name="$1"
  rm -f "$OUT/$name.xml"
  timeout 20s "\${ADB[@]}" shell uiautomator dump "/data/local/tmp/$name.xml" >/dev/null
  timeout 10s "\${ADB[@]}" pull "/data/local/tmp/$name.xml" "$OUT/$name.xml" >/dev/null
}
tap() { python3 .github/scripts/ui_smoke.py tap "$OUT/$1.xml" "$2"; }
wait_proxy_pair() {
  for attempt in $(seq 1 60); do
    curl --fail --silent --show-error http://127.0.0.1:8765/__test/report > "$OUT/proxy-report.json" || true
    if python3 - "$OUT/proxy-report.json" <<'PY'
import json,sys
try:
 d=json.load(open(sys.argv[1]))
 raise SystemExit(0 if len(set(d.get("verified_image_ids",[])))==2 and d.get("manifest_requests",0)>=1 and not d.get("errors") else 1)
except Exception: raise SystemExit(1)
PY
    then return 0; fi
    sleep 2
  done
  cat "$OUT/proxy-report.json" || true
  fail "Android client did not fetch and verify both production image payloads"
}
timeout 30s adb -s emulator-5554 wait-for-device
ready=0
for attempt in $(seq 1 36); do
  if [ "$("\${ADB[@]}" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && timeout 8s "\${ADB[@]}" shell cmd package list packages >/dev/null 2>&1; then ready=1; break; fi
  sleep 5
done
[ "$ready" = 1 ] || fail "Android framework did not become ready"
"\${ADB[@]}" install -r app/build/outputs/apk/debug/app-debug.apk
"\${ADB[@]}" shell "run-as com.padippupal.app rm -f shared_prefs/padippupal_profile.xml shared_prefs/padippupal_tutor_sessions.xml"
"\${ADB[@]}" shell "run-as com.padippupal.app sh -c 'mkdir -p shared_prefs && echo PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiIHN0YW5kYWxvbmU9InllcyIgPz48bWFwPjxzdHJpbmcgbmFtZT0iZ3JhZGU+Njwvc3RyaW5nPjxzdHJpbmcgbmFtZT0iYm9hcmQiPkNCU0U8L3N0cmluZz48c3RyaW5nIG5hbWU9Im1lZGl1bSI+RW5nbGlzaDwvc3RyaW5nPjxzdHJpbmcgbmFtZT0ibGFuZ3VhZ2UiPkVuZ2xpc2g8L3N0cmluZz48L21hcD4= | base64 -d > shared_prefs/padippupal_profile.xml && test -s shared_prefs/padippupal_profile.xml'"
"\${ADB[@]}" shell am force-stop com.padippupal.app
"\${ADB[@]}" shell am start -n com.padippupal.app/.MainActivity
sleep 12
"\${ADB[@]}" exec-out screencap -p > "$OUT/home.png"
dump home
python3 .github/scripts/ui_smoke.py assert-home "$OUT/home.xml"
tap home "Start learning"
sleep 6
dump settings
tap settings "Science"
sleep 6
dump science-settings
grep -qi "Choose chapter" "$OUT/science-settings.xml" || fail "Science chapter picker did not load"
tap science-settings "Choose chapter"
sleep 2
dump science-chapters
python3 .github/scripts/ui_smoke.py tap-numbered "$OUT/science-chapters.xml" 1
sleep 3
dump science-chapter-selected
grep -qi "Exploring Magnets" "$OUT/science-chapter-selected.xml" || fail "Exploring Magnets was not selected"
python3 .github/scripts/ui_smoke.py tap-topic-picker "$OUT/science-chapter-selected.xml"
sleep 2
dump science-topic-menu
python3 .github/scripts/ui_smoke.py tap-first-concept "$OUT/science-topic-menu.xml"
sleep 2
dump science-topic-selected
tap science-topic-selected "Done"
sleep 3
dump science-ready
python3 .github/scripts/ui_smoke.py assert-tutor "$OUT/science-ready.xml"
tap science-ready "Teach"
echo "Waiting for Android to fetch both approved production PNGs."
wait_proxy_pair
"\${ADB[@]}" exec-out screencap -p > "$OUT/production-images.png"
dump production-images
curl --fail --silent --show-error http://127.0.0.1:8765/__test/report > "$OUT/proxy-report.json"
python3 - "$OUT/proxy-report.json" "$OUT/production-images.xml" <<'PY'
import json,sys,xml.etree.ElementTree as ET
r=json.load(open(sys.argv[1]))
assert r["manifest_requests"]>=1 and len(set(r["verified_image_ids"]))==2 and not r["errors"] and r["production_writes"]==0, r
root=ET.parse(sys.argv[2]).getroot()
nodes=list(root.iter("node"))
labels=[n.attrib.get("content-desc","") for n in nodes]+[n.attrib.get("text","") for n in nodes]
assert any("Magnet Poles and Compass Direction" in x for x in labels), labels[:120]
print(json.dumps(r,indent=2))
print("PASS: both production images fetched and lesson visual title is accessible.")
PY
python3 - "$OUT/production-images.png" <<'PY'
from PIL import Image,ImageChops
import sys
im=Image.open(sys.argv[1]).convert("RGB")
assert im.width>=300 and im.height>=500, im.size
crop=im.crop((int(im.width*.04),int(im.height*.20),int(im.width*.96),int(im.height*.92)))
assert ImageChops.difference(crop,Image.new("RGB",crop.size,(255,255,255))).getbbox() is not None
print("PASS: non-blank Android tutor screenshot captured.")
PY
echo "PASS: Android emulator loaded both Exploring Magnets images from production; production writes=0." | tee "$OUT/result.txt"
