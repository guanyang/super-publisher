import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import setup_environment


class SetupEnvironmentTest(unittest.TestCase):
    def test_broken_venv_is_recreated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            environment = setup_environment.SkillEnvironment()
            environment.venv_dir = root / ".venv"
            environment.venv_python = environment.venv_dir / "bin" / "python"
            environment.venv_pip = environment.venv_dir / "bin" / "pip"
            environment.requirements_file = root / "missing-requirements.txt"
            environment.venv_dir.mkdir()
            (environment.venv_dir / "stale-file").write_text("broken")

            def create_venv(path, with_pip):
                self.assertTrue(with_pip)
                python_path = Path(path) / "bin" / "python"
                python_path.parent.mkdir(parents=True)
                python_path.write_text("#!/bin/sh\n")

            with patch("setup_environment.venv.create", side_effect=create_venv) as create:
                result = environment.ensure_venv()

            self.assertTrue(result)
            create.assert_called_once_with(environment.venv_dir, with_pip=True)
            self.assertFalse((environment.venv_dir / "stale-file").exists())

    def test_requirements_marker_is_written_after_install(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            environment = setup_environment.SkillEnvironment()
            environment.venv_dir = root / ".venv"
            environment.venv_python = environment.venv_dir / "bin" / "python"
            environment.venv_pip = environment.venv_dir / "bin" / "pip"
            environment.requirements_file = root / "requirements.txt"
            environment.requirements_marker = environment.venv_dir / ".requirements.sha256"
            environment.requirements_file.write_text("example==1.0\n")
            environment.venv_python.parent.mkdir(parents=True)
            environment.venv_python.write_text("#!/bin/sh\n")
            environment.venv_pip.write_text("#!/bin/sh\n")

            with patch("setup_environment.subprocess.run"):
                self.assertTrue(environment.ensure_venv())

            self.assertEqual(
                environment.requirements_marker.read_text(),
                setup_environment.requirements_digest(environment.requirements_file),
            )


if __name__ == "__main__":
    unittest.main()
