import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "scripts/run.sh"


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.skill = self.root / "gif-maker"
        scripts = self.skill / "scripts"
        scripts.mkdir(parents=True)
        shutil.copyfile(RUNNER, scripts / "run.sh")
        (scripts / "make_gif.py").write_text("print('current-python')\n")
        (self.skill / "requirements.txt").write_text("Pillow>=999\n")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=f"{self.bin}:/usr/bin:/bin", PIP_NO_INDEX="1",
                        PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK="1")

    def python_wrapper(self, body):
        path = self.bin / "python3"
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)

    def run_launcher(self):
        return subprocess.run(["/bin/bash", str(self.skill / "scripts/run.sh")],
                              env=self.env, capture_output=True, text=True, timeout=30)

    def test_usable_existing_venv_has_priority(self):
        python = self.skill / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit 0; fi\necho skill-venv\n')
        python.chmod(0o755)
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "skill-venv")

    def test_usable_current_python_runs_offline_without_creating_venv(self):
        self.python_wrapper(f'exec "{sys.executable}" "$@"\n')
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "current-python")
        self.assertFalse((self.skill / ".venv").exists())

    def test_failed_new_environment_setup_is_cleaned_up(self):
        self.python_wrapper('if [ "$1" = "-c" ]; then exit 1; fi\n'
                            f'exec "{sys.executable}" "$@"\n')
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.skill / ".venv").exists())
        self.assertTrue((self.skill / "requirements.txt").exists())

    def test_incomplete_existing_environment_is_preserved(self):
        venv = self.skill / ".venv"
        venv.mkdir()
        (venv / "user-file").write_text("keep")
        self.python_wrapper('exit 1\n')
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((venv / "user-file").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
