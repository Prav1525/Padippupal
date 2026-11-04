#!/usr/bin/env python3
"""Regression test for the emulator's deterministic Google TTS fast path."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / ".github/scripts/android-tts-preflight.sh"


class AndroidTtsPreflightTest(unittest.TestCase):
    def test_prefers_preinstalled_google_tts_without_external_apk_download(self) -> None:
        with tempfile.TemporaryDirectory(prefix="padippupal-tts-test-") as temp:
            temp_path = Path(temp)
            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            call_log = temp_path / "adb-calls.txt"
            adb = bin_dir / "adb"
            adb.write_text(
                "#!/usr/bin/env bash\n"
                'printf \'%s\\n\' "$*" >> "$ADB_CALL_LOG"\n'
                'case "$*" in\n'
                '  *"cmd package query-services"*) printf "com.google.android.tts\\n" ;;\n'
                '  *"settings get secure tts_default_synth"*) printf "com.google.android.tts\\n" ;;\n'
                "esac\n",
                encoding="utf-8",
            )
            adb.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
            env["ADB_CALL_LOG"] = str(call_log)
            env["RUNNER_TEMP"] = str(temp_path)

            result = subprocess.run(
                ["bash", str(PREFLIGHT)],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=20,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Selected preinstalled Google TTS engine", result.stdout)
            calls = call_log.read_text(encoding="utf-8")
            self.assertIn("settings put secure tts_default_synth com.google.android.tts", calls)
            self.assertIn("settings get secure tts_default_synth", calls)
            self.assertNotIn("install", calls)


if __name__ == "__main__":
    unittest.main()
