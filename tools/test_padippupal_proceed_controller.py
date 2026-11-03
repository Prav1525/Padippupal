import unittest
from threading import Barrier
from datetime import datetime, timezone

from padippupal_proceed_controller import (GitHubStatusReporter, MONITOR_INTERVAL_SECONDS,
                                             PIPELINE_STAGES, resolve_target, run_pipeline)


class FakeGitHubActionsAPI:
    def __init__(self, failing_workflow=None):
        self.failing_workflow = failing_workflow
        self.dispatched = []
        self.runs = {}
        self.next_id = 100

    def request(self, method, path, payload=None):
        if method == "POST" and path.endswith("/dispatches"):
            workflow = path.split("/actions/workflows/", 1)[1].split("/", 1)[0]
            self.dispatched.append((workflow, payload))
            self.next_id += 1
            conclusion = "failure" if workflow == self.failing_workflow else "success"
            run = {
                "id": self.next_id,
                "event": "workflow_dispatch",
                "head_sha": "abc123",
                "head_branch": "feature/controller-test",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "completed",
                "conclusion": conclusion,
                "html_url": f"https://github.com/example/repo/actions/runs/{self.next_id}",
            }
            self.runs[self.next_id] = run
            self.runs[workflow] = run
            return None

        if method == "GET" and "/runs?" in path:
            workflow = path.split("/actions/workflows/", 1)[1].split("/runs?", 1)[0]
            run = self.runs.get(workflow)
            return {"workflow_runs": [run] if run else []}

        if method == "GET" and path.startswith("/actions/runs/"):
            run_id = int(path.rsplit("/", 1)[1])
            return self.runs[run_id]

        raise AssertionError(f"Unexpected API call: {method} {path}")


class DispatchBarrierAPI(FakeGitHubActionsAPI):
    def __init__(self, participants):
        super().__init__()
        self.barrier = Barrier(participants)

    def request(self, method, path, payload=None):
        if method == "POST" and path.endswith("/dispatches"):
            self.barrier.wait(timeout=5)
        return super().request(method, path, payload)


class ExistingRunFakeAPI(FakeGitHubActionsAPI):
    def request(self, method, path, payload=None):
        if method == "GET" and "/runs?" in path:
            workflow = path.split("/actions/workflows/", 1)[1].split("/runs?", 1)[0]
            return {"workflow_runs": [{
                "id": 777,
                "event": "pull_request",
                "head_sha": "abc123",
                "head_branch": "feature/controller-test",
                "status": "completed",
                "conclusion": "success",
                "html_url": "https://github.com/example/repo/actions/runs/777",
            }]}
        if method == "GET" and path == "/actions/runs/777":
            return {
                "id": 777, "status": "completed", "conclusion": "success",
                "html_url": "https://github.com/example/repo/actions/runs/777",
            }
        return super().request(method, path, payload)


class ExistingPushRunFakeAPI(ExistingRunFakeAPI):
    def request(self, method, path, payload=None):
        if method == "GET" and "/runs?" in path:
            return {"workflow_runs": [{
                "id": 778,
                "event": "push",
                "head_sha": "abc123",
                "head_branch": "main",
                "status": "completed",
                "conclusion": "success",
                "html_url": "https://github.com/example/repo/actions/runs/778",
            }]}
        if method == "GET" and path == "/actions/runs/778":
            return {
                "id": 778, "status": "completed", "conclusion": "success",
                "html_url": "https://github.com/example/repo/actions/runs/778",
            }
        return super().request(method, path, payload)


class MissingPushRunFakeAPI(FakeGitHubActionsAPI):
    def request(self, method, path, payload=None):
        if method == "GET" and "/runs?" in path:
            return {"workflow_runs": []}
        return super().request(method, path, payload)


class DelayedFakeGitHubActionsAPI(FakeGitHubActionsAPI):
    def __init__(self):
        super().__init__()
        self.status_polls = {}

    def request(self, method, path, payload=None):
        if method == "GET" and path.startswith("/actions/runs/"):
            run_id = int(path.rsplit("/", 1)[1])
            self.status_polls[run_id] = self.status_polls.get(run_id, 0) + 1
            run = dict(self.runs[run_id])
            if self.status_polls[run_id] == 1:
                run["status"] = "in_progress"
                run["conclusion"] = None
            return run
        return super().request(method, path, payload)



class FakeReporterAPI:
    def __init__(self):
        self.calls = []
        self.issue = {"number": 42, "html_url": "https://github.com/example/repo/issues/42"}

    def request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "POST" and path == "/issues":
            return self.issue
        if method == "POST" and path == "/issues/42/comments":
            return {"id": len(self.calls)}
        raise AssertionError(f"Unexpected reporter API call: {method} {path}")


class StatusReporterTests(unittest.TestCase):
    def test_reporter_creates_issue_and_posts_lifecycle_updates_with_real_newlines(self):
        api = FakeReporterAPI()
        reporter = GitHubStatusReporter(api, "feature/reporting", "deadbeef123456")
        reporter.start()
        reporter.post("Proceed cycle started.")
        reporter.post("Five-minute monitor checkpoint — **Android APK**: in_progress / pending")
        reporter.finish([
            {"name": "Android APK", "status": "success", "url": "https://example.test/run/1"}
        ])

        self.assertEqual(api.calls[0][0:2], ("POST", "/issues"))
        issue_body = api.calls[0][2]["body"]
        self.assertIn("\n", issue_body)
        self.assertNotIn("\\n", issue_body)
        self.assertIn("Exact SHA: \`deadbeef123456\`", issue_body)
        self.assertEqual(len(api.calls), 4)
        self.assertTrue(all(call[1] == "/issues/42/comments" for call in api.calls[1:]))
        self.assertIn("Five-minute monitor checkpoint", api.calls[2][2]["body"])
        self.assertIn("Proceed cycle completed — PASS", api.calls[3][2]["body"])
        self.assertIn("Android APK", api.calls[3][2]["body"])


