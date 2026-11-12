import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import padippupal_local_executor as executor

class LocalExecutorPolicyTests(unittest.TestCase):
    def test_exact_approved_task_is_required_when_named(self):
        ledger = {"tasks": [{"id": "A", "status": "APPROVED"}, {"id": "B", "status": "PROPOSED"}]}
        executor.require_approved_task("A", ledger)
        for task in ("B", "missing"):
            with self.assertRaises(executor.PreflightError):
                executor.require_approved_task(task, ledger)

    def test_no_task_id_defers_selection_to_active_work_contract(self):
        executor.require_approved_task(None, {"tasks": []})

    def test_command_uses_workspace_write_and_on_request_only(self):
        command = executor.build_codex_command("codex", Path("/repo"), Path("/tmp/summary.md"))
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
        self.assertEqual(command[command.index("--ask-for-approval") + 1], "on-request")
        self.assertNotIn("--yolo", command)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertNotIn("danger-full-access", command)

    def test_prompt_preserves_repair_and_release_boundaries(self):
        prompt = executor.build_prompt("LOCAL-CODEX-EXECUTOR")
        self.assertIn("five generations", prompt)
        self.assertIn("Never merge a PR", prompt)
        self.assertIn("Requested approved task ID", prompt)

    def test_branch_name_is_timestamped_and_non_main(self):
        fixed = dt.datetime(2026, 11, 12, 7, 0, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(executor.make_branch_name(fixed), "agent/local-proceed-20261112-070000")

    def test_sensitive_file_detection(self):
        sensitive = [".env", ".env.production", "backend/secrets/key.json",
                     "config/auth.json", "certs/private.pem", "private_keys/token.key"]
        for path in sensitive:
            self.assertTrue(executor.is_sensitive_path(path), path)
        for path in ["tools/example.py", "docs/README.md", "app/src/Main.kt"]:
            self.assertFalse(executor.is_sensitive_path(path), path)

    def test_codex_auth_requires_logged_in_status(self):
        def fake_which(name):
            return "/usr/bin/codex"
        def logged(command, **kwargs):
            return type("Result", (), {"returncode": 0, "stdout": "Logged in using ChatGPT", "stderr": ""})()
        with patch.object(executor.shutil, "which", fake_which):
            self.assertEqual(executor.check_codex_auth(runner=logged), "/usr/bin/codex")
        def denied(command, **kwargs):
            return type("Result", (), {"returncode": 1, "stdout": "", "stderr": "not logged in"})()
        with patch.object(executor.shutil, "which", fake_which):
            with self.assertRaises(executor.PreflightError):
                executor.check_codex_auth(runner=denied)

    def test_dirty_worktree_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            dirty = type("Result", (), {"returncode": 0, "stdout": " M changed.py", "stderr": ""})()
            with patch.object(executor, "git", return_value=dirty):
                with self.assertRaises(executor.PreflightError):
                    executor.ensure_clean_repository(root)

    def test_sensitive_diff_is_not_exported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(executor, "include_untracked_files"):
                with patch.object(executor, "changed_paths", return_value=[".env.production"]):
                    with self.assertRaises(executor.PreflightError):
                        executor.collect_patch(root)

    def test_empty_diff_produces_no_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            empty = type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            with patch.object(executor, "include_untracked_files"):
                with patch.object(executor, "changed_paths", return_value=[]):
                    with patch.object(executor, "git", return_value=empty):
                        self.assertIsNone(executor.collect_patch(root))

if __name__ == "__main__":
    unittest.main(verbosity=2)
