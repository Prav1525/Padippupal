"""Safely apply reviewed Science translation patches to the existing approved synthesis.

Dry-run is the default. A database write requires both --apply and --reviewed.
The script never calls a translation model; all localized text comes from patch JSON.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ALLOWED_STEP_FIELDS = {"title", "caption", "teacher_says", "checkpoint"}
PATCH_ROOT = Path(__file__).with_name("science_translation_patches")


def apply_patch(source: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Overlay only localized learner-facing strings; preserve synthesis structure."""
    if str(source.get("id")) != str(patch.get("lesson_id")):
        raise ValueError("patch lesson_id does not match approved lesson")
    if str(source.get("chapter")) != str(patch.get("chapter")):
        raise ValueError("patch chapter does not match approved lesson")
    if str(source.get("subject", "")).casefold() != "science":
        raise ValueError("only Science lessons are supported")
    lesson = copy.deepcopy(source["lesson"])
    for field in ("chapter_title", "overview"):
        value = patch.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"patch requires non-empty {field}")
        lesson[field] = value
    objectives = patch.get("learning_objectives")
    if not isinstance(objectives, list) or len(objectives) != len(lesson.get("learning_objectives", [])):
        raise ValueError("learning_objectives must preserve the original list length")
    if any(not isinstance(item, str) or not item.strip() for item in objectives):
        raise ValueError("learning_objectives must contain non-empty strings")
    lesson["learning_objectives"] = objectives

    source_steps = lesson.get("teaching_sequence")
    patch_steps = patch.get("teaching_sequence")
    if not isinstance(source_steps, list) or not isinstance(patch_steps, list):
        raise ValueError("teaching_sequence must be a list in source and patch")
    source_ids = [str(item.get("id", "")) for item in source_steps]
    patch_ids = [str(item.get("id", "")) for item in patch_steps]
    if source_ids != patch_ids:
        raise ValueError("patch must preserve every teaching step ID and its order")
    for source_step, patch_step in zip(source_steps, patch_steps):
        if set(patch_step) - ({"id"} | ALLOWED_STEP_FIELDS):
            raise ValueError(f"unsupported patch fields for {patch_step.get('id')}")
        for field in ALLOWED_STEP_FIELDS:
            if field not in patch_step:
                continue
            value = patch_step[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{patch_step.get('id')}.{field} must be non-empty text")
            source_step[field] = value
    return lesson


def request_json(url: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"X-Admin-Token": token, "Accept": "application/json",
                                 "Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patch", type=Path, help="translation patch JSON file")
    parser.add_argument("--api-base", default=os.environ.get("PADIPPUPAL_API_BASE", "").rstrip("/"))
    parser.add_argument("--apply", action="store_true", help="POST the translation to the API")
    parser.add_argument("--reviewed", action="store_true", help="assert a human has reviewed this exact patch")
    parser.add_argument("--reviewer-note", default="")
    args = parser.parse_args()
    patch = json.loads(args.patch.read_text(encoding="utf-8"))
    if args.apply and not args.reviewed:
        parser.error("--apply requires --reviewed; unreviewed drafts must not be learner-approved")
    if args.apply and not args.reviewer_note.strip():
        parser.error("--apply requires --reviewer-note")
    if not args.api_base:
        parser.error("set PADIPPUPAL_API_BASE or pass --api-base")
    token = os.environ.get("PADIPPUPAL_ADMIN_TOKEN", "")
    if not token:
        parser.error("PADIPPUPAL_ADMIN_TOKEN is required; never put it in the patch or repository")

    lesson_id = str(patch["lesson_id"])
    source = request_json(f"{args.api_base}/admin/chapter-lessons/{lesson_id}", token)
    localized = apply_patch(source, patch)
    if not args.apply:
        print(json.dumps({"lesson_id": lesson_id, "chapter": patch["chapter"],
                          "language": patch["language"], "step_count": len(localized["teaching_sequence"]),
                          "mode": "dry-run", "database_write": False}, ensure_ascii=False))
        return 0
    result = request_json(
        f"{args.api_base}/admin/chapter-lessons/{lesson_id}/translations", token,
        {"language": patch["language"], "lesson": localized, "reviewed": True,
         "reviewer_note": args.reviewer_note},
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
