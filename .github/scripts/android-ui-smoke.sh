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
log "Resetting smoke-test profile and saved tutor session so every retry starts from a deterministic clean state"
"${ADB[@]}" shell "run-as com.padippupal.app rm -f shared_prefs/padippupal_profile.xml"
# TutorScreen restores the selected subject/chapter/topic from a separate
# same-day session file. Clearing only the profile leaves stale selections
# behind, so later steps incorrectly expect the empty-state picker labels.
"${ADB[@]}" shell "run-as com.padippupal.app rm -f shared_prefs/padippupal_tutor_sessions.xml"
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

log "Testing tutor settings and voice controls"
python3 .github/scripts/ui_smoke.py tap tutor.xml "Change"
sleep 2
"${ADB[@]}" exec-out screencap -p > ui-screenshots/settings.png
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/settings.xml
"${ADB[@]}" pull /data/local/tmp/settings.xml settings.xml
python3 .github/scripts/ui_smoke.py assert-settings settings.xml | tee -a "$REPORT"
log "Scrolling lesson setup to verify lower voice preferences while Done stays fixed"
"${ADB[@]}" shell input swipe 540 1450 540 650 450
sleep 1
"${ADB[@]}" exec-out screencap -p > ui-screenshots/settings-scrolled.png
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/settings-scrolled.xml
"${ADB[@]}" pull /data/local/tmp/settings-scrolled.xml settings-scrolled.xml
python3 .github/scripts/ui_smoke.py assert-voice-settings settings-scrolled.xml | tee -a "$REPORT"
# Return to the top so the subject picker is visible for the next step.
"${ADB[@]}" shell input swipe 540 650 540 1450 450
sleep 1
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/settings-top.xml
"${ADB[@]}" pull /data/local/tmp/settings-top.xml settings-top.xml

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
python3 .github/scripts/ui_smoke.py tap-topic-picker chapter-selected.xml
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
python3 .github/scripts/ui_smoke.py tap-exact ready-to-teach.xml "▶ Teach"

# Start frame capture immediately after Teach, not after the polling loop. The
# lesson may already reach its checkpoint by the time UIAutomator observes it;
# starting capture only then produces 35 identical checkpoint frames and falsely
# reports that word highlighting never rendered. Capture across preparation and
# playback so frames include the moving active word.
log "Starting early live-lesson frame capture for playback/highlight evidence"
"${ADB[@]}" shell rm -rf /data/local/tmp/padippupal-live-frames
"${ADB[@]}" shell mkdir -p /data/local/tmp/padippupal-live-frames
("${ADB[@]}" shell 'i=0; while [ "$i" -lt 100 ]; do screencap -p "/data/local/tmp/padippupal-live-frames/frame-$i.png"; i=$((i+1)); sleep 1; done' > ui-screenshots/frame-capture.log 2>&1) &
FRAME_CAPTURE_PID=$!

log "Waiting for the lesson-plan API to return a real segment (up to 150s)"
lesson_started=0
for attempt in $(seq 1 50); do
  timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-lesson.xml >/dev/null 2>&1 || true
  "${ADB[@]}" pull /data/local/tmp/live-lesson.xml live-lesson.xml >/dev/null 2>&1 || true
  if [ -s live-lesson.xml ]; then
    if grep -Eqi "Live lesson · segment|segment [0-9]+ of [0-9]+|[0-9]+[[:space:]]*/[[:space:]]*5|Quick check|check your understanding|does that make sense so far" live-lesson.xml; then
      lesson_started=1
      break
    fi
    if grep -Eqi "could not answer right now|No matching textbook passage|not configured on the backend|connection failed|invalid response|no safe textbook fallback" live-lesson.xml; then
      FAILURE_CLASS="APP_FAILURE"
      log "FAIL: tutor API returned an explicit lesson-start error"
      cat live-lesson.xml | tee -a "$REPORT"
      exit 1
    fi
  fi
  sleep 3
done
if [ "$lesson_started" -ne 1 ]; then
  FAILURE_CLASS="APP_FAILURE"
  log "FAIL: tutor did not leave lesson preparation within 150 seconds"
  [ ! -s live-lesson.xml ] || cat live-lesson.xml | tee -a "$REPORT"
  exit 1
fi
log "Lesson UI detected; allowing early frame capture to finish so playback frames are included"
wait "$FRAME_CAPTURE_PID"
"${ADB[@]}" pull /data/local/tmp/padippupal-live-frames ui-screenshots/live-frames
"${ADB[@]}" exec-out screencap -p > ui-screenshots/live-lesson.png
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-lesson.xml
"${ADB[@]}" pull /data/local/tmp/live-lesson.xml live-lesson.xml
python3 .github/scripts/ui_smoke.py assert-live live-lesson.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py assert-live-layout ui-screenshots/live-lesson.png | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py assert-highlight-frames live-lesson.xml ui-screenshots/live-frames | tee -a "$REPORT"

