#!/usr/bin/env python3
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import padippupal_proceed_listener as listener

SHA = "a" * 40
STAMP = "2026-11-12T08:00:00Z"


def comment(comment_id=10, user="Prav1525", body="/proceed", number=398):
    return {
        "id": comment_id,
        "body": body,
        "created_at": STAMP,
        "issue_url": f"https://api.github.com/repos/Prav1525/Padippupal/issues/{number}",
        "user": {"login": user},
    }


def pull_request(state="open", author="Prav1525", repo="Prav1525/Padippupal", sha=SHA):
    return {
        "state": state,
        "user": {"login": author},
        "head": {"sha": sha, "repo": {"full_name": repo}},
    }


class FakeGitHub:
    def __init__(self, comments, pr=None):
        self.comments = comments
        self.pr = pr or pull_request()
        self.reports = []

    def comments_since(self, _timestamp):
        return self.comments

    def pull_request(self, _number):
        return self.pr

    def report(self, number, body):
        self.reports.append((number, body))


class ListenerContractTests(unittest.TestCase):
    def test_only_exact_owner_proceed_pr_comment_is_candidate(self):
        self.assertTrue(listener.is_owner_proceed(comment(), "Prav1525"))
        self.assertFalse(listener.is_owner_proceed(comment(user="someone-else"), "Prav1525"))
        self.assertFalse(listener.is_owner_proceed(comment(body="/proceed please"), "Prav1525"))
        self.assertFalse(listener.is_owner_proceed(comment(number=None), "Prav1525"))

    def test_pull_request_must_be_open_owner_authored_and_same_repository(self):
        self.assertIsNone(listener.validate_pr(pull_request(), "Prav1525/Padippupal", "Prav1525"))
        self.assertIsNotNone(listener.validate_pr(pull_request(state="closed"), "Prav1525/Padippupal", "Prav1525"))
        self.assertIsNotNone(listener.validate_pr(pull_request(author="other"), "Prav1525/Padippupal", "Prav1525"))
        self.assertIsNotNone(listener.validate_pr(pull_request(repo="fork/Padippupal"), "Prav1525/Padippupal", "Prav1525"))
        self.assertIsNotNone(listener.validate_pr(pull_request(sha="bad"), "Prav1525/Padippupal", "Prav1525"))

    def test_first_launch_arms_without_replaying_old_comments(self):
        with tempfile.TemporaryDirectory() as temp:
            state, first = listener.load_state(Path(temp) / "state.json")
            self.assertTrue(first)
            self.assertEqual(state["processed"], {})
            self.assertTrue(state["last_created_at"].endswith("Z"))

    def test_owner_proceed_runs_once_on_exact_pr_and_posts_result(self):
        with tempfile.TemporaryDirectory() as temp:
            state = {"schema_version": 1, "last_created_at": "2026-11-12T07:59:00Z", "processed": {}}
            state_path = Path(temp) / "state.json"
            client = FakeGitHub([comment()])
            expected = {"status": "PASS", "exit_code": 0, "branch": "agent/local-proceed-test",
                        "changed": "none", "summary": "/tmp/summary.md", "patch": "not produced",
                        "worktree": "/tmp/worktree"}
            calls = []
            with patch.object(listener, "make_worktree", return_value=Path("/tmp/worktree")) as worktree:
                outcome = listener.process_pending(
                    "Prav1525/Padippupal", client, state, root=Path(temp),
                    executor=lambda path, cid: calls.append((path, cid)) or expected,
                    state_path=state_path,
                )
            self.assertEqual(outcome, "PASS")
            self.assertEqual(len(calls), 1)
            worktree.assert_called_once_with(398, SHA, 10, Path(temp))
            self.assertEqual(client.reports[0][0], 398)
            self.assertIn(SHA, client.reports[0][1])
            self.assertIn("No commit, push", client.reports[0][1])
            self.assertEqual(state["processed"]["10"]["status"], "pass")
            listener.save_state(state, state_path)
            second = listener.process_pending(
                "Prav1525/Padippupal", client, state, root=Path(temp),
                executor=lambda *_: self.fail("duplicate comment executed"), state_path=state_path,
            )
            self.assertIsNone(second)

    def test_fork_pr_is_rejected_without_creating_worktree(self):
        with tempfile.TemporaryDirectory() as temp:
            state = {"schema_version": 1, "last_created_at": "2026-11-12T07:59:00Z", "processed": {}}
            client = FakeGitHub([comment()], pull_request(repo="attacker/Padippupal"))
            with patch.object(listener, "make_worktree") as worktree:
                result = listener.process_pending("Prav1525/Padippupal", client, state,
                                                   root=Path(temp), state_path=Path(temp) / "state.json")
            self.assertIsNone(result)
            worktree.assert_not_called()
            self.assertEqual(state["processed"]["10"]["status"], "rejected")
            self.assertEqual(client.reports, [])

    def test_non_owner_comment_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            state = {"schema_version": 1, "last_created_at": "2026-11-12T07:59:00Z", "processed": {}}
            client = FakeGitHub([comment(user="not-owner")])
            result = listener.process_pending("Prav1525/Padippupal", client, state,
                                               root=Path(temp), state_path=Path(temp) / "state.json")
            self.assertIsNone(result)
            self.assertEqual(state["processed"]["10"]["status"], "ignored")

    def test_fetch_must_match_exact_api_sha_before_worktree_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(listener, "git", side_effect=["", "b" * 40, ""]):
                with self.assertRaises(listener.ListenerError):
                    listener.make_worktree(398, SHA, 10, Path(temp))


if __name__ == "__main__":
    unittest.main(verbosity=2)
