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

# Avoid am start -W: on hosted software-rendered emulators it may report a false
# timeout while the Activity is actually running.
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
sleep 5
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home.png
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || {
  sleep 3
  timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml
}
"${ADB[@]}" pull /data/local/tmp/home.xml home.xml
python3 .github/scripts/ui_smoke.py assert-home home.xml | tee -a "$REPORT"

log "Opening tutor using accessibility bounds"
python3 .github/scripts/ui_smoke.py tap home.xml "Begin lesson"
sleep 8
"${ADB[@]}" exec-out screencap -p > ui-screenshots/tutor.png
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml || {
  sleep 3
  timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml
}
"${ADB[@]}" pull /data/local/tmp/tutor.xml tutor.xml
python3 .github/scripts/ui_smoke.py assert-tutor tutor.xml | tee -a "$REPORT"

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
log "PASS: app launch, home UI, tutor navigation, tutor UI, and back navigation"
