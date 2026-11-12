#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/android_activity_package.sh"
expected="com.google.android.apps.nexuslauncher"

[[ "$(resolve_activity_package "$expected/.NexusLauncherActivity")" == "$expected" ]]
[[ "$(resolve_activity_package "ResolveInfo{$expected/.NexusLauncherActivity}")" == "$expected" ]]

if resolve_activity_package "No activity found" >/dev/null 2>&1; then
  echo "FAIL: invalid activity output was accepted" >&2
  exit 1
fi

echo "PASS: flattened and braced HOME components resolve safely; invalid output is rejected."
