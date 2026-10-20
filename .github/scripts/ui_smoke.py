#!/usr/bin/env python3
"""Small accessibility-tree helpers for the PadippuPal Android emulator smoke test."""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def load(path):
    root = ET.parse(path).getroot()
    nodes = list(root.iter("node"))
    texts = [n.attrib.get("text", "").strip() for n in nodes]
    texts = [t for t in texts if t]
    return nodes, texts

def assert_home(path):
    _, texts = load(path)
    joined = "\n".join(texts)
    expected = ("YOUR LEARNING DESK", "A little wiser today", "YOUR PERSONAL TUTOR", "Begin lesson")
    missing = [term for term in expected if term.lower() not in joined.lower()]
    print("HOME TEXT:", " | ".join(texts[:80]))
    if missing:
        raise SystemExit("Home screen is missing expected accessible labels: " + ", ".join(missing))
    print("PASS: expected home-screen labels are accessible")

def assert_tutor(path):
    _, texts = load(path)
    joined = "\n".join(texts)
    print("TUTOR TEXT:", " | ".join(texts[:120]))
    if not texts:
        raise SystemExit("Tutor screen accessibility tree is empty")
    if "YOUR LEARNING DESK" in joined.upper():
        raise SystemExit("Tutor navigation did not leave the Home screen")
    expected_any = ("chapter", "math", "tutor", "lesson", "ask", "subject", "class", "english", "tamil", "topic")
    if not any(term in joined.lower() for term in expected_any):
        raise SystemExit("Tutor screen has no recognizable tutor/lesson/chapter labels")
    feedback = ("How did that explanation feel?", "I understand", "Explain again", "Ask")
    missing = [term for term in feedback if term.lower() not in joined.lower()]
    if missing:
        raise SystemExit("Tutor feedback controls are missing: " + ", ".join(missing))
    print("PASS: tutor screen and all three explanation-feedback controls are accessible")

def assert_feedback(path):
    _, texts = load(path)
    joined = "\n".join(texts)
    print("FEEDBACK TEXT:", " | ".join(texts[:100]))
    if "great!" not in joined.lower():
        raise SystemExit("Tapping I understand did not show supportive feedback")
    print("PASS: I understand action shows supportive feedback")

def assert_settings(path):
    nodes, texts = load(path)
    joined = "\n".join(texts + [n.attrib.get("content-desc", "") for n in nodes]).lower()
    print("SETTINGS TEXT:", " | ".join(texts[:140]))
    expected = ("Mathematics", "Choose chapter", "Choose concept", "Language", "English", "Tanglish", "Read replies aloud", "Prefer on-device voice")
    missing = [term for term in expected if term.lower() not in joined]
    if missing:
        raise SystemExit("Tutor settings are missing expected controls: " + ", ".join(missing))
    print("PASS: subject, chapter/topic, language, and voice settings are accessible")

def tap(path, target):
    nodes, texts = load(path)
    candidates = []
    for node in nodes:
        text = node.attrib.get("text", "").strip()
        if target.lower() in text.lower():
            candidates.append(node)
    if not candidates:
        raise SystemExit(f"Could not find target text {target!r}; visible labels: {' | '.join(texts[:100])}")
    # Prefer a clickable node, otherwise use the bounds of the text label itself.
    node = next((n for n in candidates if n.attrib.get("clickable") == "true"), candidates[0])
    bounds = node.attrib.get("bounds", "")
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        raise SystemExit(f"Target {target!r} has invalid accessibility bounds: {bounds!r}")
    x1, y1, x2, y2 = map(int, match.groups())
    x, y = (x1 + x2) // 2, (y1 + y2) // 2
    print(f"Tapping {target!r} at ({x}, {y}), bounds={bounds}, clickable={node.attrib.get('clickable')}")
    subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap", str(x), str(y)],
                   check=True, timeout=45)

def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: ui_smoke.py {assert-home|assert-tutor|tap} XML [TARGET]")
    action, path = sys.argv[1], sys.argv[2]
    if not Path(path).is_file():
        raise SystemExit("UI XML file does not exist: " + path)
    if action == "assert-home":
        assert_home(path)
    elif action == "assert-tutor":
        assert_tutor(path)
    elif action == "assert-feedback":
        assert_feedback(path)
    elif action == "assert-settings":
        assert_settings(path)
    elif action == "tap" and len(sys.argv) >= 4:
        tap(path, sys.argv[3])
    else:
        raise SystemExit("Unknown action or missing tap target: " + action)

if __name__ == "__main__":
    main()
