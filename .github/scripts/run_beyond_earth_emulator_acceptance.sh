#!/usr/bin/env bash
# Start and verify the Android emulator directly. The third-party runner's
# post-boot keyevent can fail on software-rendered hosted runners before the
# supplied test script is ever invoked.
set -Eeuo pipefail

export ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_AVD_HOME="${ANDROID_AVD_HOME:-$HOME/.android/avd}"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
readonly ADB="$ANDROID_HOME/platform-tools/adb"
readonly EMULATOR="$ANDROID_HOME/emulator/emulator"
readonly EVIDENCE="ui-screenshots/beyond-earth"
mkdir -p "$EVIDENCE" "$ANDROID_AVD_HOME"

collect_diagnostics() {
  local reason="${1:-failure}"
  local emulator_pid=""
  echo "Collecting emulator diagnostics ($reason)" >&2
  printf '%s\n' "$reason" > "$EVIDENCE/failure-reason.txt"
  timeout 8s "$ADB" devices -l > "$EVIDENCE/adb-devices.txt" 2>&1 || true
  if [ -s /tmp/emulator.pid ]; then emulator_pid="$(cat /tmp/emulator.pid)"; fi
  # Never wait on adb shell when emulator provisioning failed before launch.
  if [ -n "$emulator_pid" ] && kill -0 "$emulator_pid" 2>/dev/null; then
    timeout 12s "$ADB" -s emulator-5554 logcat -d -v threadtime > "$EVIDENCE/logcat.txt" 2>&1 || true
    timeout 12s "$ADB" -s emulator-5554 shell dumpsys activity activities > "$EVIDENCE/activity.txt" 2>&1 || true
    timeout 12s "$ADB" -s emulator-5554 shell dumpsys window windows > "$EVIDENCE/windows.txt" 2>&1 || true
  else
    printf '%s\n' "Emulator process was not running; adb shell diagnostics skipped." > "$EVIDENCE/adb-diagnostics-skipped.txt"
  fi
  cp /tmp/emulator.log "$EVIDENCE/emulator.log" 2>/dev/null || true
  cp /tmp/beyond-earth-fixture.log "$EVIDENCE/fixture.log" 2>/dev/null || true
}
cleanup() {
  local status=$?
  local emulator_pid=""
  if [ "$status" -ne 0 ]; then collect_diagnostics "exit-$status"; fi
  if [ -s /tmp/emulator.pid ]; then
    emulator_pid="$(cat /tmp/emulator.pid)"
    timeout 8s "$ADB" -s emulator-5554 emu kill >/dev/null 2>&1 || true
    kill "$emulator_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "Installing Android API 35 emulator components"
# With pipefail, yes receives SIGPIPE after sdkmanager accepts all licenses.
# Check sdkmanager's status specifically; the expected yes exit is harmless.
set +e
yes | sdkmanager --licenses > "$EVIDENCE/sdkmanager-licenses.log" 2>&1
license_status=${PIPESTATUS[1]}
set -e
if [ "$license_status" -ne 0 ]; then
  cat "$EVIDENCE/sdkmanager-licenses.log"
  echo "::error::sdkmanager --licenses failed with exit $license_status"
  exit "$license_status"
fi
if ! timeout 12m sdkmanager --install "platform-tools" "platforms;android-35" "build-tools;37.0.0" "emulator" "system-images;android-35;google_apis;x86_64" > "$EVIDENCE/sdkmanager-install.log" 2>&1; then
  cat "$EVIDENCE/sdkmanager-install.log"
  echo "::error::Android SDK component installation failed or timed out"
  exit 1
fi

echo "Creating Pixel 2 API 35 AVD"
echo no | avdmanager create avd --force -n beyond-earth-ci --package "system-images;android-35;google_apis;x86_64" --device "pixel_2"
printf 'hw.cpu.ncore=2\n' >> "$ANDROID_AVD_HOME/beyond-earth-ci.avd/config.ini"

"$ADB" start-server
"$EMULATOR" -port 5554 -avd beyond-earth-ci -no-window -no-audio -no-boot-anim -no-snapshot -no-snapshot-save -gpu swiftshader_indirect -memory 2048 -cores 2 -accel off > /tmp/emulator.log 2>&1 &
echo $! > /tmp/emulator.pid

echo "Waiting for emulator transport"
transport_ready=0
for attempt in $(seq 1 180); do
  if "$ADB" devices | grep -q '^emulator-5554[[:space:]]\+device$'; then
    transport_ready=1
    break
  fi
  sleep 2
done
if [ "$transport_ready" -ne 1 ]; then
  collect_diagnostics "transport-timeout"
  echo "::error::Android emulator did not register with ADB"
  exit 1
fi

echo "Waiting for Android boot (transient ADB errors are retried)"
boot_ready=0
for attempt in $(seq 1 180); do
  boot_value=""
  for retry in 1 2 3; do
    boot_value=$("$ADB" -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
    [ "$boot_value" = "1" ] && break
    sleep 2
  done
  if [ "$boot_value" = "1" ]; then
    boot_ready=1
    break
  fi
  sleep 2
done
if [ "$boot_ready" -ne 1 ]; then
  collect_diagnostics "boot-timeout"
  echo "::error::Android emulator did not finish booting within 12 minutes"
  exit 1
fi

echo "Emulator booted; verifying Android package manager"
package_manager_ready=0
for attempt in $(seq 1 30); do
  if timeout 8s "$ADB" -s emulator-5554 shell cmd package list packages >/dev/null 2>&1; then
    package_manager_ready=1
    break
  fi
  sleep 2
done
if [ "$package_manager_ready" -ne 1 ]; then
  collect_diagnostics "package-manager-timeout"
  echo "::error::Android package manager did not become ready"
  exit 1
fi
"$ADB" -s emulator-5554 shell settings put global window_animation_scale 0
"$ADB" -s emulator-5554 shell settings put global transition_animation_scale 0
"$ADB" -s emulator-5554 shell settings put global animator_duration_scale 0

echo "Running verified offline TTS preflight and Beyond Earth tutor acceptance"
bash .github/scripts/android-tts-preflight.sh
python3 .github/scripts/test_beyond_earth_emulator.py
