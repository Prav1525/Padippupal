#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p ui-screenshots
REPORT="ui-screenshots/test-report.txt"
: > "$REPORT"
FAILURE_CLASS="ENVIRONMENT_FAILURE"
ADB=(adb -s emulator-5554)
log() { printf '%s\n' "$*" | tee -a "$REPORT"; }
capture_diagnostics() {
  rc=$?
  if command -v adb >/dev/null 2>&1; then
    adb -s emulator-5554 logcat -d > ui-screenshots/logcat.txt 2>&1 || true
    adb -s emulator-5554 shell dumpsys activity activities > ui-screenshots/activities.txt 2>&1 || true
    adb -s emulator-5554 shell dumpsys window > ui-screenshots/windows.txt 2>&1 || true
  fi
  if [ "$rc" -ne 0 ]; then log "RESULT: $FAILURE_CLASS (exit $rc)"; else log "RESULT: PASS"; fi
  exit "$rc"
}
trap capture_diagnostics EXIT

adb devices -l | tee ui-screenshots/adb-devices.txt

# Emulator boot_completed can become 1 while Android's package/activity services
# are still restarting. Do not race PackageManager with APK installation.
log "Waiting for Android framework and PackageManager readiness (max 180s; every ADB/UI operation is bounded)"
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
  FAILURE_CLASS="ENVIRONMENT_FAILURE"
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

# The first-pass interactive chapter blueprints currently cover CBSE Class 6.
# The normal app default is Tamil Nadu State Board, which has no matching CBSE-only
# lesson records. Use an isolated CBSE profile so this test checks the supported
# Patterns in Mathematics lesson rather than silently testing the wrong curriculum.
# A profile-only reset is insufficient: Room/database state, saved lesson progress,
# and persisted UI state can survive attempt 1 and contaminate attempt 2. Clear all
# app user data before seeding the deterministic smoke profile on every attempt.
log "Resetting all app user data so this attempt starts from a clean install state"
clear_result=$("${ADB[@]}" shell pm clear com.padippupal.app 2>&1)
log "pm clear result: $clear_result"
if ! echo "$clear_result" | grep -q "Success"; then
  FAILURE_CLASS="ENVIRONMENT_FAILURE"
  log "FAIL: unable to clear app data; refusing to run a potentially contaminated smoke test"
  exit 1
fi
"${ADB[@]}" shell am force-stop com.padippupal.app
log "Configuring smoke-test profile: CBSE, Class 6, English"
${ADB[@]} shell "run-as com.padippupal.app sh -c 'mkdir -p shared_prefs && echo PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiIHN0YW5kYWxvbmU9InllcyIgPz48bWFwPjxzdHJpbmcgbmFtZT0iZ3JhZGUiPjY8L3N0cmluZz48c3RyaW5nIG5hbWU9ImJvYXJkIj5DQlNFPC9zdHJpbmc+PHN0cmluZyBuYW1lPSJtZWRpdW0iPkVuZ2xpc2g8L3N0cmluZz48c3RyaW5nIG5hbWU9Imxhbmd1YWdlIj5FbmdsaXNoPC9zdHJpbmc+PC9tYXA+ | base64 -d > shared_prefs/padippupal_profile.xml && test -s shared_prefs/padippupal_profile.xml'"
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
  FAILURE_CLASS="APP_FAILURE"
  log "FAIL: app process did not start within 60 seconds"
  exit 1
fi
sleep 15
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home.png
# UIAutomator can hang when Android accessibility/SystemUI is unhealthy. Bound
# each attempt so the test produces diagnostics instead of burning several minutes.
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml || {
  FAILURE_CLASS="ENVIRONMENT_FAILURE"
  log "First home accessibility dump failed; checking framework health before one retry"
  "${ADB[@]}" shell service check accessibility >> "$REPORT" 2>&1 || true
  "${ADB[@]}" shell dumpsys activity activities > ui-screenshots/activities-before-retry.txt 2>&1 || true
  sleep 2
  timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home.xml
}
"${ADB[@]}" pull /data/local/tmp/home.xml home.xml
python3 .github/scripts/ui_smoke.py assert-home home.xml | tee -a "$REPORT"
FAILURE_CLASS="APP_FAILURE"

log "Opening tutor using accessibility bounds"
python3 .github/scripts/ui_smoke.py tap home.xml "Begin lesson"
sleep 8
"${ADB[@]}" exec-out screencap -p > ui-screenshots/tutor.png
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml || {
  sleep 3
  timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/tutor.xml
}
"${ADB[@]}" pull /data/local/tmp/tutor.xml tutor.xml
python3 .github/scripts/ui_smoke.py assert-tutor tutor.xml | tee -a "$REPORT"

log "Testing the I understand feedback action"
python3 .github/scripts/ui_smoke.py tap tutor.xml "I understand"
sleep 2
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/feedback.xml
"${ADB[@]}" pull /data/local/tmp/feedback.xml feedback.xml
"${ADB[@]}" exec-out screencap -p > ui-screenshots/feedback.png
python3 .github/scripts/ui_smoke.py assert-feedback feedback.xml | tee -a "$REPORT"

