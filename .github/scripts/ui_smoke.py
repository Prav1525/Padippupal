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
    labels = {text.strip().lower() for text in texts}
    if "change" in labels:
        raise SystemExit("Tutor ready screen must not duplicate chapter/topic selection; use the previous screen")
    if not any(label.strip().lstrip("▶").strip().lower() == "teach" for label in labels):
        raise SystemExit("Tutor ready screen is missing the Teach action")
    if any("set up your lesson" in text.lower() for text in texts):
        raise SystemExit("Lesson setup must open only after the learner chooses Change")
    source_path = Path(__file__).resolve().parents[2] / "app/src/main/java/com/padippupal/app/TutorScreen.kt"
    source = source_path.read_text(encoding="utf-8")
    if "color=Color(0xFFEAF5EE)" in source and "InteractiveLessonLab" in source:
        raise SystemExit("Concept lab still uses the detached pale-green panel styling")
    print("PASS: concept lab does not use the detached pale-green panel styling")
    print("PASS: tutor ready screen exposes Teach without duplicating chapter/topic selection or showing setup")

def assert_checkpoint(path, screenshot_path=None):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    print("CHECKPOINT TEXT:", " | ".join(texts[:120]))
    required = ("i understand", "explain again", "i have a question", "watch the pattern")
    has_checkpoint_heading = "quick check" in joined or "let's check your understanding" in joined or "does that make sense so far?" in joined
    missing = [label for label in required if label not in joined]
    if not has_checkpoint_heading:
        missing.append("understanding checkpoint heading/prompt")
    if missing:
        raise SystemExit("Live lesson did not pause at the complete understanding checkpoint: " + ", ".join(missing))
    prompt_index = max(joined.find("quick check"), joined.find("let's check your understanding"), joined.find("does that make sense so far?"))
    prompt_and_actions = joined[prompt_index:prompt_index + 400] if prompt_index >= 0 else joined
    if re.search(r"(^|\s)(null|undefined)(\s|$)", prompt_and_actions):
        raise SystemExit("Understanding checkpoint rendered a null/undefined placeholder")
    prompt_lines = [value.strip() for value in texts if value.strip().lower() not in required and value.strip().lower() != "quick check"]
    if not any("?" in value and len(value) >= 8 for value in prompt_lines):
        raise SystemExit("Understanding checkpoint has no human-readable question")
    if not screenshot_path:
        raise SystemExit("Checkpoint screenshot path is required; XML presence alone cannot prove the animation is visible")
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to inspect checkpoint screenshot") from exc
    image = Image.open(screenshot_path).convert("RGB")
    width, height = image.size
    # The five repeated-one tiles use exact fill #DCE7FF. Exclude the top header
    # and search only the teaching viewport so the LIVE badge cannot pass this check.
    pixels = image.load()
    x1, x2 = int(width * .08), int(width * .92)
    y1, y2 = int(height * .18), int(height * .76)
    tile_pixels = sum(1 for y in range(y1, y2) for x in range(x1, x2) if pixels[x, y] == (220, 231, 255))
    print(f"Checkpoint repeated-ones tile pixels in teaching viewport: {tile_pixels}")
    if tile_pixels < 350:
        raise SystemExit("Checkpoint XML exists, but the repeated-ones animation is not visibly rendered in the teaching viewport")
    print("PASS: checkpoint prompt, response choices, and visible repeated-ones animation are present")

