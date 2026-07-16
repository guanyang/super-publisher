import sys
import tempfile
import unittest
import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import run


class RunnerEnvironmentTest(unittest.TestCase):
    def write_current_marker(self, venv_python):
        marker = venv_python.parents[1] / ".requirements.sha256"
        marker.write_text(run.requirements_digest())

    def test_existing_venv_python_skips_environment_setup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_python = Path(temp_dir) / ".venv" / "bin" / "python"
            venv_python.parent.mkdir(parents=True)
            venv_python.write_text("#!/bin/sh\n")
            venv_python.chmod(0o755)
            self.write_current_marker(venv_python)

            with (
                patch("run.get_venv_python", return_value=venv_python),
                patch("run.subprocess.run") as subprocess_run,
            ):
                result = run.ensure_venv()

            self.assertEqual(result, venv_python)
            subprocess_run.assert_not_called()

    def test_missing_venv_python_runs_setup_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_python = Path(temp_dir) / "missing-python"
            ready_python = Path(temp_dir) / "ready-python"
            ready_python.write_text("#!/bin/sh\n")
            ready_python.chmod(0o755)
            completed = Mock(returncode=0)

            with (
                patch(
                    "run.get_venv_python",
                    side_effect=[missing_python, ready_python],
                ),
                patch("run.subprocess.run", return_value=completed) as subprocess_run,
            ):
                result = run.ensure_venv()

            self.assertEqual(result, ready_python)
            subprocess_run.assert_called_once()
            self.assertEqual(subprocess_run.call_args.args[0][0], sys.executable)
            self.assertTrue(
                str(subprocess_run.call_args.args[0][1]).endswith(
                    "scripts/setup_environment.py"
                )
            )

    def test_signal_return_code_is_normalized_for_agents(self):
        self.assertEqual(run.normalize_returncode(-2), 130)
        self.assertEqual(run.normalize_returncode(3), 3)

    def test_stale_requirements_marker_runs_setup_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / ".venv"
            venv_python = venv_dir / "bin" / "python"
            venv_python.parent.mkdir(parents=True)
            venv_python.write_text("#!/bin/sh\n")
            venv_python.chmod(0o755)
            (venv_dir / ".requirements.sha256").write_text("stale")
            completed = Mock(returncode=0)

            with (
                patch("run.get_venv_python", return_value=venv_python),
                patch("run.subprocess.run", return_value=completed) as subprocess_run,
            ):
                run.ensure_venv(json_mode=True)

            subprocess_run.assert_called_once()
            self.assertIs(subprocess_run.call_args.kwargs["stdout"], sys.stderr)

    def test_environment_setup_failure_emits_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_python = Path(temp_dir) / "missing-python"
            stdout = StringIO()
            stderr = StringIO()

            with (
                patch("run.get_venv_python", return_value=missing_python),
                patch("run.subprocess.run", return_value=Mock(returncode=1)),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                with self.assertRaises(SystemExit) as raised:
                    run.ensure_venv(json_mode=True)

            payload = json.loads(stdout.getvalue())
            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(payload["status"], "environment_setup_failed")

    def test_interrupt_is_forwarded_to_child_and_waits_for_clean_exit(self):
        process = Mock()
        process.wait.side_effect = [KeyboardInterrupt(), 0]

        with (
            patch.object(sys, "argv", ["run.py", "publisher.py", "--json"]),
            patch("run.ensure_venv", return_value=Path(sys.executable)),
            patch("run.subprocess.Popen", return_value=process) as popen,
            self.assertRaises(SystemExit) as raised,
        ):
            run.main()

        self.assertEqual(raised.exception.code, 0)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        process.send_signal.assert_called_once_with(run.signal.SIGINT)
        process.wait.assert_called_with(timeout=30)


if __name__ == "__main__":
    unittest.main()