log "Testing tutor settings and voice controls"
python3 .github/scripts/ui_smoke.py tap feedback.xml "Change"
sleep 2
"${ADB[@]}" exec-out screencap -p > ui-screenshots/settings.png
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/settings.xml
"${ADB[@]}" pull /data/local/tmp/settings.xml settings.xml
python3 .github/scripts/ui_smoke.py assert-settings settings.xml | tee -a "$REPORT"

log "Loading the real Mathematics chapter list"
python3 .github/scripts/ui_smoke.py tap settings.xml "Mathematics"
sleep 10
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-options.xml
"${ADB[@]}" pull /data/local/tmp/chapter-options.xml chapter-options.xml
python3 .github/scripts/ui_smoke.py assert-chapter-button chapter-options.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap chapter-options.xml "Choose chapter"
sleep 2
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-menu.xml
"${ADB[@]}" pull /data/local/tmp/chapter-menu.xml chapter-menu.xml
python3 .github/scripts/ui_smoke.py tap-numbered chapter-menu.xml 1
sleep 3
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/chapter-selected.xml
"${ADB[@]}" pull /data/local/tmp/chapter-selected.xml chapter-selected.xml
python3 .github/scripts/ui_smoke.py assert-chapter-selected chapter-selected.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap chapter-selected.xml "Choose concept"
sleep 2
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-menu.xml
"${ADB[@]}" pull /data/local/tmp/concept-menu.xml concept-menu.xml
python3 .github/scripts/ui_smoke.py tap-first-concept concept-menu.xml
sleep 2
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/concept-selected.xml
"${ADB[@]}" pull /data/local/tmp/concept-selected.xml concept-selected.xml
python3 .github/scripts/ui_smoke.py tap concept-selected.xml "Done"
sleep 3
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/ready-to-teach.xml
"${ADB[@]}" pull /data/local/tmp/ready-to-teach.xml ready-to-teach.xml
python3 .github/scripts/ui_smoke.py tap ready-to-teach.xml "Teach"

log "Waiting up to 90 seconds for confirmed playback (lesson-plan request can take 50s and hosted voice fallback 15s)"
pause_ready=false
for attempt in $(seq 1 45); do
  timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-pause-control.xml >/dev/null 2>&1 || true
  "${ADB[@]}" pull /data/local/tmp/live-pause-control.xml ui-screenshots/live-pause-control.xml >/dev/null 2>&1 || true
  if [ -f ui-screenshots/live-pause-control.xml ] && python3 .github/scripts/ui_smoke.py has-pause-control ui-screenshots/live-pause-control.xml >/dev/null 2>&1; then
    pause_ready=true
    break
  fi
  sleep 2
done
if [ "$pause_ready" != true ]; then
  echo "FAIL: live audio never exposed a usable Pause/Resume control" | tee -a "$REPORT"
  exit 1
fi
python3 .github/scripts/ui_smoke.py assert-pause-control ui-screenshots/live-pause-control.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap ui-screenshots/live-pause-control.xml "Pause"
sleep 2
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-paused.xml
"${ADB[@]}" pull /data/local/tmp/live-paused.xml ui-screenshots/live-paused.xml
python3 .github/scripts/ui_smoke.py assert-paused ui-screenshots/live-paused.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap ui-screenshots/live-paused.xml "Resume"
resume_ready=false
for attempt in $(seq 1 15); do
  sleep 1
  timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-resumed.xml >/dev/null 2>&1 || true
  "${ADB[@]}" pull /data/local/tmp/live-resumed.xml ui-screenshots/live-resumed.xml >/dev/null 2>&1 || true
  if [ -f ui-screenshots/live-resumed.xml ] && python3 .github/scripts/ui_smoke.py assert-resumed ui-screenshots/live-resumed.xml >/dev/null 2>&1; then
    resume_ready=true
    break
  fi
done
if [ "$resume_ready" != true ]; then
  echo "FAIL: Resume did not return to confirmed speaking state" | tee -a "$REPORT"
  exit 1
fi
python3 .github/scripts/ui_smoke.py assert-resumed ui-screenshots/live-resumed.xml | tee -a "$REPORT"

log "Recording live lesson frames to verify inline spoken-word highlighting"
"${ADB[@]}" shell rm -rf /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell mkdir -p /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell 'i=0; while [ "$i" -lt 35 ]; do screencap -p "/data/local/tmp/padippupal-live-frames/frame-$i.png"; i=$((i+1)); sleep 1; done'
"${ADB[@]}" pull /data/local/tmp/padippupal-live-frames ui-screenshots/live-frames
"${ADB[@]}" exec-out screencap -p > ui-screenshots/live-lesson.png
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-lesson.xml
"${ADB[@]}" pull /data/local/tmp/live-lesson.xml live-lesson.xml
python3 .github/scripts/ui_smoke.py assert-live live-lesson.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py assert-highlight-frames live-lesson.xml ui-screenshots/live-frames | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap live-lesson.xml "Stop"
sleep 2

log "Testing Android back navigation to Home"
"${ADB[@]}" shell input keyevent 4
sleep 5
"${ADB[@]}" exec-out screencap -p > ui-screenshots/home-return.png
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml || {
  sleep 3
  timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/home-return.xml
}
"${ADB[@]}" pull /data/local/tmp/home-return.xml home-return.xml
python3 .github/scripts/ui_smoke.py assert-home home-return.xml | tee -a "$REPORT"
log "PASS: app launch, home UI, tutor navigation, tutor UI, and back navigation"
