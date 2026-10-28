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
    "number_line": "number_line",
    "geometry": "geometry",
    "compare": "compare",
    "process": "process",
    "table": "table",
    "diagram": "diagram",
    "fraction": "fraction",
    "parts": "fraction",
    "fraction": "fraction",
    "cycle": "cycle",
    "none": "concept_card",
}


def _clean(value: Any, limit: int = 160) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _svg_text(value: str) -> str:
    return html.escape(value, quote=True)


def _render_svg(kind: str, title: str, nodes: list[str]) -> str:
    """Render a responsive, static 2D SVG from only synthesis-provided labels."""
    labels = [_svg_text(_clean(node, 42)) for node in nodes[:6]]
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
        count = min(3, len(labels))
        for i, label in enumerate(labels[:count]):
            x = 28 + i * 88
            parts.append(f'<rect x="{x}" y="43" width="82" height="68" rx="4" fill="#FFFFFF" stroke="#7C91A0"/>')
            parts.append(f'<rect x="{x}" y="43" width="82" height="22" rx="4" fill="#DCEFEB"/>')
            parts.append(f'<text x="{x+41}" y="57" text-anchor="middle" font-size="8" font-family="sans-serif" fill="#24445B">{label}</text>')
            parts.append(f'<path d="M{x} 87 H{x+82}" stroke="#D7E5EC"/>')
    else:
        parts.append('<circle cx="160" cy="76" r="42" fill="#DCEFEB" stroke="#287F79" stroke-width="1.5"/>')
        parts.append('<text x="160" y="72" text-anchor="middle" font-size="9" font-family="sans-serif" fill="#24445B">' + labels[0] + '</text>')
        if len(labels) > 1:
            parts.append('<text x="160" y="86" text-anchor="middle" font-size="8" font-family="sans-serif" fill="#24445B">' + labels[1] + '</text>')
    parts.append("</svg>")
    return "".join(parts)


def _step_visual(step: Mapping[str, Any], index: int) -> dict[str, Any]:
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
    caption = _clean(step.get("caption") or step.get("teacher_says") or step.get("title"), 240)
    title = _clean(step.get("title") or caption, 90)
    nodes = labels[:6] or sync_labels[:4] or [title]
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
        if not blueprint["nodes"]:
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
