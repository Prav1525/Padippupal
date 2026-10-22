#!/usr/bin/env python3
"""Fail fast when durable PadippuPal process records are missing or stale-shaped."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
required = {
    "DEVELOPMENT_PROTOCOL.md": [
        "New-chat / handoff startup checklist",
        "Definition of done",
        "Status report format",
    ],
    "PROJECT_STATE.md": [
        "Current objective",
        "Next task after protocol is established",
        "Session handoff template",
    ],
    "docs/REGRESSION_CHECKLIST.md": [
        "PP-TUTOR-001",
        "PP-TEST-001",
        "Repeat-failure protocol",
    ],
    "docs/DECISION_LOG.md": [
        "D-001",
        "D-005",
    ],
    ".github/NEW_CHAT_STARTER.md": [
        "Required startup actions",
        "PROJECT_STATE.md",
    ],
    ".github/pull_request_template.md": [
        "Observed behavior and evidence",
        "Root cause",
        "Acceptance criteria",
        "Verification evidence",
        "Project handoff",
    ],
}
errors = []
for name, markers in required.items():
    path = ROOT / name
    if not path.is_file():
        errors.append(f"Missing required process file: {name}")
        continue
    body = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker.casefold() not in body.casefold():
            errors.append(f"{name} is missing required section/marker: {marker}")

# For PRs, require a reviewable task description. The PR body is passed via env,
# not interpolated into shell source.
if os.getenv("GITHUB_EVENT_NAME") == "pull_request":
    body = os.getenv("PR_BODY", "")
    for heading in ("Purpose", "Scope", "Validation"):
        if heading.casefold() not in body.casefold():
            errors.append(f"Pull request description must include: {heading}")

if errors:
    print("PROJECT PROCESS GUARD: FAIL")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("PROJECT PROCESS GUARD: PASS")
print("Required durable process records, handoff prompt, PR template, and review metadata are present.")
print("This guard does not prove a developer read the protocol or that product behavior is correct.")
