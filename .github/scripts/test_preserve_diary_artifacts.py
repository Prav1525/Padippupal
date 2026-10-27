#!/usr/bin/env python3
"""Regression tests for the diary artifact-preservation shell step."""
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".github/scripts/preserve_diary_artifacts.sh"


class PreserveDiaryArtifactsTests(unittest.TestCase):
    def run_script(self, root: Path, status: int) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT), str(status)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_success_copies_diagnostics_and_records_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "ui-screenshots/diary-test"
            source.mkdir(parents=True)
            (source / "hierarchy.xml").write_text("<hierarchy />", encoding="utf-8")

            result = self.run_script(root, 0)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "diary-artifacts/exit-code.txt").read_text(), "0\n")
            self.assertEqual(
                (root / "diary-artifacts/diary-test/hierarchy.xml").read_text(),
                "<hierarchy />",
            )

    def test_failure_still_preserves_diagnostics_and_propagates_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "ui-screenshots/diary-test"
            source.mkdir(parents=True)
            (source / "failure.txt").write_text("picker diagnostic", encoding="utf-8")

            result = self.run_script(root, 7)

            self.assertEqual(result.returncode, 7)
            self.assertEqual((root / "diary-artifacts/exit-code.txt").read_text(), "7\n")
            self.assertEqual(
                (root / "diary-artifacts/diary-test/failure.txt").read_text(),
                "picker diagnostic",
            )

    def test_invalid_status_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", str(SCRIPT), "not-a-status"],
                cwd=tmp,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
