"""Small, source-linked 2D vector assets derived from approved synthesized lessons.

Each visual is a compact SVG/vector recipe generated from the saved teaching step.
No 3D, large animation, stock image, or copied textbook page is created.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from typing import Any, Mapping


_VISUAL_KIND_MAP = {
    "number_pattern": "sequence",
    "sequence": "sequence",
    "repeating_pattern": "sequence",
    "shape_pattern": "sequence",
    "number_line": "number_line",
    "integer_line": "number_line",
    "geometry": "geometry",
    "angle": "geometry",
    "compare": "compare",
    "comparison": "compare",
    "process": "process",
    "chain": "process",
    "table": "table",
    "diagram": "diagram",
    "fraction": "fraction",
    "parts": "fraction",
    "cycle": "cycle",
    "none": "concept_card",
}


def _clean(value: Any, limit: int = 160) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _svg_text(value: str) -> str:
    return html.escape(value, quote=True)


def _render_svg(kind: str, title: str, nodes: list[str]) -> str:
    """Render a responsive, static 2D SVG from only synthesis-provided labels."""
    raw_labels = [_clean(node, 84) for node in nodes[:6]]
    labels = [_svg_text(label) for label in raw_labels]
    if not labels:
        labels = [_svg_text(title or "Key idea")]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 156" role="img" '
        'aria-label="' + _svg_text(title or "Lesson visual") + '" preserveAspectRatio="xMidYMid meet">',
        '<rect x="1" y="1" width="318" height="154" rx="14" fill="#F5FAFC" stroke="#D7E5EC"/>',
    ]
    if kind == "fraction":
        # Four equal parts is a safe visual default only when the synthesis itself
        # explicitly mentions four; otherwise use the number of labelled parts.
        count = 4 if any("four" in n.lower() or n.strip() == "4" for n in nodes) else max(2, min(6, len(labels)))
        gap, left, top, total_w, total_h = 5, 28, 39, 264, 72
        cell_w = (total_w - gap * (count - 1)) / count
        parts.append('<text x="160" y="23" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#24445B">' + labels[0] + '</text>')
        for i in range(count):
            x = left + i * (cell_w + gap)
            fill = "#5BB7A5" if i == 0 else "#FFFFFF"
            parts.append(f'<rect x="{x:.1f}" y="{top}" width="{cell_w:.1f}" height="{total_h}" rx="5" fill="{fill}" stroke="#287F79" stroke-width="1.4"/>')
        parts.append('<text x="160" y="132" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#24445B">' + (labels[1] if len(labels) > 1 else "Equal parts") + '</text>')
    elif kind in {"sequence", "process", "cycle"}:
        count = min(4, len(labels))
        box_w = 64 if count >= 4 else min(88, 264 / max(count, 1))
        total = count * box_w + max(0, count - 1) * 8
        left = (320 - total) / 2
        for i, label in enumerate(labels[:count]):
            x = left + i * (box_w + 8)
            if i:
                parts.append(f'<path d="M{x-7:.1f} 77 l4 -4 l0 8 z" fill="#287F79"/>')
            parts.append(f'<rect x="{x:.1f}" y="49" width="{box_w:.1f}" height="54" rx="8" fill="#FFFFFF" stroke="#287F79" stroke-width="1.4"/>')
            parts.append(f'<text x="{x+box_w/2:.1f}" y="79" text-anchor="middle" font-size="9" font-family="sans-serif" fill="#24445B">{label}</text>')
    elif kind == "compare":
        parts.append('<path d="M44 119 H276" stroke="#7C91A0" stroke-width="1.5"/>')
        for i, label in enumerate(labels[:3]):
            x = 52 + i * 82
            height = 28 + i * 15
            parts.append(f'<rect x="{x}" y="{119-height}" width="42" height="{height}" rx="5" fill="{("#5BB7A5", "#7CA9E8", "#F1C46A")[i]}"/>')
            parts.append(f'<text x="{x+21}" y="137" text-anchor="middle" font-size="8" font-family="sans-serif" fill="#24445B">{label}</text>')
    elif kind in {"geometry", "number_line"}:
        parts.append('<path d="M34 91 H286" stroke="#287F79" stroke-width="2"/>')
        for i, label in enumerate(labels[:5]):
            x = 44 + i * (232 / max(1, min(4, len(labels)-1)))
            parts.append(f'<circle cx="{x:.1f}" cy="91" r="5" fill="#5BB7A5" stroke="#287F79"/>')
            parts.append(f'<text x="{x:.1f}" y="76" text-anchor="middle" font-size="9" font-family="sans-serif" fill="#24445B">{label}</text>')
        if kind == "geometry":
            parts.append('<path d="M96 112 L160 37 L224 112 Z" fill="#7CA9E8" fill-opacity=".25" stroke="#287F79" stroke-width="2"/>')
    elif kind == "table":
        count = min(3, len(raw_labels))
        for i, raw_label in enumerate(raw_labels[:count]):
            header, separator, values = raw_label.partition("|")
            x = 28 + i * 88
            parts.append(f'<rect x="{x}" y="39" width="82" height="78" rx="4" fill="#FFFFFF" stroke="#7C91A0"/>')
            parts.append(f'<rect x="{x}" y="39" width="82" height="24" rx="4" fill="#DCEFEB"/>')
            parts.append(f'<text x="{x+41}" y="54" text-anchor="middle" font-size="8" font-family="sans-serif" fill="#24445B">{_svg_text(header[:24])}</text>')
            if separator and values:
                values = _svg_text(values[:54])
                parts.append(f'<text x="{x+41}" y="82" text-anchor="middle" font-size="7" font-family="sans-serif" fill="#24445B">{values[:27]}</text>')
                if len(values) > 27:
                    parts.append(f'<text x="{x+41}" y="94" text-anchor="middle" font-size="7" font-family="sans-serif" fill="#24445B">{values[27:54]}</text>')
            else:
                parts.append(f'<path d="M{x+8} 84 H{x+74}" stroke="#D7E5EC"/>')
                parts.append(f'<path d="M{x+8} 99 H{x+74}" stroke="#D7E5EC"/>')
    elif kind == "diagram":
        # A connected concept map is clearer than a single generic bubble.
        positions = [(54, 76), (160, 76), (266, 76)]
        for i, label in enumerate(labels[:3]):
            x, y = positions[i]
            if i:
                parts.append(f'<path d="M{x-52} {y} H{x-36}" stroke="#287F79" stroke-width="2"/>')
            parts.append(f'<rect x="{x-43}" y="{y-22}" width="86" height="44" rx="8" fill="#FFFFFF" stroke="#287F79" stroke-width="1.5"/>')
            parts.append(f'<text x="{x}" y="{y+3}" text-anchor="middle" font-size="8" font-family="sans-serif" fill="#24445B">{label}</text>')
        parts.append('<text x="160" y="132" text-anchor="middle" font-size="9" font-family="sans-serif" fill="#24445B">Ideas connect as understanding grows</text>')
    else:
        # Do not silently fabricate a scene when evidence is too weak.
        return ""
    parts.append("</svg>")
    return "".join(parts)


def _infer_visual_content(title: str, caption: str, fallback_kind: str, source_evidence: str = "") -> tuple[str, list[str]]:
    """Choose a topic-specific scene only from synthesis text and its cited source evidence."""
    text = _clean(f"{title} {caption} {source_evidence}", 5000)
    lowered = text.casefold()

    # This textbook sequence is a stable, explicit concept: each term remains 1.
    if re.search(r"\ball\s+1(?:['’]?s?)?\b|\ball\s+ones?\b", lowered):
        return "sequence", ["1", "1", "1", "1", "1"]

    # Extract clear rows from OCR tables only when the values are unambiguous.
    if fallback_kind == "table":
        row_labels = [
            ("Squares", r"squares"),
            ("Triangular numbers", r"triangular numbers"),
            ("Cubes", r"cubes"),
            ("All 1s", r"\ball\s+1(?:['’]?s?)?\b|\ball\s+ones?\b"),
            ("Counting numbers", r"counting numbers"),
            ("Odd numbers", r"odd numbers"),
            ("Even numbers", r"even numbers"),
        ]
        found = []
        matches = []
        for label, pattern in row_labels:
            match = re.search(r"(?i)\b" + pattern + r"\b", text)
            if match:
                matches.append((match.start(), match.end(), label))
        matches.sort()
        for index, (start, end, label) in enumerate(matches):
            next_start = matches[index + 1][0] if index + 1 < len(matches) else min(len(text), end + 80)
            segment = text[end:next_start]
            values = re.findall(r"(?<![A-Za-z])\d{1,3}(?![A-Za-z])", segment)
            # Reject OCR-merged values and page-number-like outliers instead of guessing.
            if len(values) >= 3 and all(len(value) <= 2 or value in {"100", "125"} for value in values[:5]):
                values = values[:5]
                if label == "All 1s" and all(value == "1" for value in values):
                    found.append("All 1s|1 · 1 · 1 · 1 · 1")
                elif label == "Squares" and values[:5] == ["1", "4", "9", "16", "25"]:
                    found.append("Squares|1 · 4 · 9 · 16 · 25")
                elif label == "Counting numbers" and values[:5] == ["1", "2", "3", "4", "5"]:
                    found.append("Counting|1 · 2 · 3 · 4 · 5")
                elif label == "Odd numbers" and values[:5] == ["1", "3", "5", "7", "9"]:
                    found.append("Odd|1 · 3 · 5 · 7 · 9")
                elif label == "Even numbers" and values[:5] == ["2", "4", "6", "8", "10"]:
                    found.append("Even|2 · 4 · 6 · 8 · 10")
        if found:
            # Put the currently named concept first when the caption contains it.
            if "all 1s" in lowered or "all ones" in lowered:
                found.sort(key=lambda row: 0 if row.startswith("All 1s|") else 1)
            return "table", found[:3]

    # Topic-specific scene rules learned from Science Chapter 1 review. These
    # are deterministic vector scenes, not keyword-only generic cards. They only
    # activate when the synthesis text itself contains the complete concept cue.
    if ("pen stops writing" in lowered or "pen has stopped writing" in lowered) and any(
        term in lowered for term in ("ink", "refill", "guess", "test", "check")
    ):
        return "process", ["Notice the problem", "Make a guess", "Test the refill"]

    if "jigsaw" in lowered and any(term in lowered for term in ("knowledge", "discover", "question", "piece")):
        return "process", ["What we know", "New discovery", "New questions"]

    if any(term in lowered for term in ("scientific method", "scientific inquiry", "investigation")) and any(
        term in lowered for term in ("observe", "question", "test", "evidence")
    ):
        labels = []
        for label, cues in (
            ("Observe", ("observe", "notice")),
            ("Ask", ("question", "ask why")),
            ("Suggest", ("guess", "possible explanation", "hypothesis")),
            ("Test", ("test", "experiment", "check")),
            ("Review results", ("evidence", "result", "conclusion")),
        ):
            if any(cue in lowered for cue in cues):
                labels.append(label)
        if len(labels) >= 3:
            return "process", labels[:5]

    if any(term in lowered for term in ("paper", "metal key", "plastic ruler", "rubber eraser")) and any(
        term in lowered for term in ("material", "made of", "object")
    ):
        labels = [label for label, cue in (
            ("Paper", "paper"), ("Metal key", "metal key"),
            ("Plastic ruler", "plastic ruler"), ("Rubber eraser", "rubber eraser")
        ) if cue in lowered]
        if len(labels) >= 2:
            return "compare", labels[:4]

    if any(term in lowered for term in ("curious", "curiosity", "flower bloom", "stars shine")) and any(
        term in lowered for term in ("why", "question", "wonder", "explore")
    ):
        return "process", ["Notice", "Ask why", "Explore with evidence"]

    if re.search(r"\b(fraction|fractions|half|halves|quarter|quarters|\d+\s*/\s*\d+)\b", lowered):
        labels = []
        for word in ("whole", "half", "quarter", "third", "equal parts", "numerator", "denominator"):
            if re.search(r"\b" + word + r"\b", lowered):
                labels.append(word.title())
        fraction = re.search(r"\b\d+\s*/\s*\d+\b", text)
        if fraction:
            labels.insert(0, fraction.group(0).replace(" ", ""))
        return "fraction", labels[:6] or ["Whole", "Equal parts"]

    if any(term in lowered for term in ("water cycle", "evaporation", "condensation", "precipitation")):
        labels = [term.title() for term in ("evaporation", "condensation", "precipitation", "collection") if term in lowered]
        return "cycle", labels[:4] or ["Water", "Change", "Water"]

    if any(term in lowered for term in ("angle", "triangle", "parallel", "perpendicular", "point", "line segment")):
        labels = [term.title() for term in ("point", "line", "line segment", "angle", "triangle", "parallel", "perpendicular") if re.search(r"\b" + re.escape(term) + r"\b", lowered)]
        return "geometry", labels[:5] or ["Point", "Line", "Angle"]

    if any(term in lowered for term in ("perimeter", "area of a rectangle", "area of a square")):
        labels = [term.title() for term in ("length", "width", "area", "perimeter") if re.search(r"\b" + re.escape(term) + r"\b", lowered)]
        return "geometry", labels[:5] or ["Length", "Width", "Area"]

    if any(term in lowered for term in ("magnet", "magnetic", "north pole", "south pole")):
        labels = [term.title() for term in ("north pole", "south pole", "attract", "repel", "magnetic field") if term in lowered]
        return "diagram", labels[:4] or ["Magnet", "Poles"]

    if any(term in lowered for term in ("melting", "freezing", "solid", "liquid", "gas")):
        labels = [term.title() for term in ("solid", "liquid", "gas", "melting", "freezing", "evaporation", "condensation") if re.search(r"\b" + re.escape(term) + r"\b", lowered)]
        if len(labels) >= 2:
            return "process", labels[:5]

    if "number line" in lowered:
        numbers = re.findall(r"(?<![A-Za-z])[-+]?\d{1,2}(?![A-Za-z])", text)
        unique = list(dict.fromkeys(numbers))
        if len(unique) >= 2:
            return "number_line", unique[:5]
        return "number_line", ["0", "1", "2"]

    if any(term in lowered for term in ("bar graph", "pictograph", "tally marks")):
        labels = []
        if "tally marks" in lowered and "count" in lowered:
            labels.append("Tally marks|Count")
        if "pictograph" in lowered and "symbol" in lowered:
            labels.append("Pictograph|Picture symbols")
        if "bar graph" in lowered and any(term in lowered for term in ("value", "values", "height", "heights")):
            labels.append("Bar graph|Values")
        if labels:
            return "table", labels[:3]

    if any(term in lowered for term in ("cooking", "bicycle tyre", "light bulb", "daily life", "everyday problem")):
        labels = [label for term, label in (("cooking", "Cooking"), ("bicycle tyre", "Bicycle tyre"), ("light bulb", "Light bulb"), ("switch", "Switch")) if term in lowered]
        return "compare", labels[:3] or ["Observe", "Suggest", "Test"]

    # If a synthesis supplied no structured recipe, do not fabricate a diagram from its title.
    return fallback_kind, []


def _step_visual(step: Mapping[str, Any], index: int) -> dict[str, Any]:
    source_caption = _clean(step.get("caption") or step.get("teacher_says") or step.get("title"), 5000)
    caption = _clean(source_caption, 240)
    title = _clean(step.get("title") or caption, 90)
    visual = step.get("visual") if isinstance(step.get("visual"), Mapping) else {}
    raw_kind = _clean(visual.get("type") or step.get("visual_type") or "none", 32).lower()
    kind = _VISUAL_KIND_MAP.get(raw_kind, "concept_card")
    objects = visual.get("objects", [])
    if not isinstance(objects, list):
        objects = []
    labels = []
    for item in objects:
        raw_label = item.get("label") if isinstance(item, Mapping) else item
        label = _clean(raw_label, 72)
        if label:
            labels.append(label)
    source_evidence = _clean(step.get("source_evidence") or "", 5000)
    inferred_kind, inferred_nodes = _infer_visual_content(title, source_caption, kind, source_evidence)
    topic_specific_cues = (
        "jigsaw", "pen stops writing", "pen has stopped writing", "scientific method",
        "scientific inquiry", "observe, ask", "paper, a metal key", "plastic ruler",
        "curiosity", "flower bloom", "stars shine",
    )
    if inferred_nodes and (
        kind in {"concept_card", "table"} or not labels
        or any(cue in (title + " " + source_caption).casefold() for cue in topic_specific_cues)
    ):
        # Source-grounded scene rules outrank broad model-provided labels only
        # when a strong topic cue or explicit source excerpt supports the scene.
        kind = inferred_kind
        labels = inferred_nodes
    actions = visual.get("actions", [])
    if isinstance(actions, str):
        actions = [actions]
    if not isinstance(actions, list):
        actions = []
    actions = [_clean(item, 90) for item in actions if _clean(item, 90)][:6]
    narration_sync = visual.get("narration_sync", [])
    if isinstance(narration_sync, str):
        narration_sync = [narration_sync]
    if not isinstance(narration_sync, list):
        narration_sync = []
    sync_labels = [_clean(item, 90) for item in narration_sync if _clean(item, 90)][:6]
    spatial = visual.get("spatial_relationships", [])
    if not isinstance(spatial, list):
        spatial = []
    spatial = [_clean(item, 120) for item in spatial if _clean(item, 120)][:6]
    teaching_order = visual.get("teaching_order", [])
    if not isinstance(teaching_order, list):
        teaching_order = []
    teaching_order = [_clean(item, 100) for item in teaching_order if _clean(item, 100)][:6]
    raw_pages = visual.get("reference_page_numbers", [])
    if isinstance(raw_pages, (str, int)):
        raw_pages = [raw_pages]
    if not isinstance(raw_pages, list):
        raw_pages = []
    reference_pages = []
    for page in raw_pages[:8]:
        try:
            page_no = int(page)
            if page_no > 0 and page_no not in reference_pages:
                reference_pages.append(page_no)
        except (TypeError, ValueError):
            continue
    visual_rationale = _clean(visual.get("visual_rationale"), 180)
    visual_subtype = _clean(visual.get("visual_subtype") or kind, 32).lower()
    nodes = labels[:6] or sync_labels[:4]
    blueprint = {
        "step_id": _clean(step.get("id") or f"step-{index + 1}", 48),
        "title": title,
        "caption": caption,
        "kind": kind,
        "visual_subtype": visual_subtype,
        "layout": "compact_2d",
        "motion": "narration_synced_staggered_reveal",
        "animation_plan": {
            "mode": "staggered_reveal",
            "duration_ms": 850,
            "loop": False,
            "reveal_order": list(range(min(6, len(nodes)))),
            "actions": actions[:6],
            "sync_markers": sync_labels[:6],
            "stages": teaching_order[:6] or actions[:6] or sync_labels[:6],
        },
        "nodes": nodes,
        "actions": actions,
        "narration_sync": sync_labels,
        "spatial_relationships": spatial,
        "teaching_order": teaching_order,
        "reference_page_numbers": reference_pages,
        "visual_rationale": visual_rationale,
        "source_chunk_ids": [str(value) for value in step.get("source_chunk_ids", []) if value][:8]
            if isinstance(step.get("source_chunk_ids", []), list) else [],
        "evidence_status": _clean(visual.get("evidence_status") or "source_cited_draft", 40),
        "quality_flags": visual.get("quality_flags", []) if isinstance(visual.get("quality_flags", []), list) else [],
    }
    # SVG is a compact vector asset stored in the same DB JSON field as its recipe.
    # It is deterministic for a given synthesis step and escapes all source labels.
    blueprint["svg_markup"] = _render_svg(kind, title, nodes)
    return blueprint


def build_visual_records(lesson_id: str, lesson: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Create stable SVG/vector records for an already-synthesized lesson's teaching sequence."""
    sequence = lesson.get("teaching_sequence")
    if not isinstance(sequence, list):
        return []
    records = []
    for index, step in enumerate(sequence):
        if not isinstance(step, Mapping):
            continue
        caption = _clean(step.get("caption") or step.get("teacher_says") or step.get("title"))
        if not caption:
            continue
        blueprint = _step_visual(step, index)
        if not blueprint["nodes"] or not blueprint.get("svg_markup"):
            continue
        serialized = json.dumps(blueprint, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        records.append({
            "id": hashlib.sha256(f"{lesson_id}:{blueprint['step_id']}".encode()).hexdigest()[:32],
            "lesson_id": lesson_id,
            "step_id": blueprint["step_id"],
            "summary_text": caption,
            "visual_kind": blueprint["kind"],
            "blueprint_json": serialized,
            "source_chunk_ids_json": json.dumps(blueprint["source_chunk_ids"], ensure_ascii=False),
            "content_fingerprint": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "blueprint": blueprint,
        })
    return records
