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
if ! timeout 12m sdkmanager --install "platform-tools" "platforms;android-35" "build-tools;37.0.0" "emulator" "system-images;android-35;default;x86_64" > "$EVIDENCE/sdkmanager-install.log" 2>&1; then
  cat "$EVIDENCE/sdkmanager-install.log"
  echo "::error::Android SDK component installation failed or timed out"
  exit 1
fi

echo "Creating Pixel 2 API 35 AOSP AVD (software-emulated CI runner; visual acceptance does not require Google Play or device TTS)"
echo no | avdmanager create avd --force -n beyond-earth-ci --package "system-images;android-35;default;x86_64" --device "pixel_2"
printf 'hw.cpu.ncore=2\nhw.ramSize=3072\nhw.lcd.width=720\nhw.lcd.height=1280\nhw.lcd.density=320\n' >> "$ANDROID_AVD_HOME/beyond-earth-ci.avd/config.ini"

adb_server_restart_attempted=0
adb_device_state() {
  timeout 8s "$ADB" devices -l 2>/dev/null | awk '$1 == "emulator-5554" { print $2; exit }'
}
recover_offline_transport() {
  echo "ADB reports emulator-5554 offline; requesting a bounded transport reconnect"
  timeout 8s "$ADB" reconnect offline >/dev/null 2>&1 || true
  sleep 3
  local state
  state="$(adb_device_state)"
  if [[ "$state" != "device" && "$adb_server_restart_attempted" -eq 0 ]]; then
    echo "ADB transport did not recover; restarting the host ADB server once"
    "$ADB" kill-server >/dev/null 2>&1 || true
    "$ADB" start-server
    adb_server_restart_attempted=1
  fi
}
wait_for_adb_device() {
  local wait_seconds="${1:-120}"
  local deadline=$((SECONDS + wait_seconds))
  local state=""
  while (( SECONDS < deadline )); do
    state="$(adb_device_state)"
    if [[ "$state" == "device" ]]; then return 0; fi
    if [[ "$state" == "offline" ]]; then recover_offline_transport; fi
    sleep 2
  done
  return 1
}

"$ADB" start-server
"$EMULATOR" -port 5554 -avd beyond-earth-ci -no-window -no-audio -no-boot-anim -no-snapshot -no-snapshot-save -gpu swiftshader_indirect -memory 3072 -cores 2 -accel off > /tmp/emulator.log 2>&1 &
echo $! > /tmp/emulator.pid

echo "Waiting for emulator transport (including bounded offline-device recovery)"
if ! wait_for_adb_device 360; then
  collect_diagnostics "transport-timeout"
  echo "::error::Android emulator did not become online in ADB within six minutes"
  exit 1
fi

echo "Waiting for Android boot (transient ADB errors are retried)"
boot_ready=0
offline_since=0
for attempt in $(seq 1 180); do
  device_state="$(adb_device_state)"
  if [[ "$device_state" == "offline" ]]; then
    if (( offline_since == 0 )); then offline_since=$SECONDS; fi
    recover_offline_transport
    if (( SECONDS - offline_since >= 120 )); then
      collect_diagnostics "adb-offline-during-boot"
      echo "::error::ADB remained offline for two minutes during Android boot"
      exit 1
    fi
  elif [[ "$device_state" == "device" ]]; then
    offline_since=0
    boot_value=$("$ADB" -s emulator-5554 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
    if [ "$boot_value" = "1" ]; then
      boot_ready=1
      break
    fi
  fi
  sleep 2
done
if [ "$boot_ready" -ne 1 ]; then
  collect_diagnostics "boot-timeout"
  echo "::error::Android emulator did not finish booting within the bounded boot wait"
  exit 1
fi

echo "Emulator reported boot complete; confirming ADB transport is online"
if ! wait_for_adb_device 120; then
  collect_diagnostics "adb-offline-after-boot"
  echo "::error::Android boot completed but ADB transport did not recover"
  exit 1
fi

echo "Emulator booted; waiting up to 10 minutes for Android PackageManagerService"
package_manager_ready=0
package_manager_deadline=$((SECONDS + 600))
last_package_manager_notice=$SECONDS
offline_since=0
while (( SECONDS < package_manager_deadline )); do
  device_state="$(adb_device_state)"
  if [[ "$device_state" == "offline" ]]; then
    if (( offline_since == 0 )); then offline_since=$SECONDS; fi
    recover_offline_transport
    if (( SECONDS - offline_since >= 120 )); then
      collect_diagnostics "adb-offline-during-package-manager"
      echo "::error::ADB remained offline for two minutes while waiting for PackageManagerService"
      exit 1
    fi
  elif [[ "$device_state" == "device" ]]; then
    offline_since=0
    package_service_state=$(timeout 6s "$ADB" -s emulator-5554 shell service check package 2>&1 || true)
    if [[ "$package_service_state" == *"found"* ]]; then
      if timeout 15s "$ADB" -s emulator-5554 shell cmd package list packages > /tmp/beyond-earth-packages.txt 2>/dev/null \
        && grep -q "^package:" /tmp/beyond-earth-packages.txt; then
        package_manager_ready=1
        break
      fi
    fi
  fi
  if (( SECONDS - last_package_manager_notice >= 30 )); then
    echo "PackageManagerService is still initializing; continuing bounded wait"
    last_package_manager_notice=$SECONDS
  fi
  sleep 3
done
if [ "$package_manager_ready" -ne 1 ]; then
  collect_diagnostics "package-manager-timeout"
  echo "::error::Android PackageManagerService did not become ready within 10 minutes"
  exit 1
fi
"$ADB" -s emulator-5554 shell settings put global window_animation_scale 0
"$ADB" -s emulator-5554 shell settings put global transition_animation_scale 0
"$ADB" -s emulator-5554 shell settings put global animator_duration_scale 0

echo "Running Beyond Earth visual acceptance with deterministic fixture; device TTS is outside this test scope"
python3 .github/scripts/test_beyond_earth_emulator.py
