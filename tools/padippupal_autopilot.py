#!/usr/bin/env python3
"""Shared deterministic policy helpers for the existing PadippuPal AutoPilot."""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
APPROVED_WORK = ROOT / "docs" / "approved-work.json"
MAX_REPAIR_GENERATIONS = 5
REQUIRED_TRIGGER_CONTRACT = (
    "Same-invocation operating contract",
    "Engineering OS lane (orchestrator)",
    "AutoPilot lane (execution and quality subsystem)",
    "One shared state",
    "one coordinated cycle",
)
REQUIRED_GUIDES = (
    "TESTING_GUIDANCE.md",
    "TEST_INVESTIGATION.md",
    "docs/TESTING_ERRORS.md",
    "docs/TEST_FAILURE_REGISTER.md",
    "docs/AUTOPILOT_TRIGGER_PROMPT.md",
    ".github/testing-regression-checklist.md",
)

SIGNATURES = (
    ("runner_infrastructure", ("runner lost communication", "hosted runner", "502 bad gateway", "503 service unavailable")),
    ("dependency_or_network", ("connection reset by peer", "temporary failure resolving", "429 too many requests", "read timed out")),
    ("android_build_or_test", ("execution failed for task", "assertionerror", "tests failed", "compilation error")),
    ("emulator_or_adb", ("adb: device offline", "emulator-5554 offline", "failed to launch emulator", "device still booting")),
)


def classify_log(text: str) -> tuple[str, str]:
    lowered = text.lower()
    for category, needles in SIGNATURES:
        matches = [needle for needle in needles if needle in lowered]
        if matches:
            return category, ", ".join(matches[:3])
    return "unknown_requires_review", "No allowlisted signature matched; diagnosis required."


def next_generation(current: int) -> int | None:
    """Return next distinct patch generation, or None after the five-generation cap."""
    if current < 0:
        raise ValueError("generation count cannot be negative")
    return current + 1 if current < MAX_REPAIR_GENERATIONS else None


def approved_task(task_id: str, ledger: dict) -> dict | None:
    """Only exact, explicitly APPROVED task IDs are eligible for autonomous work."""
    for item in ledger.get("tasks", []):
        if item.get("id") == task_id and item.get("status") == "APPROVED":
            return item
    return None


def validate(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_GUIDES:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required guide: {relative}")
        else:
            try:
                path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                errors.append(f"unreadable required guide: {relative}")

    trigger_path = root / "docs" / "AUTOPILOT_TRIGGER_PROMPT.md"
    if trigger_path.is_file():
        try:
            trigger_text = trigger_path.read_text(encoding="utf-8")
            for required in REQUIRED_TRIGGER_CONTRACT:
                if required not in trigger_text:
                    errors.append(f"unified trigger contract is missing: {required}")
        except (OSError, UnicodeError):
            errors.append("unified trigger prompt is unreadable")

    ledger_path = root / "docs" / "approved-work.json"
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if ledger.get("policy") != "approved-roadmap-only":
            errors.append("approved-work ledger policy must be approved-roadmap-only")
        if ledger.get("max_repair_generations") != MAX_REPAIR_GENERATIONS:
            errors.append("approved-work ledger must set max_repair_generations to 5")
        seen: set[str] = set()
        for item in ledger.get("tasks", []):
            task_id = item.get("id")
            if not task_id or task_id in seen:
                errors.append("approved-work task IDs must be present and unique")
            seen.add(task_id)
            if item.get("status") == "APPROVED" and not (
                item.get("scope") and item.get("acceptance_criteria") and item.get("approved_by")
            ):
                errors.append(f"approved task {task_id} lacks scope, acceptance criteria, or approver")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid approved-work ledger: {exc}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("AUTOPILOT POLICY CHECK: BLOCKED")
        for error in errors:
            print(f"- {error}")
        return 2
    print("AUTOPILOT POLICY CHECK: PASS")
    print(f"- Approved-roadmap-only ledger: {APPROVED_WORK.relative_to(ROOT)}")
    print(f"- Maximum distinct repair generations: {MAX_REPAIR_GENERATIONS}")
    print("- Required project guidance is present and readable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
