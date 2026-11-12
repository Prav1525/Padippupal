#!/usr/bin/env python3
"""Bounded local Codex executor for the existing PadippuPal Proceed workflow."""
from __future__ import annotations
import argparse, datetime as dt, json, pathlib, re, shutil, subprocess, sys, tempfile
from typing import Sequence
from padippupal_autopilot import approved_task, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "approved-work.json"
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
SENSITIVE_NAMES = {"auth.json", "credentials.json", "secrets.json"}

class PreflightError(RuntimeError):
    pass

def git(root: pathlib.Path, *args: str, capture: bool = True):
    return subprocess.run(["git", *args], cwd=root, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None, check=False)

def current_branch(root: pathlib.Path = ROOT) -> str:
    result = git(root, "branch", "--show-current")
    if result.returncode:
        raise PreflightError(result.stderr.strip() or "Could not read current Git branch.")
    return result.stdout.strip()

def ensure_clean_repository(root: pathlib.Path = ROOT) -> None:
    result = git(root, "status", "--porcelain")
    if result.returncode:
        raise PreflightError(result.stderr.strip() or "Could not inspect Git working tree.")
    if result.stdout.strip():
        raise PreflightError("Working tree is not clean. Preserve existing changes before starting; the runner will not overwrite them.")

def ensure_policy(root: pathlib.Path = ROOT) -> None:
    errors = validate(root)
    if errors:
        raise PreflightError("AutoPilot policy validation failed:\n- " + "\n- ".join(errors))

def load_ledger(path: pathlib.Path = LEDGER) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightError(f"Could not read approved-work ledger: {exc}") from exc
    if not isinstance(value, dict):
        raise PreflightError("Approved-work ledger must contain a JSON object.")
    return value

def active_task_id(root: pathlib.Path = ROOT) -> str:
    """Read the ledger task ID from the first canonical current-objective section."""
    path = root / ".engineering" / "tasks" / "active-work.md"
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PreflightError(f"Could not read active-work handoff: {exc}") from exc
    sections = list(re.finditer(r"^## .*— current objective\s*$([\s\S]*?)(?=^## |\Z)", content, re.MULTILINE))
    if len(sections) != 1:
        raise PreflightError(
            f"active-work.md must identify exactly one current objective; found {len(sections)}."
        )
    task = re.search(r"Ledger task:\s*\x60([^\x60]+)\x60", sections[0].group(1))
    if not task:
        raise PreflightError("The current active-work objective has no explicit approved ledger task ID.")
    return task.group(1)


def require_approved_task(task_id: str | None, ledger: dict) -> None:
    if task_id and approved_task(task_id, ledger) is None:
        raise PreflightError(f"Task {task_id!r} is not explicitly APPROVED in docs/approved-work.json.")

