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

def assert_checkpoint(path):
    _, texts = load(path)
    joined = "\\n".join(texts).lower()
    print("CHECKPOINT TEXT:", " | ".join(texts[:120]))
    required = ("quick check", "i understand", "explain again", "i have a question")
    missing = [label for label in required if label not in joined]
    if missing:
        raise SystemExit("Live lesson did not pause at the complete understanding checkpoint: " + ", ".join(missing))
    print("PASS: lesson pauses at the understanding checkpoint with all response choices")

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
        raise SystemExit("Choose chapter control is disabled")
    if any("no chapter list is available" in text.lower() for text in texts):
        raise SystemExit("Chapter options are empty for the selected board/class/subject. This is a curriculum/API-data failure, not a successful load.")
    print("PASS: chapter picker is enabled and the UI does not report an empty chapter list")

def assert_chapter_selected(path):
    _, texts = load(path)
    joined = "\\n".join(texts).lower()
    print("SELECTED CHAPTER TEXT:", " | ".join(texts[:100]))
    if "patterns in mathematics" not in joined:
        raise SystemExit("Smoke test did not select Class 6 Mathematics Chapter 1: Patterns in Mathematics")
    print("PASS: selected the expected Mathematics Chapter 1")

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

def concept_candidates(nodes):
    """Return visible numbered topic rows; Compose may omit clickable/enabled flags."""
    numbered = []
    pattern = r"^\d+[.)]\s*\S"
    for node in nodes:
        label = node.attrib.get("text", "").strip()
        bounds = node.attrib.get("bounds", "")
        if not re.match(pattern, label):
            continue
        if not re.fullmatch(r"\[\d+,\d+\]\[\d+,\d+\]", bounds):
            continue
        if node.attrib.get("enabled") == "false":
            continue
        numbered.append(node)
    # Prefer explicit accessibility clickability, but do not require it:
    # Compose dialog rows can be tappable even when the XML node says clickable=false.
    return sorted(numbered, key=lambda n: n.attrib.get("clickable") != "true")


def tap_topic_picker(path):
    nodes, texts = load(path)
    # Chapter selection may preselect the first curriculum topic. In that case
    # the button displays its selected title instead of the placeholder label.
    candidates = []
    for node in nodes:
        label = node.attrib.get("text", "").strip()
        if label.lower() == "choose concept" or label.lower() == "all 1s":
            if re.fullmatch(r"\[\d+,\d+\]\[\d+,\d+\]", node.attrib.get("bounds", "")):
                candidates.append(node)
    if not candidates:
        raise SystemExit("No concept-picker control found (expected placeholder or currently selected topic). Visible labels: " + " | ".join(texts[:120]))
    node = next((n for n in candidates if n.attrib.get("clickable") == "true"), candidates[0])
    bounds = node.attrib["bounds"]
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    x1, y1, x2, y2 = map(int, match.groups())
    print("Opening concept picker:", node.attrib.get("text"), bounds)
    subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap", str((x1+x2)//2), str((y1+y2)//2)],
                   check=True, timeout=45)

def tap_first_concept(path):
    nodes, texts = load(path)
    candidates = concept_candidates(nodes)
    if not candidates:
        raise SystemExit("No visible numbered concept row with valid tap bounds. Visible labels: " + " | ".join(texts[:120]))
    node = candidates[0]
    bounds = node.attrib["bounds"]
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    x1, y1, x2, y2 = map(int, match.groups())
    if x2 <= x1 or y2 <= y1:
        raise SystemExit("Concept row has zero-area bounds: " + bounds)
    print("Selecting first visible concept row:", node.attrib.get("text"), bounds,
          "clickable=", node.attrib.get("clickable", "unspecified"),
          "enabled=", node.attrib.get("enabled", "unspecified"))
    subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap", str((x1+x2)//2), str((y1+y2)//2)],
                   check=True, timeout=45)