def assert_continued(path):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    print("CONTINUED LESSON TEXT:", " | ".join(texts[:120]))
    # The backend may return four or five segments, and the next segment can
    # reach its own understanding checkpoint before the emulator captures a frame.
    # The shell-level assertion verifies the counter and caption both changed from
    # the checkpoint we tapped; here verify the UI has advanced beyond segment 2.
    import re
    counters = re.findall(r"(\d+)\s*/\s*(\d+)", joined)
    progressed = any(int(current) >= 3 and int(total) >= int(current) for current, total in counters)
    if not progressed:
        raise SystemExit("Checkpoint closed, but no later lesson segment was confirmed active")
    print("PASS: understanding response advanced beyond segment 2 (including valid 4- or 5-segment lessons)")

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
    if "set up your lesson" not in joined:
        raise SystemExit("The pre-tutor lesson-selection screen did not render its setup heading")
    if "done" not in joined:
        raise SystemExit("Lesson-selection screen has no Done action to return to the tutor")
    # Done must remain in the visible, fixed footer even when the setup fields
    # need scrolling; a label somewhere in off-screen content is not sufficient.
    done_nodes = [n for n in nodes if n.attrib.get("text", "").strip().lower() == "done"]
    if not done_nodes:
        raise SystemExit("Lesson-selection Done action is not exposed as a visible accessibility node")
    done_node = next((n for n in done_nodes if n.attrib.get("enabled") == "true"), done_nodes[0])
    bounds = done_node.attrib.get("bounds", "")
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        raise SystemExit("Lesson-selection Done action has no visible screen bounds")
    x1, y1, x2, y2 = map(int, match.groups())
    if x2 <= x1 or y2 <= y1:
        raise SystemExit("Lesson-selection Done action has zero-area bounds")
    if done_node.attrib.get("enabled") == "false":
        raise SystemExit("Lesson-selection Done action is disabled")
    # Voice preferences live lower in the independently scrollable setup form.
    # Validate the controls in a second accessibility dump after scrolling rather
    # than falsely treating off-screen Compose children as missing.
    expected = ("Mathematics", "Language", "English", "Tanglish")
    missing = [term for term in expected if term.lower() not in joined]
    # When a saved session already has Chapter 1 selected, the control shows the
    # selected chapter name rather than the empty-state "Choose chapter" prompt.
    if "choose chapter" not in joined and "patterns in mathematics" not in joined:
        missing.append("Choose chapter or selected chapter (Patterns in Mathematics)")
    # The topic picker intentionally shows its selected database topic (for this
    # smoke test, "All 1s") instead of the "Choose concept" placeholder. Accept
    # either state, but never accept a settings screen with no topic selection.
    if "choose concept" not in joined and "all 1s" not in joined:
        missing.append("Choose concept or selected topic (All 1s)")
    if missing:
        raise SystemExit("Tutor settings are missing expected controls: " + ", ".join(missing))
    print("PASS: subject, chapter/topic, language, and fixed Done footer are accessible")

def assert_voice_settings(path):
    nodes, texts = load(path)
    joined = "\\n".join(texts + [n.attrib.get("content-desc", "") for n in nodes]).lower()
    print("SCROLLED SETTINGS TEXT:", " | ".join(texts[:140]))
    expected = ("read replies aloud", "prefer on-device voice")
    missing = [label for label in expected if label not in joined]
    if missing:
        raise SystemExit("Voice controls are missing after scrolling lesson setup: " + ", ".join(missing))
    print("PASS: both voice preferences are reachable by scrolling the lesson setup")

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
    joined = "\n".join(texts).lower()
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

def assert_completed_lesson(path):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    print("COMPLETED LESSON TEXT:", " | ".join(texts[:100]))
    if "live lesson complete" not in joined:
        raise SystemExit("Playback did not reach the explicit lesson-complete state")
    if "ask your teacher" not in joined:
        raise SystemExit("Question composer is missing after lesson playback completes")
    if not any(len(value.strip()) >= 220 and "all 1s" in value.lower() for value in texts):
        raise SystemExit("Completed lesson disappeared instead of remaining available in chat history")
    if any(term in joined for term in ("how did that explanation feel", "i understand", "explain again")):
        raise SystemExit("Per-reply feedback prompt reappeared after the lesson")
    print("PASS: completed lesson remains in chat and follow-up input is available")


def assert_followup_answer(path):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    print("FOLLOW-UP TEXT:", " | ".join(texts[:100]))
    expected = "the smoke-test tutor is ready to help with the selected topic"
    if expected not in joined:
        raise SystemExit("Follow-up question did not receive the expected tutor response")
    if "why does all 1s repeat" not in joined:
        raise SystemExit("The submitted follow-up question is not visible in chat history")
    print("PASS: follow-up question and answer are both visible")