class ProceedTargetTests(unittest.TestCase):
    def test_chat_bridge_uses_exact_pr_branch_and_head_sha(self):
        self.assertEqual(
            resolve_target({
                "PROCEED_REF": "feature/active-pr",
                "PROCEED_SHA": "deadbeef",
                "GITHUB_REF_NAME": "main",
                "GITHUB_SHA": "mainsha",
                "GITHUB_REF_TYPE": "branch",
            }),
            ("feature/active-pr", "deadbeef"),
        )

    def test_manual_workflow_dispatch_keeps_its_exact_ref_and_sha(self):
        self.assertEqual(
            resolve_target({
                "GITHUB_REF_NAME": "feature/manual",
                "GITHUB_SHA": "abc123",
                "GITHUB_REF_TYPE": "branch",
            }),
            ("feature/manual", "abc123"),
        )

    def test_missing_exact_sha_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_target({"PROCEED_REF": "feature/no-sha"})


class ProceedControllerTests(unittest.TestCase):
    def test_controller_monitors_active_test_runs_every_five_minutes(self):
        api = DelayedFakeGitHubActionsAPI()
        waits = []
        results = run_pipeline(
            api,
            "feature/controller-test",
            "abc123",
            stages=(PIPELINE_STAGES[0],),
            sleep=waits.append,
            emit=lambda _message: None,
        )
        self.assertEqual(waits, [MONITOR_INTERVAL_SECONDS])
        self.assertEqual(MONITOR_INTERVAL_SECONDS, 300)
        self.assertEqual(results[0]["status"], "success")

    def test_pipeline_contains_one_ordered_entry_for_each_existing_check(self):
        workflows = [stage["workflow"] for stage in PIPELINE_STAGES]
        self.assertEqual(len(workflows), len(set(workflows)))
        self.assertEqual(workflows, [
            "investigation-guidance.yml",
            "curriculum-engine.yml",
            "android.yml",
            "deployed-api-smoke.yml",
            "android-ui-smoke.yml",
        ])

    def test_failure_does_not_prevent_later_steps_from_running(self):
        api = FakeGitHubActionsAPI(failing_workflow="curriculum-engine.yml")
        results = run_pipeline(
            api,
            "feature/controller-test",
            "abc123",
            sleep=lambda _seconds: None,
            emit=lambda _message: None,
        )
        self.assertEqual(len(api.dispatched), len(PIPELINE_STAGES))
        self.assertEqual(results[1]["status"], "failure")
        self.assertEqual(results[2]["status"], "success")
        self.assertEqual(results[-1]["status"], "success")


    def test_independent_checks_are_dispatched_concurrently(self):
        stages = PIPELINE_STAGES[:3]
        api = DispatchBarrierAPI(len(stages))
        results = run_pipeline(
            api,
            "feature/controller-test",
            "abc123",
            stages=stages,
            sleep=lambda _seconds: None,
            emit=lambda _message: None,
        )
        self.assertEqual(len(api.dispatched), len(stages))
        self.assertTrue(all(item["status"] == "success" for item in results))

    def test_pr_cycle_reuses_exact_sha_run_instead_of_dispatching_duplicate(self):
        api = ExistingRunFakeAPI()
        results = run_pipeline(
            api,
            "feature/controller-test",
            "abc123",
            stages=(PIPELINE_STAGES[0],),
            reuse_event="pull_request",
            sleep=lambda _seconds: None,
            emit=lambda _message: None,
        )
        self.assertEqual(api.dispatched, [])
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["run_id"], 777)

    def test_main_push_cycle_reuses_exact_sha_run_without_dispatch(self):
        api = ExistingPushRunFakeAPI()
        results = run_pipeline(
            api,
            "main",
            "abc123",
            stages=(PIPELINE_STAGES[0],),
            reuse_event="push",
            sleep=lambda _seconds: None,
            emit=lambda _message: None,
        )
        self.assertEqual(api.dispatched, [])
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["run_id"], 778)

    def test_main_push_missing_exact_run_does_not_dispatch_newer_commit(self):
        api = MissingPushRunFakeAPI()
        clock = [0.0]
        def sleep(seconds):
            clock[0] += seconds
        results = run_pipeline(
            api,
            "main",
            "abc123",
            stages=(PIPELINE_STAGES[0],),
            reuse_event="push",
            sleep=sleep,
            monotonic=lambda: clock[0],
            emit=lambda _message: None,
        )
        self.assertEqual(api.dispatched, [])
        self.assertEqual(results[0]["status"], "run_not_found")

    def test_android_dispatch_never_requests_public_release(self):
        android = next(stage for stage in PIPELINE_STAGES if stage["workflow"] == "android.yml")
        self.assertEqual(android["inputs"], {"publish_release": "false"})

    def test_each_stage_is_dispatched_once_without_blind_retry(self):
        api = FakeGitHubActionsAPI(failing_workflow="android-ui-smoke.yml")
        results = run_pipeline(
            api,
            "feature/controller-test",
            "abc123",
            sleep=lambda _seconds: None,
            emit=lambda _message: None,
        )
        dispatched_workflows = [workflow for workflow, _payload in api.dispatched]
        self.assertCountEqual(dispatched_workflows, [stage["workflow"] for stage in PIPELINE_STAGES])
        self.assertEqual(len(dispatched_workflows), len(PIPELINE_STAGES))
        self.assertEqual(results[-1]["status"], "failure")


if __name__ == "__main__":
    unittest.main(verbosity=2)
