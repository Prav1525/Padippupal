#!/usr/bin/env python3
"""Regression tests for base SHA resolution in dispatched investigation-gate runs."""
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

SCRIPT = Path(__file__).parent.parent / ".github" / "scripts" / "validate_investigation_ledger.py"
SPEC = importlib.util.spec_from_file_location("validate_investigation_ledger", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BaseShaResolutionTests(unittest.TestCase):
    def test_uses_event_supplied_base_sha(self):
        self.assertEqual(MODULE.resolve_base_sha("base-from-event", "head-sha"), "base-from-event")

    @mock.patch.object(MODULE, "run", return_value="merge-base-sha")
    def test_dispatch_falls_back_to_default_branch_merge_base(self, git_run):
        self.assertEqual(MODULE.resolve_base_sha("", "head-sha"), "merge-base-sha")
        git_run.assert_called_once_with("git", "merge-base", "origin/main", "head-sha")

    @mock.patch.object(MODULE, "run", side_effect=MODULE.subprocess.CalledProcessError(1, "git"))
    def test_missing_event_base_and_unavailable_merge_base_blocks(self, _git_run):
        self.assertIsNone(MODULE.resolve_base_sha("", "head-sha"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
