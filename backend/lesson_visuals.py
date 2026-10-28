"""Small, source-linked 2D visual blueprints derived from approved synthesized lessons.

The module intentionally creates compact vector/diagram recipes, not 3D assets,
large animations, or textbook-page copies. Every label is copied from the saved
lesson synthesis so the visual cannot silently drift from the narration.
"""
from __future__ import annotations

import hashlib
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
    "cycle": "cycle",
    "none": "concept_card",
}


def _clean(value: Any, limit: int = 160) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _step_visual(step: Mapping[str, Any], index: int) -> dict[str, Any]:
    visual = step.get("visual") if isinstance(step.get("visual"), Mapping) else {}
    raw_kind = _clean(visual.get("type") or step.get("visual_type") or "none", 32).lower()
    kind = _VISUAL_KIND_MAP.get(raw_kind, "concept_card")
    objects = visual.get("objects", [])
    if not isinstance(objects, list):
        objects = []
    labels = [_clean(item, 72) for item in objects if _clean(item, 72)]
    actions = visual.get("actions", [])
    if isinstance(actions, str):
        actions = [actions]
    if not isinstance(actions, list):
        actions = []
    actions = [_clean(item, 90) for item in actions if _clean(item, 90)][:4]
    narration_sync = visual.get("narration_sync", [])
    if isinstance(narration_sync, str):
        narration_sync = [narration_sync]
    if not isinstance(narration_sync, list):
        narration_sync = []
    sync_labels = [_clean(item, 90) for item in narration_sync if _clean(item, 90)][:4]
    caption = _clean(step.get("caption") or step.get("teacher_says") or step.get("title"), 240)
    title = _clean(step.get("title") or caption, 90)
    # Do not create an unrelated stock image: this is a vector blueprint made
    # from the selected synthesis step's own nouns, labels, and actions.
    nodes = labels[:6] or sync_labels[:4] or [title]
    return {
        "step_id": _clean(step.get("id") or f"step-{index + 1}", 48),
        "title": title,
        "caption": caption,
        "kind": kind,
        "layout": "compact_2d",
        "motion": "none",
        "nodes": nodes,
        "actions": actions,
        "narration_sync": sync_labels,
        "source_chunk_ids": [str(value) for value in step.get("source_chunk_ids", []) if value][:8]
            if isinstance(step.get("source_chunk_ids", []), list) else [],
    }


def build_visual_records(lesson_id: str, lesson: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Create stable visual records for an already-synthesized lesson's teaching sequence."""
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