def assert_live(path):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    print("LIVE LESSON TEXT:", " | ".join(texts[:140]))
    # The app intentionally exposes progress as "Playing segment N of M" /
    # "Live lesson · segment N of M"; it never renders the obsolete literal
    # "teacher is speaking". Validate the real progress + inline lesson content.
    # Audio/highlight progression is checked independently below, so this
    # assertion must not mask those checks with a stale accessibility label.
    teaching_texts = [value.strip() for value in texts if len(value.strip()) >= 220]
    if not teaching_texts:
        raise SystemExit("Tutor screen does not expose one complete teaching explanation in its active caption")
    forbidden_interruptions = ("quick check", "let's check your understanding", "does that make sense so far", "i understand", "explain again", "i have a question", "watch the pattern", "visual focus")
    found_interruptions = [label for label in forbidden_interruptions if label in joined]
    if found_interruptions:
        raise SystemExit("Per-segment checkpoint or animation UI reappeared: " + ", ".join(found_interruptions))
    lesson_words = ("one", "all 1s", "pattern", "number")
    if not any(term in joined for term in lesson_words):
        raise SystemExit("Live lesson is active but no recognizable inline teaching caption text is accessible")
    voice_failures = (
        "no compatible english voice",
        "this selected voice engine has no tamil voice",
        "voice playback failed",
        "voice playback did not start",
        "voice engine could not initialize",
        "speech engine did not finish starting",
    )
    failure = next((message for message in voice_failures if message in joined), None)
    if failure:
        raise SystemExit("Live lesson cannot speak on the selected voice engine: " + failure)
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
    if "all 1s" in joined:
        if not any(term in joined for term in ("1, 1, 1", "repeats the number 1", "each term is 1", "same number", "number one", "stays the same", "each value stays the same")):
            raise SystemExit("All 1s lesson lacks an explanation of the repeated-one rule")
        if "square numbers grow" in joined or "1²" in joined or "+3" in joined:
            raise SystemExit("All 1s topic is incorrectly showing square-number content")
    print("PASS: complete continuous lesson is visible without checkpoints, animations, or interactive overlays")

def exact_color_mask(image, target):
    """Return a fast Pillow mask for pixels exactly matching an RGB color."""
    from PIL import Image, ImageChops
    rgb = image.convert("RGB")
    channels = rgb.split()
    channel_masks = [
        channel.point(lambda value, expected=expected: 255 if value == expected else 0)
        for channel, expected in zip(channels, target)
    ]
    # Intersect channel masks so near-matches never count as exact target pixels.
    return ImageChops.multiply(
        ImageChops.multiply(channel_masks[0], channel_masks[1]),
        channel_masks[2],
    )


