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
    ".engineering/tasks/active-work.md",
    ".github/testing-regression-checklist.md",
)
REQUIRED_AGENT_CONTRACT_MARKERS = (
    "## Closed-loop partner contract (mandatory)",
    "### 3. Execute a closed loop",
    "Maximum: five distinct repair generations",
    "### 4. Treat tests as a proof ladder",
    "### 6. Hard stop and approval boundaries",
    "A task is DONE only when its stated acceptance criteria pass and the evidence is recorded.",
    "Never merge PRs, deploy production, mutate production databases, publish/release publicly",
)

REPAIR_STATE_START = "<!-- padippupal-repair-state:start -->"
REPAIR_STATE_END = "<!-- padippupal-repair-state:end -->"
REPAIR_OUTCOMES = {"IN_PROGRESS", "PASS", "FAIL", "BLOCKED"}
REPAIR_CHAIN_STATUSES = {"OPEN", "RESOLVED", "ESCALATED"}
REQUIRED_PROCEED_BRIDGE_MARKERS = (
    "  issue_comment:",
    "  comment-proceed-cycle:",
    "github.event.comment.body == '/proceed'",
    "github.event.comment.user.login == github.repository_owner",
    "pr.user.login !== context.payload.repository.owner.login",
    "pr.head.repo.full_name !== context.payload.repository.full_name",
    "PROCEED_REF:",
    "PROCEED_SHA:",
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


def validate_proceed_bridge(root: pathlib.Path) -> list[str]:
    path = root / ".github" / "workflows" / "autopilot.yml"
    try:
        workflow = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ["missing or unreadable AutoPilot workflow for chat Proceed bridge"]
    errors = [f"AutoPilot Proceed bridge missing: {marker}"
              for marker in REQUIRED_PROCEED_BRIDGE_MARKERS if marker not in workflow]
    if workflow.count("  issue_comment:") != 1:
        errors.append("AutoPilot workflow must define exactly one issue_comment trigger")
    if workflow.count("  comment-proceed-cycle:") != 1:
        errors.append("AutoPilot workflow must define exactly one chat Proceed job")
    return errors


def validate_repair_state(root: pathlib.Path, approved_ledger: dict) -> list[str]:
    """Validate the persistent five-generation ledger embedded in active-work.md."""
    errors: list[str] = []
    path = root / ".engineering" / "tasks" / "active-work.md"
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ["missing or unreadable active-work handoff for repair state"]

    if content.count(REPAIR_STATE_START) != 1 or content.count(REPAIR_STATE_END) != 1:
        return ["active-work.md must contain exactly one repair-state marker block"]
    payload = content.split(REPAIR_STATE_START, 1)[1].split(REPAIR_STATE_END, 1)[0].strip()
    try:
        state = json.loads(payload)
    except json.JSONDecodeError as exc:
        return [f"invalid repair-generation state JSON: {exc}"]
    if not isinstance(state, dict):
        return ["repair-generation state must be a JSON object"]

    if state.get("schema_version") != 1:
        errors.append("repair-generation state schema_version must be 1")
    if state.get("max_generations") != MAX_REPAIR_GENERATIONS:
        errors.append("repair-generation state must enforce a maximum of five generations")
    chains = state.get("chains")
    if not isinstance(chains, list):
        return errors + ["repair-generation state chains must be an array"]

    seen_ids: set[str] = set()
    for chain in chains:
        if not isinstance(chain, dict):
            errors.append("each repair chain must be an object")
            continue
        chain_id = chain.get("id")
        if not isinstance(chain_id, str) or not chain_id or chain_id in seen_ids:
            errors.append("repair chain IDs must be present and unique strings")
        else:
            seen_ids.add(chain_id)
        for field in ("originating_run", "originating_sha", "task_id"):
            if not chain.get(field):
                errors.append(f"repair chain {chain_id or '<unknown>'} missing {field}")
        if chain.get("status") not in REPAIR_CHAIN_STATUSES:
            errors.append(f"repair chain {chain_id or '<unknown>'} has invalid status")
        if chain.get("task_id") and approved_task(chain["task_id"], approved_ledger) is None:
            errors.append(f"repair chain {chain_id or '<unknown>'} is outside approved work")
        generations = chain.get("generations")
        if not isinstance(generations, list):
            errors.append(f"repair chain {chain_id or '<unknown>'} generations must be an array")
            continue
        if len(generations) > MAX_REPAIR_GENERATIONS:
            errors.append(f"repair chain {chain_id or '<unknown>'} exceeds five repair generations")
        numbers = [item.get("number") for item in generations if isinstance(item, dict)]
        if numbers != list(range(1, len(generations) + 1)):
            errors.append(f"repair chain {chain_id or '<unknown>'} generations must be sequential from 1")
        for generation in generations:
            if not isinstance(generation, dict):
                errors.append(f"repair chain {chain_id or '<unknown>'} has a malformed generation")
                continue
            if not generation.get("hypothesis"):
                errors.append(f"repair chain {chain_id or '<unknown>'} generation lacks a hypothesis")
            if generation.get("outcome") not in REPAIR_OUTCOMES:
                errors.append(f"repair chain {chain_id or '<unknown>'} generation has invalid outcome")
            if generation.get("outcome") != "IN_PROGRESS" and not generation.get("verification_run"):
                errors.append(f"repair chain {chain_id or '<unknown>'} generation lacks verification_run")
            if generation.get("outcome") != "IN_PROGRESS" and not generation.get("commit_sha"):
                errors.append(f"repair chain {chain_id or '<unknown>'} generation lacks commit_sha")
        last_outcome = generations[-1].get("outcome") if generations and isinstance(generations[-1], dict) else None
        if chain.get("status") == "RESOLVED" and last_outcome != "PASS":
            errors.append(f"repair chain {chain_id or '<unknown>'} cannot resolve without a passing generation")
        if len(generations) == MAX_REPAIR_GENERATIONS and last_outcome != "PASS" and chain.get("status") != "ESCALATED":
            errors.append(f"repair chain {chain_id or '<unknown>'} must escalate after five unsuccessful generations")
    return errors


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

    agent_path = root / "AGENTS.md"
    try:
        agent_contract = agent_path.read_text(encoding="utf-8")
        for marker in REQUIRED_AGENT_CONTRACT_MARKERS:
            if marker not in agent_contract:
                errors.append(f"AGENTS.md missing closed-loop contract requirement: {marker}")
    except (OSError, UnicodeError):
        errors.append("missing or unreadable required guide: AGENTS.md")

    trigger_path = root / "docs" / "AUTOPILOT_TRIGGER_PROMPT.md"
    try:
        trigger_text = trigger_path.read_text(encoding="utf-8")
        for marker in REQUIRED_TRIGGER_CONTRACT:
            if marker not in trigger_text:
                errors.append(f"unified trigger contract is missing: {marker}")
    except (OSError, UnicodeError):
        errors.append("missing or unreadable unified trigger prompt")

    ledger: dict = {}
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
    errors.extend(validate_repair_state(root, ledger))
    errors.extend(validate_proceed_bridge(root))
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
    print("- Closed-loop contract markers are present in AGENTS.md (drift check only; not runtime enforcement)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
