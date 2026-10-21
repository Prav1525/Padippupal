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
    adb -s emulator-5554 shell dumpsys connectivity > ui-screenshots/connectivity.txt 2>&1 || true
    adb -s emulator-5554 logcat -d -s System.err AndroidRuntime OkHttp OkHttpClient TrafficStats NetworkSecurityConfig > ui-screenshots/network-errors.txt 2>&1 || true
  fi
  if [ "$rc" -ne 0 ]; then log "RESULT: FAIL (exit $rc)"; else log "RESULT: PASS"; fi
  exit "$rc"
}
trap capture_diagnostics EXIT

adb devices -l | tee ui-screenshots/adb-devices.txt
"${ADB[@]}" shell getprop sys.boot_completed | tee -a "$REPORT"
log "Installing debug APK"
timeout 25s "${ADB[@]}" install -r app/build/outputs/apk/debug/app-debug.apk
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
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || {
  sleep 3
  timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml
}
"${ADB[@]}" pull /data/local/tmp/home.xml home.xml

# Android may show its first-run immersive-mode education overlay above the app.
# Dismiss it before asserting the actual PadippuPal home screen.
if grep -Fqi 'Viewing full screen' home.xml && grep -Fqi 'GOT IT' home.xml; then
  log "INFO: dismissing Android full-screen education overlay"
  python3 .github/scripts/ui_smoke.py tap home.xml "GOT IT" || "${ADB[@]}" shell input tap 540 960
  sleep 3
  timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || true
  "${ADB[@]}" pull /data/local/tmp/home.xml home.xml || true
  "${ADB[@]}" exec-out screencap -p > ui-screenshots/home-after-system-overlay.png
fi

# Retry transient Android System UI ANRs before classifying them as an app UI failure.
for attempt in 1 2 3; do
  if grep -Eqi "System UI isn.t responding|Close app|Wait" home.xml; then
    log "WARNING: Android System UI is unresponsive (attempt $attempt/3)"
    "${ADB[@]}" exec-out screencap -p > "ui-screenshots/home-anr-attempt-$attempt.png" || true
    if [ "$attempt" -lt 3 ]; then
      "${ADB[@]}" shell input keyevent 4 || true
      sleep 10
      "${ADB[@]}" shell am force-stop com.padippupal.app || true
      "${ADB[@]}" shell am start -n com.padippupal.app/.MainActivity || true
      sleep 12
      timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || true
      "${ADB[@]}" pull /data/local/tmp/home.xml home.xml || true
    fi
  else
    break
  fi
done
if grep -Eqi "System UI isn.t responding|Close app|Wait" home.xml; then
  log "FAIL: Android System UI remained unresponsive after 3 attempts"
  exit 1
fi
python3 .github/scripts/ui_smoke.py assert-home home.xml | tee -a "$REPORT"

log "Opening tutor using accessibility bounds"
python3 .github/scripts/ui_smoke.py tap home.xml "Begin lesson"
sleep 8
"${ADB[@]}" exec-out screencap -p > ui-screenshots/tutor.png
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml || {
  sleep 3
  timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml
}
"${ADB[@]}" pull /data/local/tmp/tutor.xml tutor.xml
python3 .github/scripts/ui_smoke.py assert-tutor tutor.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py assert-profile tutor.xml | tee -a "$REPORT"

log "Testing the I understand feedback action"
python3 .github/scripts/ui_smoke.py tap tutor.xml "I understand"
sleep 2
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/feedback.xml
"${ADB[@]}" pull /data/local/tmp/feedback.xml feedback.xml
"${ADB[@]}" exec-out screencap -p > ui-screenshots/feedback.png
python3 .github/scripts/ui_smoke.py assert-feedback feedback.xml | tee -a "$REPORT"

log "Testing tutor settings and voice controls"
python3 .github/scripts/ui_smoke.py tap feedback.xml "Change"
sleep 2
"${ADB[@]}" exec-out screencap -p > ui-screenshots/settings.png
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/settings.xml
"${ADB[@]}" pull /data/local/tmp/settings.xml settings.xml
python3 .github/scripts/ui_smoke.py assert-settings settings.xml | tee -a "$REPORT"

log "Loading the real Mathematics chapter list"
python3 .github/scripts/ui_smoke.py tap settings.xml "Mathematics"
sleep 10
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-options.xml
"${ADB[@]}" pull /data/local/tmp/chapter-options.xml chapter-options.xml
python3 .github/scripts/ui_smoke.py assert-chapter-button chapter-options.xml | tee -a "$REPORT"
# Wait for asynchronous API fetches and fail with the visible UI state, not a
# generic empty-list assertion. Network and app diagnostics are captured on exit.
python3 .github/scripts/ui_smoke.py tap chapter-options.xml "Choose chapter"
sleep 2
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-menu.xml
"${ADB[@]}" pull /data/local/tmp/chapter-menu.xml chapter-menu.xml
python3 .github/scripts/ui_smoke.py assert-chapter-one chapter-menu.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap-numbered chapter-menu.xml 1
sleep 3
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-selected.xml
"${ADB[@]}" pull /data/local/tmp/chapter-selected.xml chapter-selected.xml
python3 .github/scripts/ui_smoke.py assert-selected-chapter chapter-selected.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap chapter-selected.xml "Choose concept"
sleep 2
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-menu.xml
"${ADB[@]}" pull /data/local/tmp/concept-menu.xml concept-menu.xml
python3 .github/scripts/ui_smoke.py tap-first-concept concept-menu.xml
sleep 2
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-selected.xml
"${ADB[@]}" pull /data/local/tmp/concept-selected.xml concept-selected.xml
python3 .github/scripts/ui_smoke.py tap concept-selected.xml "Done"
sleep 3
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/ready-to-teach.xml
"${ADB[@]}" pull /data/local/tmp/ready-to-teach.xml ready-to-teach.xml
python3 .github/scripts/ui_smoke.py tap ready-to-teach.xml "Teach"

log "Recording live lesson frames to verify inline spoken-word highlighting"
"${ADB[@]}" shell rm -rf /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell mkdir -p /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell 'i=0; while [ "$i" -lt 35 ]; do screencap -p "/data/local/tmp/padippupal-live-frames/frame-$i.png"; i=$((i+1)); sleep 1; done'
"${ADB[@]}" pull /data/local/tmp/padippupal-live-frames ui-screenshots/live-frames
"${ADB[@]}" exec-out screencap -p > ui-screenshots/live-lesson.png
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-lesson.xml
"${ADB[@]}" pull /data/local/tmp/live-lesson.xml live-lesson.xml
python3 .github/scripts/ui_smoke.py assert-live live-lesson.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py assert-highlight-frames live-lesson.xml ui-screenshots/live-frames | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap live-lesson.xml "Stop"
sleep 2

log "Testing Android back navigation to Home"
"${ADB[@]}" shell input keyevent 4
sleep 5
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home-return.png
timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml || {
  sleep 3
  timeout 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml
}
"${ADB[@]}" pull /data/local/tmp/home-return.xml home-return.xml
python3 .github/scripts/ui_smoke.py assert-home home-return.xml | tee -a "$REPORT"
log "PASS: app launch, home UI, tutor navigation, tutor UI, and back navigation"
