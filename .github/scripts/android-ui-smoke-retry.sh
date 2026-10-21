#!/usr/bin/env bash
# Run the full emulator UI smoke flow at most twice, preserving evidence per attempt.
set -uo pipefail

mkdir -p attempt-artifacts
result=1
for attempt in 1 2; do
  echo "===== UI smoke attempt $attempt/2 ====="
  # Never let a retry consume XML/screenshots left by the previous attempt.
  rm -rf ui-screenshots
  rm -f home.xml tutor.xml home-return.xml feedback.xml settings.xml chapter-options.xml chapter-menu.xml chapter-selected.xml concept-menu.xml concept-selected.xml ready-to-teach.xml live-lesson.xml
  set +e
  bash .github/scripts/android-ui-smoke.sh
  result=$?
  set -e

  evidence="attempt-artifacts/attempt-$attempt"
  mkdir -p "$evidence"
  if [ -d ui-screenshots ]; then
    cp -a ui-screenshots "$evidence/" || true
  fi
  for file in home.xml tutor.xml home-return.xml feedback.xml settings.xml chapter-options.xml chapter-menu.xml chapter-selected.xml concept-menu.xml concept-selected.xml ready-to-teach.xml live-lesson.xml; do
    if [ -f "$file" ]; then cp "$file" "$evidence/"; fi
  done
  printf '%s\n' "$result" > "$evidence/exit-code.txt"
  echo "Attempt $attempt exit code: $result"

  if [ "$result" -eq 0 ]; then
    echo "UI smoke test passed on attempt $attempt"
    exit 0
  fi
  # A retry must not turn a reproducible product failure into a green workflow.
  # Retry only failures explicitly classified as emulator/ADB/test-environment issues.
  if grep -q "RESULT: APP_FAILURE" ui-screenshots/test-report.txt 2>/dev/null; then
    echo "Application/UI failure detected. Evidence preserved; refusing to mask it with a retry."
    exit "$result"
  fi
  if [ "$attempt" -lt 2 ]; then
    echo "Environment/harness failure; evidence preserved. Retrying once in the same booted emulator."
    adb -s emulator-5554 shell am force-stop com.padippupal.app || true
    sleep 5
  fi
done

echo "UI smoke test failed on both attempts. See attempt-artifacts for each attempt's evidence."
exit "$result"
