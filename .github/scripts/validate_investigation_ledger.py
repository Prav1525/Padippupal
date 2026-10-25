#!/usr/bin/env python3
"""Require durable investigation records for code-changing pull requests."""
from pathlib import Path
import os
import re
import subprocess
import sys

REQUIRED_FILES = ("AGENTS.md", "TESTING_GUIDANCE.md", "TEST_INVESTIGATION.md")
REQUIRED_LEDGER_MARKERS = (
    "Append-only attempt log",
    "Result:",
    "Root cause",
    "Evidence",
    "Next action",
)
CODE_SUFFIXES = {".py", ".kt", ".kts", ".java", ".xml", ".gradle", ".yml", ".yaml", ".sh", ".js", ".ts", ".tsx", ".json"}
CODE_PREFIXES = ("app/", "backend/", "server/", "scripts/", ".github/workflows/", ".github/scripts/")

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def main():
    base = os.environ.get("BASE_SHA")
    head = os.environ.get("HEAD_SHA")
    if not base or not head:
        print("BLOCKED: BASE_SHA and HEAD_SHA are required.")
        return 2
    changed = run("git", "diff", "--name-only", "--diff-filter=ACMR", base, head).splitlines()
    code_changed = [p for p in changed if p.endswith(tuple(CODE_SUFFIXES)) or p.startswith(CODE_PREFIXES)]
    print(f"Changed files: {len(changed)}; code/config files: {len(code_changed)}")
    if not code_changed:
        print("PASS: no code/config changes; investigation-ledger gate not applicable.")
        return 0

    missing = [p for p in REQUIRED_FILES if not Path(p).is_file()]
    if missing:
        print("FAIL: missing required guidance/ledger file(s): " + ", ".join(missing))
        return 1

    ledger_changed = "TEST_INVESTIGATION.md" in changed
    if not ledger_changed:
        print("FAIL: code/config changed but TEST_INVESTIGATION.md was not updated in this PR.")
        return 1

    ledger = Path("TEST_INVESTIGATION.md").read_text(encoding="utf-8")
    absent = [marker for marker in REQUIRED_LEDGER_MARKERS if marker.lower() not in ledger.lower()]
    if absent:
        print("FAIL: investigation ledger is missing required fields: " + ", ".join(absent))
        return 1

    # A template placeholder must not count as a real investigation entry.
    entries = re.findall(r"(?ms)^### (20\d{2}-\d{2}-\d{2}) — (.+?)\n(.*?)(?=^### |\Z)", ledger)
    real_entries = []
    for date, title, body in entries:
        if title.strip() in {"Short test/change description", "Short description"}:
            continue
        if not re.search(r"(?im)^- \*\*Result:\*\* (PASS|FAIL|BLOCKED|UNVERIFIED)\b", body):
            continue
        if not re.search(r"(?im)^- \*\*Evidence", body):
            continue
        if not re.search(r"(?im)^- \*\*Next action", body):
            continue
        real_entries.append((date, title))
    if not real_entries:
        print("FAIL: append a real dated attempt with an explicit result, evidence, and next action; the template placeholder does not count.")
        return 1

    print("PASS: guidance exists and the investigation ledger contains a dated attempt with outcome, evidence, and next action.")
    print("NOTE: this gate checks documentation completeness, not whether the diagnosis or test claims are true.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
