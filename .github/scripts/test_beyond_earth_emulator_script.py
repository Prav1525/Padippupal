#!/usr/bin/env python3
"""Regression checks for the Beyond Earth emulator setup command."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/beyond_earth_emulator_test.sh"
def require(ok: bool, message: str) -> None:
    if not ok: raise SystemExit("FAIL: " + message)
    print("PASS: " + message)
def main() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    line = next((x for x in source.splitlines() if "padippupal_profile.xml" in x and "base64 -d" in x), "")
    require(bool(line), "profile initialization command exists")
    require('shell "run-as com.padippupal.app sh -c \'mkdir -p shared_prefs' in line, "ADB receives the run-as script as one quoted remote command")
    require("&& test -s shared_prefs/padippupal_profile.xml" in line, "profile setup verifies the preferences file was written")
    require("shell run-as com.padippupal.app sh -c" not in line, "unquoted adb shell argument splitting regression is absent")
    print("PASS: Beyond Earth emulator setup regression checks completed")
if __name__ == "__main__": main()
