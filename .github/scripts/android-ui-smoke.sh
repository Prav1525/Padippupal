#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p ui-screenshots
REPORT="ui-screenshots/test-report.txt"
: > "$REPORT"
ADB=(adb -s emulator-5554)
log() { printf '%s\n' "$*" | tee -a "$REPORT"; }
capture_diagnostics() {
  # Preserve the original failure code. Diagnostics must never turn a quick
  # failure into a multi-minute hang on an unhealthy emulator/ADB transport.
  rc=$?
  set +e
  log "Collecting bounded diagnostics (each ADB call max 5 seconds)"
  if command -v adb >/dev/null 2>&1; then
    timeout -k 1s 5s adb devices -l > ui-screenshots/adb-devices-on-exit.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 get-state > ui-screenshots/adb-state-on-exit.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 logcat -d > ui-screenshots/logcat.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 shell dumpsys activity activities > ui-screenshots/activities.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 shell dumpsys activity lastanr > ui-screenshots/last-anr.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 shell dumpsys dropbox --print system_app_anr > ui-screenshots/system-anr-dropbox.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 shell dumpsys window > ui-screenshots/windows.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 shell ps -A > ui-screenshots/processes.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 shell dumpsys connectivity > ui-screenshots/connectivity.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 logcat -d -b all > ui-screenshots/full-logcat.txt 2>&1
    timeout -k 1s 5s adb -s emulator-5554 logcat -d -s System.err AndroidRuntime OkHttp OkHttpClient TrafficStats NetworkSecurityConfig > ui-screenshots/network-errors.txt 2>&1
  fi
  log "Diagnostics collection finished (some files may contain timeout/offline errors)"
  if [ "$rc" -ne 0 ]; then log "RESULT: FAIL (exit $rc)"; else log "RESULT: PASS"; fi
  exit "$rc"
}
trap capture_diagnostics EXIT

adb devices -l | tee ui-screenshots/adb-devices.txt
"${ADB[@]}" shell getprop sys.boot_completed | tee -a "$REPORT"
log "Checking emulator responsiveness before APK install"
timeout -k 2s 8s "${ADB[@]}" shell getprop sys.boot_completed || {
  log "FAIL: emulator did not respond to ADB health check before install"
  exit 1
}
APK="app/build/outputs/apk/debug/app-debug.apk"
if [ ! -s "$APK" ]; then
  log "FAIL: APK missing or empty at $APK"
  exit 1
fi
log "APK size: $(stat -c '%s' "$APK") bytes"
log "Checking ADB transport and package manager before install"
timeout -k 1s 5s "${ADB[@]}" get-state | tee -a "$REPORT" || {
  log "FAIL_CLASS=EMULATOR_ADB_TRANSPORT"
  log "FAIL: emulator ADB transport is not in device state; refusing install"
  exit 1
}
timeout -k 1s 8s "${ADB[@]}" shell pm path android | tee -a "$REPORT" || {
  log "FAIL_CLASS=EMULATOR_PACKAGE_MANAGER"
  log "FAIL: Android package manager did not answer basic health probe"
  exit 1
}
log "Checking package manager can enumerate installed packages"
timeout -k 1s 10s "${ADB[@]}" shell cmd package list packages --user 0 > ui-screenshots/package-manager-probe.txt 2>&1 || {
  log "FAIL_CLASS=EMULATOR_PACKAGE_MANAGER_STALLED"
  log "FAIL: package manager enumeration stalled before APK install"
  exit 1
}
log "Package manager probe returned $(wc -l < ui-screenshots/package-manager-probe.txt) package lines"
timeout -k 1s 6s "${ADB[@]}" shell dumpsys activity activities > ui-screenshots/preinstall-activities.txt 2>&1 || true
if grep -Eqi "Application Not Responding: com\\.android\\.systemui|System UI isn.t responding" ui-screenshots/preinstall-activities.txt; then
  log "FAIL_CLASS=EMULATOR_SYSTEM_UI_ANR"
  log "FAIL: Android System UI is already in an ANR state before APK installation"
  exit 1
