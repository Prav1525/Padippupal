#!/usr/bin/env python3
"""Write an always-run CI summary with the outcomes of each required test stage."""
import os
from pathlib import Path

stages = [
    ("JVM unit tests", os.getenv("JVM_TESTS_OUTCOME", "not-run")),
    ("APK build", os.getenv("APK_BUILD_OUTCOME", "not-run")),
    ("Smoke-script validation", os.getenv("SCRIPT_VALIDATION_OUTCOME", "not-run")),
    ("Android emulator end-to-end", os.getenv("EMULATOR_TEST_OUTCOME", "not-run")),
]
run_url = (
    f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/"
    f"{os.getenv('GITHUB_REPOSITORY', 'unknown/unknown')}/actions/runs/"
    f"{os.getenv('GITHUB_RUN_ID', 'unknown')}"
)
lines = [
    "# PadippuPal test run",
    "",
    f"- Commit: `{os.getenv('GITHUB_SHA', 'unknown')}`",
    f"- Run: {run_url}",
    "",
    "| Stage | Outcome |",
    "|---|---|",
]
lines.extend(f"| {name} | **{outcome}** |" for name, outcome in stages)
failed = [(name, outcome) for name, outcome in stages if outcome in ("failure", "cancelled", "timed_out")]
lines += ["", "## Result"]
if failed:
    lines += [
        "**FAILURE — do not merge.**",
        "",
        "Failed or interrupted stages:",
        *[f"- {name}: {outcome}" for name, outcome in failed],
        "",
        "Inspect this run's step logs and the padippupal-emulator-ui artifact. Record root cause, fix commit, and regression test in docs/TEST_FAILURE_REGISTER.md.",
    ]
else:
    lines += [
        "No stage reported failure. This summary alone is not acceptance: confirm the emulator log includes all diary crop, rescan, save, and planner assertions.",
    ]
report = "\n".join(lines) + "\n"
Path("test-failure-report.md").write_text(report, encoding="utf-8")
summary = os.getenv("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a", encoding="utf-8") as handle:
        handle.write(report)
print(report, end="")