def assert_live(path):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    print("LIVE LESSON TEXT:", " | ".join(texts[:140]))
    if "teacher is speaking" not in joined and "quick check" not in joined:
        raise SystemExit("Live lesson did not reach the speaking/checkpoint UI")
    # The inline caption is ordinary Text now; verify lesson words, not the removed prompt.
    lesson_words = ("one", "all 1s", "pattern", "number")
    if not any(term in joined for term in lesson_words):
        raise SystemExit("Live lesson is active but no recognizable inline teaching caption text is accessible")
    if "tap any word to hear its pronunciation again." in joined:
        raise SystemExit("Removed pronunciation prompt has reappeared in the live lesson UI")
    visible_labels = {text.strip().lower() for text in texts}
    if visible_labels.intersection({"choose chapter", "choose concept", "subject", "change"}):
        raise SystemExit("Setup/selection controls are still taking space on the live teaching screen")
    if "pause" not in joined or "stop" not in joined:
        raise SystemExit("Live teaching header is missing Pause/Stop playback controls")
    if "ask your teacher" in joined or "send question" in joined:
        raise SystemExit("Chat composer is still visible during the dedicated live teaching experience")
    forbidden_activity_labels = ("interactive concept lab", "touch & explore", "drag the objects", "touch and hold an object", "reset to start again")
    found_activity = [label for label in forbidden_activity_labels if label in joined]
    if found_activity:
        raise SystemExit("Interactive activity UI reappeared in the teaching flow: " + ", ".join(found_activity))
    if "patterns in mathematics" in joined and "watch the pattern" not in joined:
        raise SystemExit("Class 6 Patterns in Mathematics live lesson is missing its passive auto-playing concept animation")
    if "all 1s" in joined:
        if "1, 1, 1, 1, 1" not in joined:
            raise SystemExit("All 1s topic is not showing the matching repeated-ones animation")
        if "square numbers grow" in joined or "1²" in joined or "+3" in joined:
            raise SystemExit("All 1s topic is incorrectly showing square-number content")
    print("PASS: live lesson has inline teaching text, no interactive activity, and concept-matched passive animation")

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
    centers = []
    for frame in frames:
        try:
            image = Image.open(frame).convert("RGB")
            pixels = image.load()
            coords = [(x, y) for y in range(image.height) for x in range(image.width) if pixels[x, y] == target]
            count = len(coords)
            if count > best_count:
                best_count, best_frame = count, str(frame)
            # The same lesson text must visibly move its highlight as speech progresses.
            if count >= 12:
                centers.append((sum(x for x, _ in coords) / count, sum(y for _, y in coords) / count))
        except Exception as exc:
            print("Skipping unreadable frame", frame, exc)
    distinct_centers = []
    for center in centers:
        if all(((center[0] - prior[0]) ** 2 + (center[1] - prior[1]) ** 2) ** 0.5 >= 18 for prior in distinct_centers):
            distinct_centers.append(center)
    print(f"Highlight pixel scan: {len(frames)} frames; max exact highlight pixels={best_count} in {best_frame}; distinct highlight positions={len(distinct_centers)}")
    if best_count < 12:
        raise SystemExit("No clear inline word-highlight background was detected in the captured live lesson frames")
    if len(distinct_centers) < 2:
        raise SystemExit("Inline highlight was found but did not move across at least two words during speech")
    print("PASS: inline spoken-word highlight is visible and moves across the lesson text")

def assert_playback_state(path, expected):
    _, texts = load(path)
    joined = "\\n".join(texts).lower()
    print("PLAYBACK STATE TEXT:", " | ".join(texts[:100]))
    required = ("stop", "resume") if expected == "paused" else ("stop", "pause")
    missing = [label for label in required if label not in joined]
    if missing:
        raise SystemExit(f"Live playback {expected} state is missing controls: " + ", ".join(missing))
    print(f"PASS: live playback {expected} state exposes the expected controls")


def assert_live_layout(path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to inspect live lesson layout") from exc
    image = Image.open(path).convert("RGB")
    width, height = image.size
    # The live teaching panel uses #EAF5EE. Check its central area near the
    # bottom of the teaching viewport, above the fixed message composer.
    x1, x2 = int(width * 0.15), int(width * 0.85)
    y1, y2 = int(height * 0.58), int(height * 0.70)
    count = 0
    for y in range(y1, y2):
        for x in range(x1, x2):
            if image.getpixel((x, y)) == (234, 245, 238):
                count += 1
    print(f"Live panel lower-viewport background pixels: {count}")
    if count < 500:
        raise SystemExit("Live teaching panel does not fill the available vertical space; a large unused blank area remains below the lesson")
    print("PASS: live teaching panel occupies the available teaching viewport")


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

def has_label(path, label):
    _, texts = load(path)
    found = any(label.lower() in text.lower() for text in texts)
    print(f"LABEL CHECK: {label!r} {'present' if found else 'not present'}")
    return found

def assert_topic_selected(path):
    _, texts = load(path)
    joined = "\\n".join(texts).lower()
    if "all 1s" not in joined and "patterns in mathematics" not in joined:
        raise SystemExit("No database-backed topic/chapter selection is visible: " + " | ".join(texts[:100]))
    print("PASS: a database-backed chapter/topic is already selected")

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
    elif action == "assert-checkpoint":
        assert_checkpoint(path)
    elif action == "assert-settings":
        assert_settings(path)
    elif action == "has-label" and len(sys.argv) >= 4:
        if not has_label(path, sys.argv[3]):
            raise SystemExit(1)
    elif action == "assert-topic-selected":
        assert_topic_selected(path)
    elif action == "assert-chapter-button":
        assert_chapter_button(path)
    elif action == "assert-chapter-selected":
        assert_chapter_selected(path)
    elif action == "tap-numbered" and len(sys.argv) >= 4:
        tap_numbered(path, sys.argv[3])
    elif action == "tap-topic-picker":
        tap_topic_picker(path)
    elif action == "tap-first-concept":
        tap_first_concept(path)
    elif action == "assert-live":
        assert_live(path)
    elif action == "assert-highlight-frames" and len(sys.argv) >= 4:
        assert_highlight_frames(sys.argv[3])
    elif action == "assert-live-layout":
        assert_live_layout(path)
    elif action == "assert-playback-state" and len(sys.argv) >= 4:
        assert_playback_state(path, sys.argv[3])
    elif action == "tap" and len(sys.argv) >= 4:
        tap(path, sys.argv[3])
    else:
        raise SystemExit("Unknown action or missing tap target: " + action)

if __name__ == "__main__":
    main()
