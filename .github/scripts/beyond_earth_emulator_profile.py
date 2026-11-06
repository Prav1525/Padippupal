#!/usr/bin/env python3
"""Safe profile-preference seeding for the Beyond Earth Android emulator test."""
from __future__ import annotations

PROFILE_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes" ?><map><string name="grade">6</string><string name="board">CBSE</string><string name="medium">English</string><string name="language">English</string></map>"""
PACKAGE = "com.padippupal.app"


def seed_profile_preferences(adb: list[str], run) -> None:
    """Create and stream profile data without adb shell argv re-tokenization."""
    run(adb + ["shell", "run-as", PACKAGE, "mkdir", "-p", "shared_prefs"], timeout=30)
    remote_command = f"run-as {PACKAGE} sh -c 'cat > shared_prefs/padippupal_profile.xml'"
    run(adb + ["shell", remote_command], timeout=30, input=PROFILE_XML, text=True)
