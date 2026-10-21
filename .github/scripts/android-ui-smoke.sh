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

# Emulator boot_completed can become 1 while Android's package/activity services
# are still restarting. Do not race PackageManager with APK installation.
log "Waiting for Android framework and PackageManager readiness (max 180s)"
timeout 30s adb -s emulator-5554 wait-for-device
ready=0
for attempt in $(seq 1 36); do
  booted=$("${ADB[@]}" shell getprop sys.boot_completed 2>/dev/null | tr -d '\\r' || true)
  package_service=$("${ADB[@]}" shell service check package 2>/dev/null || true)
  activity_service=$("${ADB[@]}" shell service check activity 2>/dev/null || true)
  if [ "$booted" = "1" ] && echo "$package_service" | grep -q "found" && echo "$activity_service" | grep -q "found"; then
    # A service can be registered before it is responsive; prove PackageManager
    # can answer a real query before attempting install.
    if timeout 10s "${ADB[@]}" shell cmd package list packages >/dev/null 2>&1; then
      ready=1
      break
    fi
  fi
  log "Android services not ready yet (attempt $attempt/36; boot=$booted; package=$package_service; activity=$activity_service)"
  sleep 5
done
if [ "$ready" -ne 1 ]; then
  log "FAIL: Android framework/PackageManager did not become responsive within 180 seconds"
  "${ADB[@]}" shell getprop > ui-screenshots/getprop.txt 2>&1 || true
  "${ADB[@]}" shell service list > ui-screenshots/services.txt 2>&1 || true
  exit 1
fi
"${ADB[@]}" shell getprop sys.boot_completed | tee -a "$REPORT"
log "Installing debug APK (up to 3 attempts after framework readiness)"
installed=0
for attempt in 1 2 3; do
  if timeout 60s "${ADB[@]}" install -r app/build/outputs/apk/debug/app-debug.apk; then
    installed=1
    break
  fi
  log "APK install attempt $attempt failed; collecting package-service state and reconnecting ADB"
  "${ADB[@]}" shell service check package >> "$REPORT" 2>&1 || true
  "${ADB[@]}" shell cmd package list packages > "ui-screenshots/packages-attempt-$attempt.txt" 2>&1 || true
  adb reconnect offline >/dev/null 2>&1 || true
  timeout 20s adb -s emulator-5554 wait-for-device || true
  sleep 5
done
if [ "$installed" -ne 1 ]; then
  log "FAIL: APK install failed after 3 bounded attempts"
  exit 1
fi
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

log "Loading the real Mathematics chapter list"
python3 .github/scripts/ui_smoke.py tap settings.xml "Mathematics"
sleep 10
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-options.xml
"${ADB[@]}" pull /data/local/tmp/chapter-options.xml chapter-options.xml
python3 .github/scripts/ui_smoke.py assert-chapter-button chapter-options.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap chapter-options.xml "Choose chapter"
sleep 2
timeout 120s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-menu.xml
"${ADB[@]}" pull /data/local/tmp/chapter-menu.xml chapter-menu.xml
python3 .github/scripts/ui_smoke.py tap-numbered chapter-menu.xml 2
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
log "PASS: app launch, home UI, tutor navigation, tutor UI, and back navigation"
