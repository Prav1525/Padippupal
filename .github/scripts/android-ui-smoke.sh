#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p ui-screenshots
REPORT="ui-screenshots/test-report.txt"
: > "$REPORT"
ADB=(adb -s emulator-5554)
log() { printf '%s\n' "$*" | tee -a "$REPORT"; }
capture_diagnostics() {
  rc=$?
  if command -v adb >/dev/null 2>&1; then
    adb -s emulator-5554 logcat -d > ui-screenshots/logcat.txt 2>&1 || true
    adb -s emulator-5554 shell dumpsys activity activities > ui-screenshots/activities.txt 2>&1 || true
    adb -s emulator-5554 shell dumpsys window > ui-screenshots/windows.txt 2>&1 || true
  fi
  if [ "$rc" -ne 0 ]; then log "RESULT: FAIL (exit $rc)"; else log "RESULT: PASS"; fi
  exit "$rc"
}
trap capture_diagnostics EXIT

adb devices -l | tee ui-screenshots/adb-devices.txt
"${ADB[@]}" shell getprop sys.boot_completed | tee -a "$REPORT"
log "Installing debug APK"
timeout 120s "${ADB[@]}" install -r app/build/outputs/apk/debug/app-debug.apk
"${ADB[@]}" shell am force-stop com.padippupal.app
"${ADB[@]}" shell am start -n com.padippupal.app/.MainActivity

started=0
for attempt in $(seq 1 30); do
  if "${ADB[@]}" shell pidof com.padippupal.app 2>/dev/null | grep -q '[0-9]'; then
    started=1
    break
  fi
  sleep 2
done
if [ "$started" -ne 1 ]; then
  log "FAIL: app process did not start within 60 seconds"
  exit 1
fi
sleep 20
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home.png
dump_ui() {
  local remote="$1" local_file="$2" attempt
  for attempt in $(seq 1 8); do
    "${ADB[@]}" shell rm -f "$remote" >/dev/null 2>&1 || true
    if timeout 35s "${ADB[@]}" shell uiautomator dump "$remote" 2>&1 | tee -a "$REPORT"; then
      if "${ADB[@]}" pull "$remote" "$local_file" >/dev/null 2>&1 && [ -s "$local_file" ] && grep -q '<hierarchy' "$local_file"; then
        return 0
      fi
    fi
    log "Accessibility tree not ready for $local_file (attempt $attempt/8); waiting 5 seconds"
    sleep 5
  done
  log "FAIL: accessibility tree unavailable after retries for $local_file"
  "${ADB[@]}" exec-out screencap -p > "ui-screenshots/failed-$(basename "$local_file" .xml).png" || true
  return 1
}
dump_ui /data/local/tmp/home.xml home.xml
python3 .github/scripts/ui_smoke.py assert-home home.xml | tee -a "$REPORT"

log "Set test profile to Class 6 CBSE, English medium"
python3 .github/scripts/ui_smoke.py tap home.xml "You"
profile_ready=0
for attempt in $(seq 1 6); do
  dump_ui /data/local/tmp/profile.xml profile.xml
  if grep -qi "Edit student details" profile.xml; then
    profile_ready=1
    log "PASS: profile screen became visible (attempt $attempt)"
    break
  fi
  log "Profile screen not visible after You tap (attempt $attempt/6)"
  if grep -qi "YOUR LEARNING DESK" profile.xml; then
    python3 .github/scripts/ui_smoke.py tap profile.xml "You" || true
  fi
  sleep 2
done
if [ "$profile_ready" -ne 1 ]; then
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/profile-navigation-failed.png || true
  python3 - <<'PY' | tee -a "$REPORT"
import xml.etree.ElementTree as ET
root=ET.parse("profile.xml").getroot()
print("LAST SCREEN LABELS:", " | ".join(n.attrib.get("text","").strip() for n in root.iter("node") if n.attrib.get("text","").strip())[:2500])
PY
  log "FAIL: tapping You did not navigate to the profile screen"
  exit 1
fi
python3 .github/scripts/ui_smoke.py tap profile.xml "Edit student details"
sleep 2
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/setup.xml
"${ADB[@]}" pull /data/local/tmp/setup.xml setup.xml
python3 .github/scripts/ui_smoke.py tap setup.xml "Education board"
sleep 1
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/board-options.xml
"${ADB[@]}" pull /data/local/tmp/board-options.xml board-options.xml
python3 .github/scripts/ui_smoke.py tap board-options.xml "CBSE"
sleep 1
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/setup-cbse.xml
"${ADB[@]}" pull /data/local/tmp/setup-cbse.xml setup-cbse.xml
python3 .github/scripts/ui_smoke.py tap setup-cbse.xml "Save my details"
sleep 3

