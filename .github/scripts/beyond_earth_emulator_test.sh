#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p ui-screenshots
REPORT="ui-screenshots/beyond-earth-image-test.txt"
ADB=(adb -s emulator-5554)
log() { printf '%s\n' "$*" | tee -a "$REPORT"; }
dump() {
  local name="$1"
  timeout 20s "${ADB[@]}" shell uiautomator dump "/data/local/tmp/$name.xml" >/dev/null
  timeout 10s "${ADB[@]}" pull "/data/local/tmp/$name.xml" "$name.xml" >/dev/null
}
: > "$REPORT"
python3 - <<'PY'
import json
p=json.load(open("beyond-earth-image-manifest.json", encoding="utf-8"))
assert p.get("lesson_id") == "10d13a36-87e9-5f3b-8210-f62eb95e8854"
assert len(p.get("images", [])) == 19
print("PASS: emulator is configured with the 19-asset production manifest")
PY
log "Resetting app to a clean CBSE Class 6 English profile"
"${ADB[@]}" shell am force-stop com.padippupal.app
"${ADB[@]}" shell run-as com.padippupal.app rm -f shared_prefs/padippupal_profile.xml shared_prefs/padippupal_tutor_sessions.xml
"${ADB[@]}" shell run-as com.padippupal.app sh -c 'mkdir -p shared_prefs && echo PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiIHN0YW5kYWxvbmU9InllcyIgPz48bWFwPjxzdHJpbmcgbmFtZT0iZ3JhZGUiPjY8L3N0cmluZz48c3RyaW5nIG5hbWU9ImJvYXJkIj5DQlNFPC9zdHJpbmc+PHN0cmluZyBuYW1lPSJtZWRpdW0iPkVuZ2xpc2g8L3N0cmluZz48c3RyaW5nIG5hbWU9Imxhbmd1YWdlIj5FbmdsaXNoPC9zdHJpbmc+PC9tYXA+ | base64 -d > shared_prefs/padippupal_profile.xml && test -s shared_prefs/padippupal_profile.xml'
"${ADB[@]}" shell am start -n com.padippupal.app/.MainActivity
sleep 12
dump beyond-home
python3 .github/scripts/ui_smoke.py assert-home beyond-home.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap beyond-home.xml "Start learning"
sleep 5
dump beyond-settings
python3 .github/scripts/ui_smoke.py assert-settings beyond-settings.xml | tee -a "$REPORT"
log "Selecting Science (not Mathematics)"
python3 .github/scripts/ui_smoke.py tap beyond-settings.xml "Science"
sleep 5
dump beyond-science-settings
python3 .github/scripts/ui_smoke.py assert-chapter-button beyond-science-settings.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap beyond-science-settings.xml "Choose chapter"
sleep 2
dump beyond-chapter-menu
python3 .github/scripts/ui_smoke.py tap-numbered beyond-chapter-menu.xml 1
sleep 3
dump beyond-chapter-selected
grep -qi "Beyond Earth" beyond-chapter-selected.xml || { log "FAIL: Science chapter picker did not select Beyond Earth"; exit 1; }
# Selecting the chapter preselects its first real curriculum topic.
python3 .github/scripts/ui_smoke.py tap beyond-chapter-selected.xml "Done"
sleep 3
dump beyond-ready-to-teach
python3 .github/scripts/ui_smoke.py assert-tutor beyond-ready-to-teach.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap-exact beyond-ready-to-teach.xml "▶ Teach"
log "Waiting up to 90 seconds for the production-mapped image to load in the live tutor"
deadline=$((SECONDS + 90))
shown=0
while [ "$SECONDS" -lt "$deadline" ]; do
  rm -f beyond-live.xml
  timeout 8s "${ADB[@]}" shell rm -f /data/local/tmp/beyond-live.xml >/dev/null 2>&1 || true
  timeout 8s "${ADB[@]}" shell uiautomator dump /data/local/tmp/beyond-live.xml >/dev/null 2>&1 || true
  timeout 10s "${ADB[@]}" pull /data/local/tmp/beyond-live.xml beyond-live.xml >/dev/null 2>&1 || true
  timeout 10s "${ADB[@]}" exec-out screencap -p > ui-screenshots/beyond-earth-inline.png || true
  if [ -s beyond-live.xml ] && python3 .github/scripts/assert_beyond_earth_image_ui.py beyond-live.xml ui-screenshots/beyond-earth-inline.png beyond-earth-image-manifest.json; then
    shown=1
    break
  fi
  sleep 2
done
if [ "$shown" -ne 1 ]; then
  log "FAIL: live tutor did not expose a decoded mapped Beyond Earth image within 90 seconds"
  [ ! -s beyond-live.xml ] || cat beyond-live.xml >> "$REPORT"
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/beyond-earth-failure.png || true
  exit 1
fi
log "PASS: Science → Beyond Earth → live tutor displayed a mapped production image inline"
log "RESULT: PASS"
