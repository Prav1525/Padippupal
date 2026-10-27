#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9]+$ ]]; then
  echo "Usage: $0 <diary-test-exit-code>" >&2
  exit 64
fi

diary_test_status="$1"
mkdir -p diary-artifacts
if [[ -d ui-screenshots/diary-test ]]; then
  cp -a ui-screenshots/diary-test diary-artifacts/
fi
printf '%s\n' "$diary_test_status" > diary-artifacts/exit-code.txt

if [[ "$diary_test_status" -ne 0 ]]; then
  echo "Diary emulator acceptance failed with exit code $diary_test_status; preserved diagnostics in diary-artifacts/" >&2
  exit "$diary_test_status"
fi