fi
log "Installing debug APK (hard timeout 45 seconds; output captured)"
set +e
timeout -k 2s 45s "${ADB[@]}" install -r "$APK" > ui-screenshots/install-output.txt 2>&1
install_rc=$?
set -e
cat ui-screenshots/install-output.txt | tee -a "$REPORT"
if [ "$install_rc" -ne 0 ]; then
  if [ "$install_rc" -eq 124 ] && [ ! -s ui-screenshots/install-output.txt ]; then
    log "FAIL_CLASS=ADB_INSTALL_CLIENT_STALLED"
    log "FAIL: adb install produced no installer output before timeout; this is not an app UI assertion failure"
  else
    log "FAIL_CLASS=APK_INSTALL_OR_EMULATOR"
    log "FAIL: APK installation failed/timed out (exit $install_rc)"
  fi
  exit "$install_rc"
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
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || {
  sleep 3
  timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml
}
"${ADB[@]}" pull /data/local/tmp/home.xml home.xml

# Android may show its first-run immersive-mode education overlay above the app.
# Dismiss it before asserting the actual PadippuPal home screen.
if grep -Fqi 'Viewing full screen' home.xml && grep -Fqi 'GOT IT' home.xml; then
  log "INFO: dismissing Android full-screen education overlay"
  python3 .github/scripts/ui_smoke.py tap home.xml "GOT IT" || "${ADB[@]}" shell input tap 540 960
  sleep 3
  timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || true
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
      timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || true
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

# Start from a deterministic, clean test profile instead of assuming the app's
# default board is CBSE. Fresh installs currently default to Tamil Nadu State Board.
log "Configuring the smoke-test learner as Class 6 CBSE"
# Compose exposes the bottom navigation as a merged, non-clickable accessibility
# node spanning the whole bar. A text-center tap lands on the middle tab, not You.
# Tap the rightmost tab using the actual emulator width, then assert the destination.
SCREEN_WIDTH=$("${ADB[@]}" shell wm size | sed -n 's/.*Physical size: \\([0-9][0-9]*\\)x.*/\\1/p' | tr -d '\\r')
if [ -z "$SCREEN_WIDTH" ]; then
  log "FAIL_CLASS=UI_GEOMETRY_UNAVAILABLE"
  log "FAIL: unable to determine emulator screen width for profile navigation"
  exit 1
