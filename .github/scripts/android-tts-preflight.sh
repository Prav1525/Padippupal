#!/usr/bin/env bash
# Install a reproducible offline TTS engine into the Android emulator.
# Read the APK name and SHA-256 from F-Droid's repository index over HTTPS
# rather than trusting a floating download URL or an unverified APK mirror.
set -euo pipefail

readonly PACKAGE="com.reecedunn.espeak"
readonly INDEX_URL="https://f-droid.org/repo/index-v1.jar"
readonly WORK_DIR="${RUNNER_TEMP:-/tmp}/padippupal-tts"
mkdir -p "$WORK_DIR"

curl --fail --location --silent --show-error --retry 3 "$INDEX_URL" -o "$WORK_DIR/index-v1.jar"
unzip -p "$WORK_DIR/index-v1.jar" index-v1.json > "$WORK_DIR/index-v1.json"

readarray -t apk_meta < <(python3 - "$WORK_DIR/index-v1.json" "$PACKAGE" <<'PY'
import json, sys
index_path, package_name = sys.argv[1:]
with open(index_path, encoding="utf-8") as f:
    index = json.load(f)
versions = index.get("packages", {}).get(package_name, [])
# Select the newest published compatible APK from F-Droid's repository index.
versions = sorted(versions, key=lambda item: int(item.get("versionCode", 0)), reverse=True)
if not versions:
    raise SystemExit(f"No F-Droid APK metadata found for {package_name}")
apk = versions[0]
name = apk.get("apkName")
digest = apk.get("hash")
if not name or not digest or apk.get("hashType", "sha256").lower() != "sha256":
    raise SystemExit("F-Droid index entry lacks a usable SHA-256 APK checksum")
print(name)
print(digest)
PY
)
apk_name="${apk_meta[0]}"
expected_sha256="${apk_meta[1]}"
curl --fail --location --silent --show-error --retry 3 "https://f-droid.org/repo/$apk_name" -o "$WORK_DIR/tts.apk"
printf '%s  %s\n' "$expected_sha256" "$WORK_DIR/tts.apk" | sha256sum --check --status
echo "Verified F-Droid TTS APK checksum: $expected_sha256 ($apk_name)"

adb -s emulator-5554 install --no-streaming "$WORK_DIR/tts.apk"
services="$(adb -s emulator-5554 shell cmd package query-services -a android.intent.action.TTS_SERVICE)"
printf '%s\n' "$services"
if ! printf '%s\n' "$services" | grep -Fq "$PACKAGE"; then
  echo "::error::Verified eSpeak APK installed but Android does not expose its TTS service."
  adb -s emulator-5554 shell dumpsys package "$PACKAGE" || true
  exit 1
fi
adb -s emulator-5554 shell settings put secure tts_default_synth "$PACKAGE"
selected="$(adb -s emulator-5554 shell settings get secure tts_default_synth | tr -d '\r')"
if [ "$selected" != "$PACKAGE" ]; then
  echo "::error::Could not select the installed offline TTS engine (selected=$selected)."
  exit 1
fi
echo "Offline TTS engine ready: $selected"
