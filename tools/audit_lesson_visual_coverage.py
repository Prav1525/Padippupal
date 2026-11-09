#!/usr/bin/env python3
"""Audit lesson-module visual coverage and create a review queue.

Input curriculum JSON is an array of approved lessons:
[{ "id": "...", "subject": "Science", "chapter": "...",
   "modules": [{ "step_id": "step_1", "title": "...", "caption": "..." }] }]
The script never invents or publishes assets. It reports coverage and proposes
a source route for human review; every unmapped module remains explicitly open.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REAL_WORLD = re.compile(
    r"\b(plant|leaf|flower|animal|bird|insect|habitat|tool|instrument|"
    r"food|grain|fruit|vegetable|magnet|compass|thermometer|water|cloud|"
    r"rain|snow|soil|rock|stone|material|machine|vehicle|body part)\b", re.I
)
ABSTRACT = re.compile(
    r"\b(fractions?|angles?|geometry|symmetry|equations?|number line|integers?|"
    r"factor|multiple|prime|pattern|area|perimeter|ratio|graph|data|"
    r"measurement|construct|polygon|decimal)\b", re.I
)
PROCESS = re.compile(
    r"\b(cycle|process|stage|steps|evaporation|condensation|growth|"
    r"life cycle|separation|method|experiment|rotation|reflection)\b", re.I
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def module_index(curriculum):
    index = {}
    for lesson in curriculum:
        lesson_id = str(lesson.get("id", "")).strip()
        if not lesson_id:
            raise ValueError("Every curriculum lesson must have an id.")
        modules = lesson.get("modules")
        if not isinstance(modules, list):
            raise ValueError(f"Lesson {lesson_id} must contain a modules array.")
        for number, module in enumerate(modules, 1):
            step_id = str(module.get("step_id", "")).strip()
            if not step_id:
                raise ValueError(f"Lesson {lesson_id} module {number} has no step_id.")
            key = (lesson_id, f"module-{number}")
            if key in index:
                raise ValueError(f"Duplicate curriculum module key: {key}")
            index[key] = {
                "lesson_id": lesson_id, "module_key": key[1],
                "step_id": step_id, "subject": lesson.get("subject", ""),
                "chapter": lesson.get("chapter", ""),
                "title": module.get("title", ""),
                "caption": module.get("caption", ""),
            }
    return index


def route_for(module):
    text = " ".join(str(module.get(k, "")) for k in ("title", "caption"))
    abstract = bool(ABSTRACT.search(text))
    real = bool(REAL_WORLD.search(text))
    process = bool(PROCESS.search(text))
    if abstract:
        route = "ORIGINAL_DIAGRAM"
        reason = "Abstract or symbolic concept is clearer as a controlled labelled teaching diagram."
    elif process:
        route = "ORIGINAL_DIAGRAM"
        reason = "A sequence or mechanism needs consistent step-by-step labels and arrows."
    elif real:
        route = "WEB_PHOTO_OR_ORIGINAL"
        reason = "A real object may benefit from a photo; use a verified open licence, otherwise draw an original."
    else:
        route = "HUMAN_REVIEW"
        reason = "Insufficient evidence to choose a visual source safely; inspect the teaching explanation."
    return route, reason


def audit(curriculum, manifest):
    modules = module_index(curriculum)
    mapped = Counter()
    errors = []
    for item in manifest.get("images", []):
        key = (str(item.get("lesson_id", "")), str(item.get("module_key", "")))
        if key not in modules:
            errors.append({"type": "unknown_mapping", "key": list(key), "title": item.get("title", "")})
            continue
        mapped[key] += 1
        step_ids = item.get("step_ids", [])
        if modules[key]["step_id"] not in step_ids:
            errors.append({"type": "step_id_mismatch", "key": list(key),
                           "expected": modules[key]["step_id"], "actual": step_ids})
    duplicate = [{"type": "duplicate_mapping", "key": list(k), "count": n}
                 for k, n in mapped.items() if n > 1]
    errors.extend(duplicate)
    queue = []
    for key, module in modules.items():
        if not mapped[key]:
            route, reason = route_for(module)
            queue.append({**module, "proposed_route": route, "reason": reason,
                          "status": "NEEDS_HUMAN_REVIEW"})
    by_subject = Counter(m["subject"] for m in modules.values())
    mapped_by_subject = Counter(modules[k]["subject"] for k, n in mapped.items() if n)
    return {
        "summary": {
            "total_modules": len(modules), "mapped_modules": sum(1 for n in mapped.values() if n),
            "unmapped_modules": len(queue), "duplicate_mappings": len(duplicate),
            "mapping_errors": len(errors) - len(duplicate),
            "by_subject": {
                subject: {"total": total, "mapped": mapped_by_subject[subject],
                          "unmapped": total - mapped_by_subject[subject]}
                for subject, total in sorted(by_subject.items())
            },
        },
        "errors": errors, "review_queue": queue,
        "policy": "Suggestions are not approvals. No image is fetched, generated, ingested, or published by this audit.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curriculum", required=True, type=Path,
                        help="JSON export of approved lesson/module IDs and captions")
    parser.add_argument("--manifest", required=True, type=Path,
                        help="Current authoring-manifest.json")
    parser.add_argument("--out", default=Path("visual-audit.json"), type=Path)
    args = parser.parse_args()
    result = audit(load_json(args.curriculum), load_json(args.manifest))
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    if result["errors"]:
        raise SystemExit(f"Audit found {len(result['errors'])} mapping errors; see {args.out}")


if __name__ == "__main__":
    main()