def assert_highlight_frames(directory):
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to inspect word-highlight screenshots") from exc
    root = Path(directory)
    frames = sorted(root.glob("*.png"))
    if not frames:
        raise SystemExit("No live lesson frames were captured")
    target = (220, 231, 255)  # WordByWordCaption active-word highlight: #DCE7FF
    best_count = 0
    best_frame = ""
    centers = []
    for frame in frames:
        try:
            image = Image.open(frame).convert("RGB")
            mask = exact_color_mask(image, target)
            count = mask.histogram()[255]
            if count > best_count:
                best_count, best_frame = count, str(frame)
            # The highlight is a single word-sized region; its bounding-box center
            # is sufficient to detect movement. Pillow computes the mask/bounds in
            # optimized native code instead of scanning millions of pixels in Python.
            bbox = mask.getbbox()
            if count >= 12 and bbox:
                centers.append(((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2))
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
    joined = "\n".join(texts).lower()
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
    # The tutor is intentionally a continuous canvas, not a large inset green card.
    # The old card's exact pale-green fill (#EAF5EE) should no longer dominate the
    # lower teaching viewport; small inline animation highlights remain acceptable.
    x1, x2 = int(width * 0.10), int(width * 0.90)
    y1, y2 = int(height * 0.48), int(height * 0.76)
    region = image.crop((x1, y1, x2, y2))
    count = exact_color_mask(region, (234, 245, 238)).histogram()[255]
    area = max(1, region.width * region.height)
    ratio = count / area
    print(f"Separate-card background coverage in teaching viewport: {ratio:.1%}")
    if ratio > 0.35:
        raise SystemExit("A large pale-green lesson card still occupies the teaching viewport")
    print("PASS: live lesson uses a continuous canvas without a dominant green card")


def exact_text_candidates(nodes, target):
    """Prefer visible text over accessibility descriptions for exact-label taps.

    DocumentsUI can expose a filename as both a non-clickable TextView and a
    clickable preview-icon content description. Combining both lets tap_exact
    choose the preview affordance. Prefer actual text when present, and fall
    back to content descriptions only for controls without visible text.
    """
    normalized_target = target.strip().lower().lstrip("▶").strip()
    text_matches = [
        node for node in nodes
        if node.attrib.get("text", "").strip().lower().lstrip("▶").strip() == normalized_target
    ]
    if text_matches:
        return text_matches
    return [
        node for node in nodes
        if node.attrib.get("content-desc", "").strip().lower().lstrip("▶").strip() == normalized_target
    ]


def tap_exact(path, target):
    """Tap an exact visible label, avoiding ambiguous substring matches like 'Teach'."""
    nodes, texts = load(path)
    candidates = exact_text_candidates(nodes, target)
    if not candidates:
        raise SystemExit(f"Could not find exact target {target!r}; visible labels: {' | '.join(texts[:100])}")
    # Compose sometimes exposes a clickable parent and a non-clickable child with
    # the same text. Prefer the clickable node; otherwise its bounds still identify
    # the exact control without accidentally hitting a similarly named chat item.
    node = next((n for n in candidates if n.attrib.get("clickable") == "true"), candidates[0])
    bounds = node.attrib.get("bounds", "")
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        raise SystemExit(f"Exact target {target!r} has invalid accessibility bounds: {bounds!r}")
    x1, y1, x2, y2 = map(int, match.groups())
    x, y = (x1 + x2) // 2, (y1 + y2) // 2
    print(f"Tapping exact target {target!r} at ({x}, {y}), bounds={bounds}, clickable={node.attrib.get('clickable')}")
    subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap", str(x), str(y)],
                   check=True, timeout=45)


def tap_file(path, filename):
    """Select a file through a genuinely clickable filename row, never its preview icon."""
    nodes, texts = load(path)
    target = filename.strip().lower()
    candidates = []
    for node in nodes:
        label = node.attrib.get("text", "").strip().lower()
        desc = node.attrib.get("content-desc", "").strip().lower()
        # List view commonly exposes the filename as text; allow metadata suffixes
        # in descriptions, but explicitly exclude the preview-icon action.
        matches = label == target or desc == target or desc.startswith(target + ",")
        if not matches or node.attrib.get("clickable") != "true":
            continue
        if "preview the file" in desc:
            continue
        bounds = node.attrib.get("bounds", "")
        if re.fullmatch(r"\\[\\d+,\\d+\\]\\[\\d+,\\d+\\]", bounds):
            candidates.append(node)
    if not candidates:
        observed = [f"text={n.attrib.get('text','')!r}, desc={n.attrib.get('content-desc','')!r}, clickable={n.attrib.get('clickable')}, bounds={n.attrib.get('bounds','')}"
                    for n in nodes if filename.lower() in (n.attrib.get("text","") + " " + n.attrib.get("content-desc","")).lower()]
        raise SystemExit("No clickable filename row for " + repr(filename) +
                         "; matching nodes: " + (" | ".join(observed) if observed else "none") +
                         "; visible labels: " + " | ".join(texts[:80]))
    # Prefer the shortest matching label: a row is more specific than a clickable parent.
    node = min(candidates, key=lambda n: len(n.attrib.get("text","") or n.attrib.get("content-desc","")))
    x1,y1,x2,y2 = map(int, re.fullmatch(r"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", node.attrib["bounds"]).groups())
    x,y=(x1+x2)//2,(y1+y2)//2
    print(f"Selecting clickable file row {filename!r} at ({x},{y}), bounds={node.attrib['bounds']}, text={node.attrib.get('text')!r}, desc={node.attrib.get('content-desc')!r}")
    subprocess.run(["adb","-s","emulator-5554","shell","input","tap",str(x),str(y)],check=True,timeout=45)