fi
PROFILE_X=$((SCREEN_WIDTH * 7 / 8))
# The bottom bar's accessible bounds are captured in home.xml; use its vertical
# midpoint while targeting the fourth (You) tab horizontally.
PROFILE_Y=$(python3 - <<'PY'
import re, xml.etree.ElementTree as ET
root=ET.parse('home.xml').getroot()
for node in root.iter('node'):
    if node.attrib.get('text','').strip().lower() == 'you':
        m=re.fullmatch(r'\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]',node.attrib.get('bounds',''))
        if m:
            print((int(m.group(2))+int(m.group(4)))//2)
            break
else:
    print('')
PY
)
if [ -z "$PROFILE_Y" ]; then
  log "FAIL_CLASS=PROFILE_TAB_BOUNDS_MISSING"
  log "FAIL: could not determine bottom-navigation vertical position from home.xml"
  exit 1
fi
log "Opening You profile tab at ($PROFILE_X, $PROFILE_Y) on $SCREEN_WIDTH px emulator"
"${ADB[@]}" shell input tap "$PROFILE_X" "$PROFILE_Y"
sleep 3
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/profile.xml
"${ADB[@]}" pull /data/local/tmp/profile.xml profile.xml
if ! grep -Eqi 'Your profile|Edit student details' profile.xml; then
  log "FAIL_CLASS=PROFILE_NAVIGATION"
  log "FAIL: tapping the You tab did not open the profile screen"
  exit 1
fi
python3 .github/scripts/ui_smoke.py tap profile.xml "Edit student details"
sleep 2
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/setup.xml
"${ADB[@]}" pull /data/local/tmp/setup.xml setup.xml
python3 .github/scripts/ui_smoke.py tap setup.xml "Tamil Nadu State Board"
sleep 1
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/board-menu.xml
"${ADB[@]}" pull /data/local/tmp/board-menu.xml board-menu.xml
python3 .github/scripts/ui_smoke.py tap board-menu.xml "CBSE"
sleep 1
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/setup-cbse.xml
"${ADB[@]}" pull /data/local/tmp/setup-cbse.xml setup-cbse.xml
python3 .github/scripts/ui_smoke.py tap setup-cbse.xml "Save my details"
sleep 2
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/profile-cbse.xml
"${ADB[@]}" pull /data/local/tmp/profile-cbse.xml profile-cbse.xml
python3 .github/scripts/ui_smoke.py assert-profile profile-cbse.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap profile-cbse.xml "Home"
sleep 2
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-cbse.xml
"${ADB[@]}" pull /data/local/tmp/home-cbse.xml home-cbse.xml
python3 .github/scripts/ui_smoke.py assert-home home-cbse.xml | tee -a "$REPORT"

log "Opening tutor using accessibility bounds"
python3 .github/scripts/ui_smoke.py tap home-cbse.xml "Begin lesson"
sleep 8
"${ADB[@]}" exec-out screencap -p > ui-screenshots/tutor.png
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml || {
  sleep 3
  timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml
}
"${ADB[@]}" pull /data/local/tmp/tutor.xml tutor.xml
python3 .github/scripts/ui_smoke.py assert-tutor tutor.xml | tee -a "$REPORT"

log "Testing the I understand feedback action"
python3 .github/scripts/ui_smoke.py tap tutor.xml "I understand"
sleep 2
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/feedback.xml
"${ADB[@]}" pull /data/local/tmp/feedback.xml feedback.xml
"${ADB[@]}" exec-out screencap -p > ui-screenshots/feedback.png
python3 .github/scripts/ui_smoke.py assert-feedback feedback.xml | tee -a "$REPORT"

log "Testing tutor settings and voice controls"
python3 .github/scripts/ui_smoke.py tap feedback.xml "Change"
sleep 2
"${ADB[@]}" exec-out screencap -p > ui-screenshots/settings.png
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/settings.xml
"${ADB[@]}" pull /data/local/tmp/settings.xml settings.xml
python3 .github/scripts/ui_smoke.py assert-settings settings.xml | tee -a "$REPORT"

log "Loading the real Mathematics chapter list"
python3 .github/scripts/ui_smoke.py tap settings.xml "Mathematics"
sleep 10
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-options.xml
"${ADB[@]}" pull /data/local/tmp/chapter-options.xml chapter-options.xml
python3 .github/scripts/ui_smoke.py assert-chapter-button chapter-options.xml | tee -a "$REPORT"
# Wait for asynchronous API fetches and fail with the visible UI state, not a
# generic empty-list assertion. Network and app diagnostics are captured on exit.
python3 .github/scripts/ui_smoke.py tap chapter-options.xml "Choose chapter"
sleep 2
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-menu.xml
"${ADB[@]}" pull /data/local/tmp/chapter-menu.xml chapter-menu.xml
python3 .github/scripts/ui_smoke.py assert-chapter-one chapter-menu.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap-numbered chapter-menu.xml 1
sleep 3
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-selected.xml
"${ADB[@]}" pull /data/local/tmp/chapter-selected.xml chapter-selected.xml
python3 .github/scripts/ui_smoke.py assert-selected-chapter chapter-selected.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap chapter-selected.xml "Choose concept"
sleep 2
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-menu.xml
"${ADB[@]}" pull /data/local/tmp/concept-menu.xml concept-menu.xml
python3 .github/scripts/ui_smoke.py tap-first-concept concept-menu.xml
sleep 2
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-selected.xml
"${ADB[@]}" pull /data/local/tmp/concept-selected.xml concept-selected.xml
python3 .github/scripts/ui_smoke.py tap concept-selected.xml "Done"
sleep 3
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/ready-to-teach.xml
"${ADB[@]}" pull /data/local/tmp/ready-to-teach.xml ready-to-teach.xml
python3 .github/scripts/ui_smoke.py tap ready-to-teach.xml "Teach"

log "Recording live lesson frames to verify inline spoken-word highlighting"
"${ADB[@]}" shell rm -rf /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell mkdir -p /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell 'i=0; while [ "$i" -lt 35 ]; do screencap -p "/data/local/tmp/padippupal-live-frames/frame-$i.png"; i=$((i+1)); sleep 1; done'
"${ADB[@]}" pull /data/local/tmp/padippupal-live-frames ui-screenshots/live-frames
"${ADB[@]}" exec-out screencap -p > ui-screenshots/live-lesson.png
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-lesson.xml
"${ADB[@]}" pull /data/local/tmp/live-lesson.xml live-lesson.xml
python3 .github/scripts/ui_smoke.py assert-live live-lesson.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py assert-highlight-frames live-lesson.xml ui-screenshots/live-frames | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap live-lesson.xml "Stop"
sleep 2

log "Testing Android back navigation to Home"
"${ADB[@]}" shell input keyevent 4
sleep 5
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home-return.png
timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml || {
  sleep 3
  timeout -k 3s 25s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml
}
"${ADB[@]}" pull /data/local/tmp/home-return.xml home-return.xml
python3 .github/scripts/ui_smoke.py assert-home home-return.xml | tee -a "$REPORT"
log "PASS: app launch, home UI, tutor navigation, tutor UI, and back navigation"
