import unittest
from datetime import datetime, timezone

from padippupal_proceed_controller import PIPELINE_STAGES, run_pipeline


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


class ProceedControllerTests(unittest.TestCase):
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
        self.assertEqual(dispatched_workflows, [stage["workflow"] for stage in PIPELINE_STAGES])
        self.assertEqual(results[-1]["status"], "failure")


if __name__ == "__main__":
    unittest.main(verbosity=2)