log "Testing live playback pause and resume"
python3 .github/scripts/ui_smoke.py tap live-lesson.xml "Pause"
sleep 1
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-paused.xml
"${ADB[@]}" pull /data/local/tmp/live-paused.xml live-paused.xml
python3 .github/scripts/ui_smoke.py assert-playback-state live-paused.xml paused | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap live-paused.xml "Resume"
sleep 2
timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-resumed.xml
"${ADB[@]}" pull /data/local/tmp/live-resumed.xml live-resumed.xml
python3 .github/scripts/ui_smoke.py assert-playback-state live-resumed.xml playing | tee -a "$REPORT"

log "Waiting for the lesson to reach its explicit understanding checkpoint (up to 150s; speech duration varies by voice engine)"
checkpoint_seen=0
for attempt in $(seq 1 50); do
  timeout 20s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-checkpoint.xml >/dev/null 2>&1 || true
  "${ADB[@]}" pull /data/local/tmp/live-checkpoint.xml live-checkpoint.xml >/dev/null 2>&1 || true
  if [ -s live-checkpoint.xml ] && grep -Eqi "No compatible English voice|This selected voice engine has no Tamil voice|Voice playback failed|Voice engine could not initialize|speech engine did not finish starting" live-checkpoint.xml; then
    FAILURE_CLASS="APP_FAILURE"
    log "FAIL: speech could not start, so checkpoint progression cannot be tested; captured the explicit voice error instead of waiting for the full timeout"
    cat live-checkpoint.xml | tee -a "$REPORT"
    exit 1
  fi
  if [ -s live-checkpoint.xml ] && grep -Eqi "Quick check|check your understanding|does that make sense so far" live-checkpoint.xml; then
    checkpoint_seen=1
    break
  fi
  sleep 3
done
if [ "$checkpoint_seen" -ne 1 ]; then
  FAILURE_CLASS="APP_FAILURE"
  log "FAIL: live lesson did not reach the understanding checkpoint within 150 seconds after resume"
  exit 1
fi
"${ADB[@]}" exec-out screencap -p > ui-screenshots/live-checkpoint.png
python3 .github/scripts/ui_smoke.py assert-checkpoint live-checkpoint.xml ui-screenshots/live-checkpoint.png | tee -a "$REPORT"
log "Testing checkpoint continuation and next-segment progression"
python3 .github/scripts/ui_smoke.py tap live-checkpoint.xml "I understand"
continued=0
# The curriculum API can return four or five segments. The next segment may
# finish quickly and reach its own checkpoint before UIAutomator captures a frame,
# so assert real forward progress from the checkpoint we tapped rather than a
# hard-coded 2/5 -> 3/5 transient screen.
checkpoint_counter=$(grep -oE '[0-9]+[[:space:]]*/[[:space:]]*[0-9]+' live-checkpoint.xml | head -n1 | tr -d ' ')
checkpoint_caption=$(python3 -c 'import sys,xml.etree.ElementTree as E; r=E.parse(sys.argv[1]).getroot(); print(" ".join(n.attrib.get("text","") for n in r.iter() if n.attrib.get("text")))' live-checkpoint.xml)
for attempt in $(seq 1 120); do
  sleep 0.25
  timeout 8s "${ADB[@]}" shell uiautomator dump /data/local/tmp/live-continued.xml >/dev/null 2>&1 || true
  "${ADB[@]}" pull /data/local/tmp/live-continued.xml live-continued.xml >/dev/null 2>&1 || true
  if [ -s live-continued.xml ]; then
    current_counter=$(grep -oE '[0-9]+[[:space:]]*/[[:space:]]*[0-9]+' live-continued.xml | head -n1 | tr -d ' ')
    current_caption=$(python3 -c 'import sys,xml.etree.ElementTree as E; r=E.parse(sys.argv[1]).getroot(); print(" ".join(n.attrib.get("text","") for n in r.iter() if n.attrib.get("text")))' live-continued.xml)
    if [ -n "$current_counter" ] && [ "$current_counter" != "$checkpoint_counter" ] && [ "$current_caption" != "$checkpoint_caption" ]; then
      continued=1
      break
    fi
  fi
done
if [ "$continued" -ne 1 ]; then
  FAILURE_CLASS="APP_FAILURE"
  log "FAIL: understanding response did not advance to a different lesson segment/checkpoint within 30 seconds"
  [ -s live-continued.xml ] && cat live-continued.xml | tee -a "$REPORT"
  exit 1
fi
python3 .github/scripts/ui_smoke.py assert-continued live-continued.xml | tee -a "$REPORT"
python3 .github/scripts/ui_smoke.py tap live-continued.xml "Stop"
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
