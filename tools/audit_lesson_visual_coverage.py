#!/usr/bin/env python3
"""Build one auditable, read-only visual lifecycle ledger for every lesson module.

Curriculum JSON is the authoritative inventory. Optional authoring, web-source,
decision, pending-ingestion and render-verification manifests are reconciled
against it. This tool never downloads, generates, uploads, approves or publishes.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REAL_WORLD = re.compile(
    r"\\b(plant|leaf|flower|animal|bird|insect|habitat|tool|instrument|"
    r"food|grain|fruit|vegetable|magnet|compass|thermometer|water|cloud|"
    r"rain|snow|soil|rock|stone|material|machine|vehicle|body part)\\b", re.I
)
ABSTRACT = re.compile(
    r"\\b(fractions?|angles?|geometry|symmetry|equations?|number line|integers?|"
    r"factor|multiple|prime|pattern|area|perimeter|ratio|graph|data|"
    r"measurement|construct|polygon|decimal)\\b", re.I
)
PROCESS = re.compile(
    r"\\b(cycle|process|stage|steps|evaporation|condensation|growth|"
    r"life cycle|separation|method|experiment|rotation|reflection)\\b", re.I
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def records(document, key):
    if document is None:
        return []
    if isinstance(document, list):
        return document
    value = document.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array")
    return value


def module_index(curriculum):
    if isinstance(curriculum, dict):
        curriculum = curriculum.get("lessons", [])
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
    if ABSTRACT.search(text):
        return "ORIGINAL_DIAGRAM", "Abstract or symbolic concept is clearer as a labelled teaching diagram."
    if PROCESS.search(text):
        return "ORIGINAL_DIAGRAM", "A sequence or mechanism needs consistent step-by-step labels."
    if REAL_WORLD.search(text):
        return "WEB_PHOTO_OR_ORIGINAL", "A real object may benefit from a licensed photo; otherwise draw an original."
    return "HUMAN_REVIEW", "Inspect the teaching explanation before choosing a visual."


def _key(item):
    return str(item.get("lesson_id", "")), str(item.get("module_key", ""))


def _matches(index, items, kind, errors):
    matched = Counter()
    for item in items:
        key = _key(item)
        if key not in index:
            errors.append({"type": f"unknown_{kind}", "key": list(key)})
            continue
        matched[key] += 1
        step_ids = item.get("step_ids", [])
        if step_ids and index[key]["step_id"] not in step_ids:
            errors.append({"type": f"{kind}_step_id_mismatch", "key": list(key),
                           "expected": index[key]["step_id"], "actual": step_ids})
    for key, count in matched.items():
        if count > 1:
            errors.append({"type": f"duplicate_{kind}", "key": list(key), "count": count})
    return matched


def audit(curriculum, manifest, web_manifest=None, decision_ledger=None,
          ingestion_ledger=None, render_ledger=None):
    index = module_index(curriculum)
    errors = []
    authored = _matches(index, records(manifest, "images"), "authoring_mapping", errors)
    web = _matches(index, records(web_manifest, "images"), "web_candidate", errors)
    decisions = records(decision_ledger, "items")
    decision_by_key = {}
    for item in decisions:
        key = _key(item)
        if key not in index:
            errors.append({"type": "unknown_decision", "key": list(key)})
        elif key in decision_by_key:
            errors.append({"type": "duplicate_decision", "key": list(key)})
        else:
            decision_by_key[key] = item
    ingested = _matches(index, records(ingestion_ledger, "images"), "ingestion_record", errors)
    rendered = _matches(index, records(render_ledger, "images"), "render_record", errors)

    ledger = []
    for key, module in index.items():
        decision = decision_by_key.get(key, {})
        if rendered[key]:
            status = "RENDER_VERIFIED"
        elif ingested[key]:
            status = "INGESTED"
        elif authored[key]:
            status = "READY"
        elif web[key]:
            status = "NEEDS_REVIEW"
        else:
            route, _ = route_for(module)
            status = "NEEDS_ORIGINAL_PNG" if route == "ORIGINAL_DIAGRAM" else (
                "NEEDS_WEB_SOURCE" if route == "WEB_PHOTO_OR_ORIGINAL" else "NEEDS_REVIEW")
        proposed_route, reason = route_for(module)
        ledger.append({
            **module,
            "status": status,
            "proposed_route": decision.get("proposed_route", proposed_route),
            "decision_status": decision.get("decision_status"),
            "source_type": decision.get("source_type"),
            "reason": decision.get("reason", reason),
            "authoring_mapping_count": authored[key],
            "web_candidate_count": web[key],
            "ingestion_record_count": ingested[key],
            "render_verification_count": rendered[key],
        })

    by_subject = {}
    for subject in sorted({m["subject"] for m in ledger}):
        subset = [m for m in ledger if m["subject"] == subject]
        by_subject[subject] = {
            "total": len(subset),
            "by_status": dict(sorted(Counter(m["status"] for m in subset).items())),
        }
    counts = Counter(m["status"] for m in ledger)
    return {
        "summary": {
            "total_modules": len(ledger),
            "by_status": dict(sorted(counts.items())),
            "by_subject": by_subject,
            "mapping_errors": len(errors),
        },
        "modules": ledger,
        "errors": errors,
        "policy": "Read-only reconciliation. No asset is fetched, generated, ingested, approved, deployed or published.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curriculum", required=True, type=Path,
                        help="Authoritative curriculum JSON (array or object with lessons)")
    parser.add_argument("--manifest", required=True, type=Path, help="Authoring manifest")
    parser.add_argument("--web-manifest", type=Path)
    parser.add_argument("--decision-ledger", type=Path)
    parser.add_argument("--ingestion-ledger", type=Path,
                        help="Export of stored image records; expected images array")
    parser.add_argument("--render-ledger", type=Path,
                        help="Verified tutor-screen render records; expected images array")
    parser.add_argument("--out", default=Path("visual-coverage-ledger.json"), type=Path)
    args = parser.parse_args()
    result = audit(
        load_json(args.curriculum), load_json(args.manifest),
        load_json(args.web_manifest) if args.web_manifest else None,
        load_json(args.decision_ledger) if args.decision_ledger else None,
        load_json(args.ingestion_ledger) if args.ingestion_ledger else None,
        load_json(args.render_ledger) if args.render_ledger else None,
    )
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    if result["errors"]:
        raise SystemExit(f"Audit found {len(result['errors'])} reconciliation errors; see {args.out}")


if __name__ == "__main__":
    main()
