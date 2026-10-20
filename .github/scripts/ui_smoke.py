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

def assert_chapter_button(path):
    nodes, texts = load(path)
    print("CHAPTER OPTIONS TEXT:", " | ".join(texts[:120]))
    node = next((n for n in nodes if "choose chapter" in n.attrib.get("text", "").lower()), None)
    if node is None:
        raise SystemExit("Choose chapter control was not found after selecting Mathematics")
    if node.attrib.get("enabled") != "true":
        raise SystemExit("Chapter list did not load or the Choose chapter control is disabled")
    print("PASS: Mathematics chapter list loaded and can be opened")

def tap_numbered(path, number):
    nodes, texts = load(path)
    candidates = []
    pattern = rf"^{re.escape(str(number))}[.)]\s*\S"
    for node in nodes:
        label = node.attrib.get("text", "").strip()
        if re.match(pattern, label):
            candidates.append(node)
    if not candidates:
        raise SystemExit(f"No numbered option {number} found. Visible labels: " + " | ".join(texts[:100]))
    node = next((n for n in candidates if n.attrib.get("clickable") == "true"), candidates[0])
    bounds = node.attrib.get("bounds", "")
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        raise SystemExit("First chapter option has invalid bounds: " + bounds)
    x1, y1, x2, y2 = map(int, match.groups())
    print("Selecting first chapter option:", node.attrib.get("text"), bounds)
    subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap", str((x1+x2)//2), str((y1+y2)//2)],
                   check=True, timeout=45)

def tap_first_concept(path):
    nodes, texts = load(path)
    candidates = []
    for node in nodes:
        label = node.attrib.get("text", "").strip()
        if not label or label.lower() in ("choose concept", "choose chapter", "done", "cancel"):
            continue
        if node.attrib.get("clickable") == "true" and node.attrib.get("enabled") == "true":
            candidates.append(node)
    if not candidates:
        raise SystemExit("No selectable concept was shown. Visible labels: " + " | ".join(texts[:120]))
    node = candidates[0]
    bounds = node.attrib.get("bounds", "")
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        raise SystemExit("First concept has invalid bounds: " + bounds)
    x1, y1, x2, y2 = map(int, match.groups())
    print("Selecting first real concept option:", node.attrib.get("text"), bounds)
    subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap", str((x1+x2)//2), str((y1+y2)//2)],
                   check=True, timeout=45)

def assert_live(path):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    print("LIVE LESSON TEXT:", " | ".join(texts[:140]))
    if "teacher is speaking" not in joined and "quick check" not in joined:
        raise SystemExit("Live lesson did not reach the speaking/checkpoint UI")
    if "tap any word to hear its pronunciation again." not in joined:
        raise SystemExit("Live lesson is active but the single inline teaching caption is missing")
    print("PASS: live lesson panel and spoken teaching text are visible")

def assert_highlight_frames(directory):
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to inspect word-highlight screenshots") from exc
    root = Path(directory)
    frames = sorted(root.glob("*.png"))
    if not frames:
        raise SystemExit("No live lesson frames were captured")
    target = (216, 232, 183)  # WordByWordCaption highlight: #D8E8B7
    best_count = 0
    best_frame = ""
    for frame in frames:
        try:
            image = Image.open(frame).convert("RGB")
            count = sum(1 for pixel in image.getdata() if pixel == target)
            if count > best_count:
                best_count, best_frame = count, str(frame)
        except Exception as exc:
            print("Skipping unreadable frame", frame, exc)
    print(f"Highlight pixel scan: {len(frames)} frames; max exact highlight pixels={best_count} in {best_frame}")
    if best_count < 12:
        raise SystemExit("No clear inline word-highlight background was detected in the captured live lesson frames")
    print("PASS: at least one emulator frame contains the inline spoken-word highlight")

def tap(path, target):
    nodes, texts = load(path)
    candidates = []
    for node in nodes:
        text = node.attrib.get("text", "").strip()
        if target.lower() in text.lower():
            candidates.append(node)
    if not candidates:
        raise SystemExit(f"Could not find target text {target!r}; visible labels: {' | '.join(texts[:100])}")
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
        raise SystemExit("Usage: ui_smoke.py {assert-home|assert-tutor|assert-feedback|assert-settings|assert-live|tap} XML [TARGET]")
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
    elif action == "assert-chapter-button":
        assert_chapter_button(path)
    elif action == "tap-numbered" and len(sys.argv) >= 4:
        tap_numbered(path, sys.argv[3])
    elif action == "tap-first-concept":
        tap_first_concept(path)
    elif action == "assert-live":
        assert_live(path)
    elif action == "assert-highlight-frames" and len(sys.argv) >= 4:
        assert_highlight_frames(sys.argv[3])
    elif action == "tap" and len(sys.argv) >= 4:
        tap(path, sys.argv[3])
    else:
        raise SystemExit("Unknown action or missing tap target: " + action)

if __name__ == "__main__":
    main()