def check_codex_auth(runner=subprocess.run) -> str:
    resolved = shutil.which("codex")
    if not resolved:
        raise PreflightError("Codex CLI was not found on PATH.")
    result = runner([resolved, "login", "status"], text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    detail = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0 or "logged in" not in detail.lower():
        raise PreflightError("Codex CLI does not report an authenticated session. Run codex login locally; never share credentials or auth files.")
    return resolved

def preflight(root: pathlib.Path = ROOT, task_id: str | None = None, runner=subprocess.run) -> str:
    if not (root / ".git").exists():
        raise PreflightError("The current directory is not the PadippuPal Git repository.")
    ensure_clean_repository(root)
    ensure_policy(root)
    ledger = load_ledger(root / "docs" / "approved-work.json")
    active_id = active_task_id(root)
    if task_id and task_id != active_id:
        raise PreflightError(f"Requested task {task_id!r} does not match current active objective {active_id!r}.")
    require_approved_task(active_id, ledger)
    return check_codex_auth(runner=runner)

def make_branch_name(now: dt.datetime | None = None) -> str:
    instant = now or dt.datetime.now(dt.timezone.utc)
    stamp = instant.astimezone(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"agent/local-proceed-{stamp}"

def build_codex_command(codex_path: str, root: pathlib.Path, output_path: pathlib.Path,
                        prompt: str) -> list[str]:
    # Keep terminal stdin available for on-request approvals.
    return [codex_path, "exec", "--cd", str(root), "--sandbox", "workspace-write",
            "--ask-for-approval", "on-request", "--json", "--output-last-message",
            str(output_path), prompt]

def build_prompt(task_id: str | None = None) -> str:
    task_line = (f"Requested approved task ID: {task_id}. Verify that this exact task remains APPROVED."
                 if task_id else "Select only the current active objective explicitly APPROVED in docs/approved-work.json.")
    return f"""You are the local coding executor for the existing PadippuPal repository.
{task_line}

MANDATORY BEFORE ACTION:
1. Read AGENTS.md and TESTING_GUIDANCE.md in full.
2. Read PROJECT_CHARTER.md, PROJECT_STATUS.md, .engineering/README.md, and relevant architecture, decisions, known issues and acceptance criteria.
3. Read docs/approved-work.json, .engineering/tasks/active-work.md, docs/TESTING_ERRORS.md, TEST_INVESTIGATION.md, docs/TEST_FAILURE_REGISTER.md and .github/testing-regression-checklist.md where present and relevant.
4. Reconcile actual Git branch/SHA, active PRs and exact CI evidence available locally or through already configured repository tooling. Treat dated notes as snapshots.
5. If the requested work is not explicitly approved or the active objective is ambiguous, stop and report BLOCKED. Do not invent or broaden a task.

EXECUTION:
- Work only on the one approved active objective and its acceptance criteria.
- Follow AGENTS.md and re-read TESTING_GUIDANCE.md before each distinct edit or test batch.
- Make the smallest evidence-supported change. Run relevant tests and preserve all assertions.
- Maintain the existing machine-readable repair state in .engineering/tasks/active-work.md. Count distinct repair hypotheses, not commands. Never exceed five generations for one failure chain; carry the same chain across branches and sessions.
- Record exact changed files, test commands, outcomes and remaining uncertainty in the existing handoff/investigation records. Distinguish PASS, FAIL, BLOCKED, NOT RUN and UNVERIFIED.
- If a required test environment, permission, credential or approval is missing, stop and report the precise blocker.

HARD SAFETY BOUNDARIES:
- Never merge a PR, push commits/branches, deploy, publish, release, write production data, run destructive migrations, delete user data, or weaken security/approval controls.
- Never use danger-full-access, --yolo, or any approval-bypass option.
- Do not access production systems or request/store production credentials.
- Do not spend paid API budget. Use only the already authenticated local Codex ChatGPT session.
- Do not modify unrelated tasks, create a second agent/ledger/trigger, or reset repair-generation state.

DELIVERABLE:
Implement and test only the approved active objective. Leave changes uncommitted on this isolated working branch. Return a concise evidence report with exact SHA, files, commands and test results. The wrapper creates a local patch; do not push or open a PR yourself.
"""

def changed_paths(root: pathlib.Path = ROOT) -> list[str]:
    result = git(root, "diff", "--name-only", "HEAD")
    if result.returncode:
        raise PreflightError(result.stderr.strip() or "Could not inspect changed paths.")
    return [line for line in result.stdout.splitlines() if line.strip()]

def is_sensitive_path(path: str) -> bool:
    candidate = pathlib.PurePosixPath(path)
    parts = {part.lower() for part in candidate.parts}
    return (candidate.name.lower() in SENSITIVE_NAMES or candidate.suffix.lower() in SENSITIVE_SUFFIXES
            or candidate.name.lower().startswith(".env")
            or bool(parts & {"secrets", "credentials", "private_keys"}))

def include_untracked_files(root: pathlib.Path = ROOT) -> None:
    result = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if result.returncode:
        raise PreflightError(result.stderr.strip() or "Could not list untracked files.")
    paths = [item for item in result.stdout.split("\0") if item]
    if paths:
        add = git(root, "add", "-N", "--", *paths)
        if add.returncode:
            raise PreflightError(add.stderr.strip() or "Could not include new files in patch.")

def collect_patch(root: pathlib.Path = ROOT, branch: str = "local-proceed") -> pathlib.Path | None:
    include_untracked_files(root)
    paths = changed_paths(root)
    sensitive = [path for path in paths if is_sensitive_path(path)]
    if sensitive:
        raise PreflightError("Sensitive paths changed; patch export blocked: " + ", ".join(sensitive))
    check = git(root, "diff", "--check", "HEAD")
    if check.returncode:
        raise PreflightError("git diff --check failed:\n" + check.stdout + check.stderr)
    diff = git(root, "diff", "--binary", "HEAD")
    if diff.returncode:
        raise PreflightError(diff.stderr.strip() or "Could not generate patch.")
    if not diff.stdout:
        return None
    destination = pathlib.Path(tempfile.gettempdir()) / f"padippupal-{branch.replace('/', '-')}.patch"
    destination.write_text(diff.stdout, encoding="utf-8")
    return destination

def safety_test_commands(root: pathlib.Path = ROOT) -> list[list[str]]:
    """Return deterministic repository policy/unit checks run after every Codex turn."""
    py = sys.executable
    return [
        [py, "-m", "py_compile",
         "tools/padippupal_autopilot.py", "tools/test_padippupal_autopilot.py",
         "tools/padippupal_proceed_controller.py", "tools/test_padippupal_proceed_controller.py",
         "tools/padippupal_local_executor.py", "tools/test_padippupal_local_executor.py"],
        [py, "tools/padippupal_autopilot.py", "validate"],
        [py, "tools/test_padippupal_autopilot.py"],
        [py, "tools/test_padippupal_proceed_controller.py"],
        [py, "tools/test_padippupal_local_executor.py"],
    ]


def run_safety_checks(root: pathlib.Path = ROOT, runner=subprocess.run) -> list[dict]:
    """Run the mandatory AutoPilot safety suite and retain complete command evidence."""
    # Re-open the canonical test/build instructions before this test batch.
    guidance = root / "TESTING_GUIDANCE.md"
    if not guidance.is_file() or not guidance.read_text(encoding="utf-8").strip():
        raise PreflightError("TESTING_GUIDANCE.md is missing or unreadable; safety tests not run.")
    results = []
    for command in safety_test_commands(root):
        result = runner(command, cwd=root, text=True, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, check=False)
        results.append({
            "command": command,
            "returncode": result.returncode,
            "output": result.stdout or "",
        })
    return results


def run_proceed(task_id: str | None = None, root: pathlib.Path = ROOT, runner=subprocess.run) -> int:
    try:
        effective_task_id = task_id or active_task_id(root)
        codex_path = preflight(root, effective_task_id, runner=runner)
        branch = make_branch_name()
        switched = git(root, "switch", "-c", branch)
        if switched.returncode:
            raise PreflightError(switched.stderr.strip() or f"Could not create branch {branch}.")
        print(f"Branch: {branch}")
        print(f"Codex: {codex_path}")
        print("Sandbox: workspace-write | approvals: on-request")
        output = pathlib.Path(tempfile.gettempdir()) / f"padippupal-{branch.replace('/', '-')}-summary.md"
        result = runner(build_codex_command(codex_path, root, output, build_prompt(effective_task_id)),
                        cwd=root, text=True, check=False)
        checks = run_safety_checks(root, runner=runner)
        with output.open("a", encoding="utf-8") as report:
            report.write("\n\n## Wrapper safety checks\n")
            for item in checks:
                report.write(f"\n- {'PASS' if item['returncode'] == 0 else 'FAIL'}: "
                             + " ".join(item["command"]) + "\n")
                report.write(item["output"] + "\n")
        patch = collect_patch(root, branch)
        paths = changed_paths(root)
        failed_checks = [item for item in checks if item["returncode"] != 0]
        with output.open("a", encoding="utf-8") as report:
            report.write("\nChanged files:\n")
            report.write("\n".join(f"- {path}" for path in paths) if paths else "- none")
            report.write("\n\nDiff check: PASS\n")
        print(f"Codex exit code: {result.returncode}")
        print(f"Wrapper safety checks: {'PASS' if not failed_checks else 'FAIL'} ({len(checks)} commands)")
        print("Changed files: " + (", ".join(paths) if paths else "none"))
        print("git diff --check: PASS")
        print(f"Execution summary: {output if output.exists() else 'not produced'}")
        if output.exists():
            print("\n===== Codex and safety-check report =====")
            print(output.read_text(encoding="utf-8"))
            print("===== End report =====")
        print(f"Patch: {patch if patch else 'no repository changes produced'}")
        print("No commit, push, PR, merge, deployment or production operation was performed.")
        return result.returncode if result.returncode else (1 if failed_checks else 0)
    except PreflightError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the existing PadippuPal Proceed task through local Codex.")
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight", help="Check repository, policy, task and Codex authentication without editing.")
    pre.add_argument("--task-id")
    run = sub.add_parser("proceed", help="Execute one approved active objective through local Codex.")
    run.add_argument("--task-id", help="Optional exact task ID; must be APPROVED in docs/approved-work.json.")
    args = parser.parse_args(argv)
    if args.command == "preflight":
        try:
            codex = preflight(ROOT, args.task_id)
            print("PREFLIGHT: PASS")
            print(f"Repository: {ROOT}")
            print(f"Current branch: {current_branch(ROOT)}")
            print(f"Active approved task: {active_task_id(ROOT)}")
            print(f"Codex: {codex}")
            print("Policy validator: PASS")
            return 0
        except PreflightError as exc:
            print(f"PREFLIGHT: BLOCKED — {exc}", file=sys.stderr)
            return 2
    return run_proceed(args.task_id)

if __name__ == "__main__":
    raise SystemExit(main())