def tap(path, target):
    nodes, texts = load(path)
    candidates = []
    for node in nodes:
        text = node.attrib.get("text", "").strip()
        description = node.attrib.get("content-desc", "").strip()
        if target.lower() in text.lower() or target.lower() in description.lower():
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

def tap_input(path):
    """Focus the actual editable composer node, not its placeholder label."""
    nodes, _ = load(path)
    candidates = [node for node in nodes
                  if node.attrib.get("class") == "android.widget.EditText"
                  and node.attrib.get("enabled", "true") == "true"]
    if not candidates:
        raise SystemExit("Could not find an enabled editable text field in " + path)
    node = candidates[0]
    bounds = node.attrib.get("bounds", "")
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if not match:
        raise SystemExit("Editable text field has invalid accessibility bounds: " + bounds)
    x1, y1, x2, y2 = map(int, match.groups())
    x, y = (x1 + x2) // 2, (y1 + y2) // 2
    print(f"Focusing editable text field at ({x}, {y}), bounds={bounds}")
    subprocess.run(["adb", "-s", "emulator-5554", "shell", "input", "tap", str(x), str(y)],
                   check=True, timeout=45)


def assert_composer_question(path):
    nodes, _ = load(path)
    expected = "why does all 1s repeat"
    fields = [node.attrib.get("text", "").replace("\\n", " ").lower()
              for node in nodes if node.attrib.get("class") == "android.widget.EditText"]
    if not any(expected in value for value in fields):
        raise SystemExit("Follow-up question was not entered into the editable composer; refusing to tap Send")
    print("PASS: follow-up question is present in the composer before Send")


def has_label(path, label):
    _, texts = load(path)
    found = any(label.lower() in text.lower() for text in texts)
    print(f"LABEL CHECK: {label!r} {'present' if found else 'not present'}")
    return found

def assert_topic_selected(path):
    _, texts = load(path)
    joined = "\n".join(texts).lower()
    if "all 1s" not in joined and "patterns in mathematics" not in joined:
        raise SystemExit("No database-backed topic/chapter selection is visible: " + " | ".join(texts[:100]))
    print("PASS: a database-backed chapter/topic is already selected")

def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: ui_smoke.py {assert-home|assert-tutor|assert-checkpoint|assert-continued|assert-feedback|assert-settings|assert-live|tap} XML [TARGET]")
    action, path = sys.argv[1], sys.argv[2]
    if not Path(path).is_file():
        raise SystemExit("UI XML file does not exist: " + path)
    if action == "assert-home":
        assert_home(path)
    elif action == "assert-tutor":
        assert_tutor(path)
    elif action == "assert-continued":
        assert_continued(path)
    elif action == "assert-feedback":
        assert_feedback(path)
    elif action == "assert-checkpoint" and len(sys.argv) >= 4:
        assert_checkpoint(path, sys.argv[3])
    elif action == "assert-settings":
        assert_settings(path)
    elif action == "assert-voice-settings":
        assert_voice_settings(path)
    elif action == "has-label" and len(sys.argv) >= 4:
        if not has_label(path, sys.argv[3]):
            raise SystemExit(1)
    elif action == "assert-topic-selected":
        assert_topic_selected(path)
    elif action == "tap-input":
        tap_input(path)
    elif action == "assert-composer-question":
        assert_composer_question(path)
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
    elif action == "tap-exact" and len(sys.argv) >= 4:
        tap_exact(path, sys.argv[3])
    elif action == "assert-live":
        assert_live(path)
    elif action == "assert-completed-lesson":
        assert_completed_lesson(path)
    elif action == "assert-followup":
        assert_followup_answer(path)
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
