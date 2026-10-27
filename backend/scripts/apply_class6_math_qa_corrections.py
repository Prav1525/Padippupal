#!/usr/bin/env python3
"""Apply reviewed Class 6 Maths QA edits through the authenticated API only.

Required environment:
  PADIPPUPAL_ADMIN_TOKEN  Admin token (never put it in source control)
Optional:
  PADIPPUPAL_API_BASE     Defaults to the production curriculum API

The script is dry-run by default. Pass --apply to send PUT requests. It never
writes to the database directly and never approves/publishes lessons.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

API_BASE = os.getenv(
    "PADIPPUPAL_API_BASE",
    "https://padippupal-curriculum-api.onrender.com",
).rstrip("/")
LESSONS = {
    "Fractions": "7d37ec27-d7c0-5e19-92ff-0c64b8ad9c6f",
    "Data Handling and Presentation": "cd2cb3fe-e0ad-5c40-87e2-8954a5c97169",
    "Perimeter and Area": "909ef146-0db1-5070-b774-f026b4d03277",
}


class QAError(RuntimeError):
    pass


def api_request(path: str, token: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_BASE + path,
        data=data,
        method=method,
        headers={
            "X-Admin-Token": token,
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if data is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise QAError(f"{method} {path} returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise QAError(f"{method} {path} failed: {exc.reason}") from exc
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise QAError(f"{method} {path} returned non-JSON data") from exc
    if not isinstance(result, dict):
        raise QAError(f"{method} {path} returned an unexpected response shape")
    return result


def step_by_title(lesson: dict[str, Any], title: str) -> dict[str, Any]:
    steps = lesson.get("teaching_sequence")
    if not isinstance(steps, list):
        raise QAError("lesson teaching_sequence is missing")
    matches = [step for step in steps if isinstance(step, dict) and step.get("title") == title]
    if len(matches) != 1:
        raise QAError(f"expected exactly one step titled {title!r}; found {len(matches)}")
    return matches[0]


def revise_lesson(chapter: str, lesson: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Make narrowly-scoped, expected-text-guarded edits; preserve all source citations."""
    import copy

    updated = copy.deepcopy(lesson)
    changes: list[str] = []

    if chapter == "Fractions":
        step = step_by_title(updated, "Parts of a Whole and Reading Fractions")
        visual = step.get("visual")
        if not isinstance(visual, dict):
            raise QAError("Fractions chikki visual recipe is missing")
        if "6 equal parts" not in str(step.get("teacher_says", "")):
            raise QAError("Fractions chikki teacher narration no longer matches the expected draft")
        if "3 equal pieces" not in str(visual.get("narration_sync", "")):
            raise QAError("Fractions chikki visual no longer matches the expected draft")
        visual["narration_sync"] = "Show one whole chikki divided into 6 equal pieces; each piece is 1/6 of the whole."
        changes.append("align chikki visual with six equal parts")

        step = step_by_title(updated, "Marking Fractions on the Number Line")
        visual = step.get("visual")
        if not isinstance(visual, dict) or "5 equal parts" not in str(visual.get("narration_sync", "")):
            raise QAError("Fractions number-line visual no longer matches the expected draft")
        visual["narration_sync"] = "First divide the interval from 0 to 1 into 2 equal parts and mark 1/2; then show 3 equal parts and mark 1/3 and 2/3."
        changes.append("align number-line visual with halves and thirds")

        step = step_by_title(updated, "History of Fractions and Unit Fraction Puzzles")
        old = str(step.get("teacher_says", ""))
        if "Ancient texts used notation very similar to ours." not in old:
            raise QAError("Fractions history narration no longer matches the expected draft")
        step["teacher_says"] = (
            "Fractions have a rich history in India. The cited Rig Veda passage uses the expression "
            "'tri-pada', associated here with a three-quarter idea. Later, mathematicians such as "
            "Brahmagupta (628 CE) described rules for arithmetic with fractions. These are distinct "
            "historical contexts; do not assume the ancient expression used modern fraction notation. "
            "We can also explore a unit-fraction puzzle: 1/2 + 1/3 + 1/6 = 1."
        )
        changes.append("separate Rig Veda reference from Brahmagupta and remove unsupported notation claim")

    elif chapter == "Data Handling and Presentation":
        step = step_by_title(updated, "Organising Data and Tally Marks")
        old = str(step.get("teacher_says", ""))
        if "crossed every fifth mark as ||||" not in old:
            raise QAError("Tally narration no longer matches the expected draft")
        step["teacher_says"] = (
            "When a raw list is hard to read, tally marks help us count each category. "
            "To show five items, draw four vertical strokes and cross them with a fifth diagonal stroke. "
            "The count of each category is called its frequency."
        )
        visual = step.get("visual")
        if not isinstance(visual, dict):
            raise QAError("Tally visual recipe is missing")
        visual["actions"] = ["Draw four vertical tally strokes, then cross the group with a fifth diagonal stroke"]
        visual["narration_sync"] = ["The fifth tally is a diagonal stroke across the previous four, making one group of five."]
        changes.append("correct the five-mark tally recipe")

        step = step_by_title(updated, "Warm-up: What is Data?")
        visual = step.get("visual")
        if not isinstance(visual, dict) or visual.get("type") != "none":
            raise QAError("Data warm-up visual no longer matches the expected draft")
        visual.update({
            "type": "table",
            "objects": ["Classmates", "Favourite colours", "Tally column"],
            "actions": ["Ask a small group about favourite colours", "Record one response per tally", "Count the tallies"],
            "narration_sync": ["Collect a few classmates' answers, record each response, and count the results as data."],
        })
        changes.append("add a simple data-collection visual to the warm-up")

    elif chapter == "Perimeter and Area":
        step = step_by_title(updated, "Tracks, Estimations, and Straight vs. Diagonal Units")
        old = str(step.get("teacher_says", ""))
        expected = "a diagonal line is longer than a straight grid unit!"
        if expected not in old:
            raise QAError("Diagonal-unit narration no longer matches the expected draft")
        step["teacher_says"] = old.replace(
            expected,
            "a diagonal across one unit square is longer than one side of that square. "
            "This comparison applies to that square; compare actual lengths rather than assuming "
            "every diagonal is longer than every straight grid segment.",
        )
        changes.append("limit the diagonal-length statement to a unit square")

        step = step_by_title(updated, "Area of Triangles and Composite Shapes")
        old = str(step.get("teacher_says", ""))
        expected = "Therefore, the area of a triangle is always half the area of the corresponding rectangle (or half of base times height)."
        if expected not in old:
            raise QAError("Triangle-area narration no longer matches the expected draft")
        step["teacher_says"] = old.replace(
            expected,
            "So a triangle's area is half the area of a rectangle with the same base and corresponding "
            "perpendicular height: area = 1/2 × base × height.",
        )
        changes.append("clarify triangle area uses the same base and corresponding perpendicular height")

    else:
        raise QAError(f"no correction recipe for chapter {chapter!r}")

    return updated, changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="send changes; without this flag only preview")
    args = parser.parse_args()
    token = os.getenv("PADIPPUPAL_ADMIN_TOKEN", "").strip()
    if not token:
        print("ERROR: PADIPPUPAL_ADMIN_TOKEN must be set in this secure environment.", file=sys.stderr)
        return 2

    for chapter, lesson_id in LESSONS.items():
        detail = api_request(f"/admin/chapter-lessons/{lesson_id}", token)
        if str(detail.get("status", "")).lower() != "draft":
            raise QAError(f"{chapter}: expected draft status; found {detail.get('status')!r}; refusing to edit")
        lesson = detail.get("lesson")
        if not isinstance(lesson, dict):
            raise QAError(f"{chapter}: admin detail response did not include a lesson object")
        updated, changes = revise_lesson(chapter, lesson)
        print(f"{chapter} ({lesson_id})")
        for change in changes:
            print(f"  - {change}")
        if args.apply:
            result = api_request(
                f"/admin/chapter-lessons/{lesson_id}/content",
                token,
                method="PUT",
                body={
                    "lesson": updated,
                    "feedback": "Targeted Class 6 Maths content QA corrections applied; source-based human review still required.",
                },
            )
            if result.get("status") != "draft" or not result.get("review_required"):
                raise QAError(f"{chapter}: API did not confirm draft/review-required status: {result}")
            print("  SAVED as draft; validation:", json.dumps(result.get("validation", {}), ensure_ascii=False))
        else:
            print("  DRY RUN — no changes sent")

    if not args.apply:
        print("\nPreview only. Re-run with --apply from a trusted environment to save via the authenticated API.")
    else:
        print("\nAll requested corrections saved as drafts. No lesson was approved or published.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QAError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
