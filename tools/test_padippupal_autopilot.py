import json
import tempfile
import unittest
from pathlib import Path

from padippupal_autopilot import (
    MAX_REPAIR_GENERATIONS,
    REQUIRED_AGENT_CONTRACT_MARKERS,
    approved_task,
    classify_log,
    next_generation,
    validate,
    validate_repair_state,
)


def make_validation_root(root: Path, ledger: dict | None = None, agent_text: str | None = None):
    for rel in ("TESTING_GUIDANCE.md", "TEST_INVESTIGATION.md",
                "docs/TESTING_ERRORS.md", "docs/TEST_FAILURE_REGISTER.md",
                "docs/AUTOPILOT_TRIGGER_PROMPT.md", ".github/testing-regression-checklist.md"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("guide", encoding="utf-8")
    active = root / ".engineering/tasks/active-work.md"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(
        "<!-- padippupal-repair-state:start -->\n"
        '{"schema_version":1,"max_generations":5,"chains":[]}\n'
        "<!-- padippupal-repair-state:end -->",
        encoding="utf-8",
    )
    (root / "AGENTS.md").write_text(
        agent_text if agent_text is not None else "\n".join(REQUIRED_AGENT_CONTRACT_MARKERS),
        encoding="utf-8",
    )
    ledger_value = ledger if ledger is not None else {
        "policy": "approved-roadmap-only",
        "max_repair_generations": 5,
        "tasks": [],
    }
    ledger_path = root / "docs/approved-work.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger_value), encoding="utf-8")


class ClassificationTests(unittest.TestCase):
    def test_known_android_failure_is_classified(self):
        self.assertEqual(classify_log("Execution failed for task :app:testDebugUnitTest")[0],
                         "android_build_or_test")

    def test_unknown_failure_requires_review(self):
        self.assertEqual(classify_log("strange opaque runner event")[0],
                         "unknown_requires_review")


class RepairLimitTests(unittest.TestCase):
    def test_all_five_generations_are_available(self):
        self.assertEqual([next_generation(n) for n in range(5)], [1, 2, 3, 4, 5])

    def test_sixth_generation_is_blocked(self):
        self.assertIsNone(next_generation(MAX_REPAIR_GENERATIONS))

    def test_negative_generation_is_rejected(self):
        with self.assertRaises(ValueError):
            next_generation(-1)


class PersistentRepairStateTests(unittest.TestCase):
    def test_empty_persistent_repair_state_is_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_validation_root(root)
            ledger = {"tasks": []}
            self.assertEqual(validate_repair_state(root, ledger), [])

    def test_repair_chain_must_reference_approved_work(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_validation_root(root)
            state = (
                '{"schema_version":1,"max_generations":5,"chains":['
                '{"id":"run-123","originating_run":"123","originating_sha":"abc",'
                '"task_id":"NOT-APPROVED","status":"OPEN","generations":[]}]}'
            )
            path = root / ".engineering/tasks/active-work.md"
            path.write_text(
                "<!-- padippupal-repair-state:start -->\n" + state + "\n"
                "<!-- padippupal-repair-state:end -->",
                encoding="utf-8",
            )
            self.assertTrue(any("outside approved work" in item
                                for item in validate_repair_state(root, {"tasks": []})))

    def test_sixth_generation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_validation_root(root)
            generations = [
                {"number": n, "hypothesis": f"hypothesis {n}", "commit_sha": f"sha{n}",
                 "verification_run": f"run{n}", "outcome": "FAIL"}
                for n in range(1, 7)
            ]
            state = {"schema_version": 1, "max_generations": 5, "chains": [{
                "id": "run-123", "originating_run": "123", "originating_sha": "abc",
                "task_id": "AUTOPILOT-CI-REPAIR", "status": "ESCALATED",
                "generations": generations,
            }]}
            path = root / ".engineering/tasks/active-work.md"
            path.write_text(
                "<!-- padippupal-repair-state:start -->\n" + json.dumps(state) + "\n"
                "<!-- padippupal-repair-state:end -->",
                encoding="utf-8",
            )
            approved = {"tasks": [{"id": "AUTOPILOT-CI-REPAIR", "status": "APPROVED"}]}
            self.assertTrue(any("exceeds five" in item
                                for item in validate_repair_state(root, approved)))

class ApprovalTests(unittest.TestCase):
    def test_only_exact_approved_task_is_eligible(self):
        ledger = {"tasks": [
            {"id": "A", "status": "APPROVED"},
            {"id": "B", "status": "PROPOSED"},
        ]}
        self.assertIsNotNone(approved_task("A", ledger))
        self.assertIsNone(approved_task("B", ledger))
        self.assertIsNone(approved_task("C", ledger))

    def test_duplicate_or_incomplete_approved_entries_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_validation_root(root, {
                "policy": "approved-roadmap-only",
                "max_repair_generations": 5,
                "tasks": [{"id": "A", "status": "APPROVED"}],
            })
            self.assertTrue(any("lacks scope" in item for item in validate(root)))

    def test_unified_trigger_contract_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_validation_root(root)
            (root / "docs/AUTOPILOT_TRIGGER_PROMPT.md").write_text(
                "# Trigger prompt without unified contract", encoding="utf-8"
            )
            errors = validate(root)
            self.assertTrue(any("unified trigger contract is missing" in item for item in errors))

    def test_closed_loop_contract_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_validation_root(root, agent_text="# Agent instructions\nNo contract markers here.")
            errors = validate(root)
            self.assertTrue(any("AGENTS.md missing closed-loop contract requirement" in item
                                for item in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
