#!/usr/bin/env python3
"""Single-run coordinator for PadippuPal's existing GitHub Actions checks.

The controller dispatches each independent check once, checks for newly-created
runs during discovery, then monitors active test runs every five minutes. It
continues to later checks even if an earlier check fails. It records evidence; it does not repair source code.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

API_ROOT = "https://api.github.com"
POLL_INTERVAL_SECONDS = 60  # Fast lookup while waiting for a dispatched run to appear.
MONITOR_INTERVAL_SECONDS = 5 * 60  # Recheck active test runs every five minutes.
RUN_DISCOVERY_TIMEOUT_SECONDS = 300
DEFAULT_STAGE_TIMEOUT_SECONDS = 25 * 60

# Preserve this order: policy -> backend -> Android build -> deployed read-only
# API check -> emulator UI acceptance. A failed stage never suppresses a later
# independent stage.
PIPELINE_STAGES = (
    {"workflow": "investigation-guidance.yml", "name": "Investigation Guidance Gate",
     "timeout_seconds": 10 * 60, "inputs": {}},
    {"workflow": "curriculum-engine.yml", "name": "Curriculum Engine Tests",
     "timeout_seconds": DEFAULT_STAGE_TIMEOUT_SECONDS, "inputs": {}},
    {"workflow": "android.yml", "name": "Android APK",
     "timeout_seconds": DEFAULT_STAGE_TIMEOUT_SECONDS, "inputs": {"publish_release": "false"}},
    {"workflow": "deployed-api-smoke.yml", "name": "Deployed PadippuPal API Smoke Test",
     "timeout_seconds": DEFAULT_STAGE_TIMEOUT_SECONDS, "inputs": {}},
    {"workflow": "android-ui-smoke.yml", "name": "Android UI smoke test",
     "timeout_seconds": 40 * 60, "inputs": {}},
)


class GitHubActionsAPI:
    def __init__(self, token: str, repository: str) -> None:
        self.token = token
        self.repository = repository

    def request(self, method: str, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            API_ROOT + "/repos/" + self.repository + path,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + self.token,
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "PadippuPal-Proceed-Controller",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"GitHub API {method} {path} returned {exc.code}: {detail}") from exc


def _created_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _find_existing_run(api, workflow: str, ref: str, sha: str,
                        event: str) -> dict | None:
    """Find an exact-SHA run already started by the parent PR event."""
    query = urllib.parse.urlencode({
        "event": event,
        "branch": ref,
        "per_page": "20",
    })
    response = api.request(
        "GET", f"/actions/workflows/{urllib.parse.quote(workflow, safe='')}/runs?{query}"
    )
    candidates = [
        run for run in response.get("workflow_runs", [])
        if run.get("event") == event
        and run.get("head_sha") == sha
        and run.get("head_branch") == ref
    ]
    return max(candidates, key=lambda item: item["id"]) if candidates else None


def _find_dispatched_run(api, workflow: str, ref: str, sha: str,
                         dispatched_at: datetime) -> dict | None:
    query = urllib.parse.urlencode({
        "event": "workflow_dispatch",
        "branch": ref,
        "per_page": "20",
    })
    response = api.request(
        "GET", f"/actions/workflows/{urllib.parse.quote(workflow, safe='')}/runs?{query}"
    )
    candidates = [
        run for run in response.get("workflow_runs", [])
        if run.get("event") == "workflow_dispatch"
        and run.get("head_sha") == sha
        and run.get("head_branch") == ref
        and _created_at(run["created_at"]) >= dispatched_at - timedelta(seconds=15)
    ]
    return max(candidates, key=lambda item: item["id"]) if candidates else None


def run_stage(api, stage: dict, ref: str, sha: str, *,
              sleep: Callable[[float], None] = time.sleep,
              monotonic: Callable[[], float] = time.monotonic,
              now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
              reuse_event: str = "") -> dict:
    workflow = stage["workflow"]
    dispatched_at = now()
    run = None
    if reuse_event:
        try:
            run = _find_existing_run(api, workflow, ref, sha, reuse_event)
        except Exception as exc:
            return {"name": stage["name"], "workflow": workflow, "status": "lookup_error",
                    "detail": f"Could not inspect existing {reuse_event} run: {exc}"}

        # Main-push runs are started by GitHub for every matrix workflow.
        # Wait for the exact SHA to appear; never dispatch a duplicate or
        # accidentally test a newer main commit when coordinating a push.
        if not run and reuse_event == "push":
            discovery_deadline = monotonic() + RUN_DISCOVERY_TIMEOUT_SECONDS
            while monotonic() < discovery_deadline:
                try:
                    run = _find_existing_run(api, workflow, ref, sha, reuse_event)
                except Exception as exc:
                    return {"name": stage["name"], "workflow": workflow, "status": "lookup_error",
                            "detail": f"Could not discover exact push run: {exc}"}
                if run:
                    break
                sleep(min(POLL_INTERVAL_SECONDS, max(0, discovery_deadline - monotonic())))
            if not run:
                return {"name": stage["name"], "workflow": workflow, "status": "run_not_found",
                        "detail": "No exact-SHA push run appeared within five minutes; duplicate dispatch was intentionally refused."}

    if run:
        # Reuse the exact-commit run already triggered by the PR; never create
        # a duplicate build/emulator job for the same SHA.
        pass
    else:
        try:
            api.request("POST", f"/actions/workflows/{urllib.parse.quote(workflow, safe='')}/dispatches",
                        {"ref": ref, "inputs": stage.get("inputs", {})})
        except Exception as exc:  # keep the coordinated cycle moving for later stages
            return {"name": stage["name"], "workflow": workflow, "status": "dispatch_error",
                    "detail": str(exc)}

        discovery_deadline = monotonic() + RUN_DISCOVERY_TIMEOUT_SECONDS
        while monotonic() < discovery_deadline:
            try:
                run = _find_dispatched_run(api, workflow, ref, sha, dispatched_at)
            except Exception as exc:
                return {"name": stage["name"], "workflow": workflow, "status": "lookup_error",
                        "detail": str(exc)}
            if run:
                break
            sleep(min(POLL_INTERVAL_SECONDS, max(0, discovery_deadline - monotonic())))

    if not run:
        return {"name": stage["name"], "workflow": workflow, "status": "run_not_found",
                "detail": "Dispatch accepted but no matching run appeared within five minutes."}

    run_id = run["id"]
    run_url = run.get("html_url", "")
    deadline = monotonic() + stage.get("timeout_seconds", DEFAULT_STAGE_TIMEOUT_SECONDS)
    while monotonic() < deadline:
        try:
            current = api.request("GET", f"/actions/runs/{run_id}")
        except Exception as exc:
            return {"name": stage["name"], "workflow": workflow, "run_id": run_id,
                    "url": run_url, "status": "status_lookup_error", "detail": str(exc)}
        if current.get("status") == "completed":
            return {"name": stage["name"], "workflow": workflow, "run_id": run_id,
                    "url": current.get("html_url", run_url),
                    "status": current.get("conclusion") or "unknown"}
        sleep(min(MONITOR_INTERVAL_SECONDS, max(0, deadline - monotonic())))

    return {"name": stage["name"], "workflow": workflow, "run_id": run_id,
            "url": run_url, "status": "timed_out",
            "detail": f"Still not completed after {stage.get('timeout_seconds', DEFAULT_STAGE_TIMEOUT_SECONDS)} seconds."}


def run_pipeline(api, ref: str, sha: str, *,
                 stages=PIPELINE_STAGES,
                 sleep: Callable[[float], None] = time.sleep,
                 monotonic: Callable[[], float] = time.monotonic,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 reuse_event: str = "",
                 emit: Callable[[str], None] = print) -> list[dict]:
    """Dispatch and monitor every independent workflow concurrently.

    Results retain the declared matrix order even though each stage dispatches
    and polls independently. A failed stage never cancels another stage.
    """
    if not stages:
        return []
    for index, stage in enumerate(stages, start=1):
        emit(f"[{index}/{len(stages)}] Starting {stage['name']} on {ref}@{sha}")

    def execute(stage):
        return run_stage(api, stage, ref, sha, sleep=sleep,
                         monotonic=monotonic, now=now, reuse_event=reuse_event)

    with ThreadPoolExecutor(max_workers=len(stages),
                            thread_name_prefix="padippupal-check") as pool:
        futures = [pool.submit(execute, stage) for stage in stages]
        results = [future.result() for future in futures]

    for index, result in enumerate(results, start=1):
        emit(f"[{index}/{len(results)}] {result['name']}: {result['status']}"
             + (f" — {result.get('url')}" if result.get("url") else ""))
    return results


def write_summary(results: list[dict]) -> None:
    lines = ["## PadippuPal — coordinated Proceed cycle", "",
             "| Check | Result | Run |", "|---|---|---|"]
    for result in results:
        url = result.get("url", "")
        run_link = f"[{result.get('run_id', 'open run')}]({url})" if url else "—"
        lines.append(f"| {result['name']} | **{result['status']}** | {run_link} |")
        if result.get("detail"):
            lines.extend(["", f"- {result['name']}: {result['detail']}"])
    failed = [item for item in results if item["status"] != "success"]
    lines.extend(["", f"**Overall:** {'PASS' if not failed else 'ATTENTION REQUIRED'}",
                  "", "A failed check does not cancel later independent checks. This controller "
                  "collects evidence only; it does not invent or apply code repairs."])
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")


def resolve_target(environ: dict[str, str]) -> tuple[str, str]:
    """Resolve an exact PR target for chat-triggered cycles or workflow_dispatch."""
    explicit_ref = environ.get("PROCEED_REF", "")
    explicit_sha = environ.get("PROCEED_SHA", "")
    ref = explicit_ref or environ.get("GITHUB_REF_NAME", "")
    sha = explicit_sha or environ.get("GITHUB_SHA", "")
    ref_type = "branch" if explicit_ref else environ.get("GITHUB_REF_TYPE", "branch")
    if not all((ref, sha)) or ref_type != "branch":
        raise ValueError("A branch ref and exact commit SHA are required.")
    return ref, sha


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repository:
        raise SystemExit("BLOCKED: GITHUB_TOKEN and GITHUB_REPOSITORY are required.")
    try:
        ref, sha = resolve_target(os.environ)
    except ValueError as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
    api = GitHubActionsAPI(token, repository)
    results = run_pipeline(api, ref, sha, reuse_event=os.environ.get("PROCEED_REUSE_EVENT", ""))
    write_summary(results)
    return 0 if all(item["status"] == "success" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