# Saving the profile returns to the profile page, not Home. Navigate explicitly
# to Home before asserting home-screen labels or opening the tutor.
dump_ui /data/local/tmp/profile-saved.xml profile-saved.xml
if grep -qi "Edit student details" profile-saved.xml; then
  log "Profile saved; explicitly navigating back to Home tab"
  python3 .github/scripts/ui_smoke.py tap profile-saved.xml "Home"
  sleep 3
fi
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home-cbse.png
dump_ui /data/local/tmp/home-cbse.xml home-cbse.xml
python3 .github/scripts/ui_smoke.py assert-home home-cbse.xml | tee -a "$REPORT"

log "Opening tutor using accessibility bounds"
python3 .github/scripts/ui_smoke.py tap home-cbse.xml "Begin lesson"
sleep 8
"${ADB[@]}" exec-out screencap -p > ui-screenshots/tutor.png
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml || {
  sleep 3
  timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml
}
"${ADB[@]}" pull /data/local/tmp/tutor.xml tutor.xml
python3 .github/scripts/ui_smoke.py assert-tutor tutor.xml | tee -a "$REPORT"

log "Testing the I understand feedback action"
python3 .github/scripts/ui_smoke.py tap tutor.xml "I understand"
sleep 2
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/feedback.xml
"${ADB[@]}" pull /data/local/tmp/feedback.xml feedback.xml
"${ADB[@]}" exec-out screencap -p > ui-screenshots/feedback.png
python3 .github/scripts/ui_smoke.py assert-feedback feedback.xml | tee -a "$REPORT"

log "Testing tutor settings and voice controls"
python3 .github/scripts/ui_smoke.py tap feedback.xml "Change"
sleep 2
"${ADB[@]}" exec-out screencap -p > ui-screenshots/settings.png
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/settings.xml
"${ADB[@]}" pull /data/local/tmp/settings.xml settings.xml
python3 .github/scripts/ui_smoke.py assert-settings settings.xml | tee -a "$REPORT"

log "Loading the real CBSE Mathematics chapter list"
python3 .github/scripts/ui_smoke.py tap settings.xml "Mathematics"
sleep 10
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-options.xml
"${ADB[@]}" pull /data/local/tmp/chapter-options.xml chapter-options.xml
python3 .github/scripts/ui_smoke.py assert-chapter-button chapter-options.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap chapter-options.xml "Choose chapter"
sleep 2
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-menu.xml
"${ADB[@]}" pull /data/local/tmp/chapter-menu.xml chapter-menu.xml
python3 .github/scripts/ui_smoke.py tap-numbered chapter-menu.xml 1
sleep 3
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-selected.xml
"${ADB[@]}" pull /data/local/tmp/chapter-selected.xml chapter-selected.xml
python3 .github/scripts/ui_smoke.py tap chapter-selected.xml "Choose concept"
sleep 2
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-menu.xml
"${ADB[@]}" pull /data/local/tmp/concept-menu.xml concept-menu.xml
python3 .github/scripts/ui_smoke.py tap-first-concept concept-menu.xml
sleep 2
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-selected.xml
"${ADB[@]}" pull /data/local/tmp/concept-selected.xml concept-selected.xml
python3 .github/scripts/ui_smoke.py tap concept-selected.xml "Done"
sleep 3
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/ready-to-teach.xml
"${ADB[@]}" pull /data/local/tmp/ready-to-teach.xml ready-to-teach.xml
python3 .github/scripts/ui_smoke.py tap ready-to-teach.xml "Teach"

log "Recording live lesson frames to verify inline spoken-word highlighting"
"${ADB[@]}" shell rm -rf /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell mkdir -p /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell 'i=0; while [ "$i" -lt 35 ]; do screencap -p "/data/local/tmp/padippupal-live-frames/frame-$i.png"; i=$((i+1)); sleep 1; done'
"${ADB[@]}" pull /data/local/tmp/padippupal-live-frames ui-screenshots/live-frames
"${ADB[@]}" exec-out screencap -p > ui-screenshots/live-lesson.png
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-lesson.xml
"${ADB[@]}" pull /data/local/tmp/live-lesson.xml live-lesson.xml
python3 .github/scripts/ui_smoke.py assert-live live-lesson.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py assert-highlight-frames live-lesson.xml ui-screenshots/live-frames | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap live-lesson.xml "Stop"
sleep 2

log "Testing Android back navigation to Home"
"${ADB[@]}" shell input keyevent 4
sleep 5
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home-return.png
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml || {
  sleep 3
  timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml
}
"${ADB[@]}" pull /data/local/tmp/home-return.xml home-return.xml
python3 .github/scripts/ui_smoke.py assert-home home-return.xml | tee -a "$REPORT"
log "PASS: Class 6 CBSE Mathematics Chapter 1 selection, live lesson, inline highlighting, tutor feedback, and back navigation"
