import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import config


class DataDirectoryConfigTest(unittest.TestCase):
    def test_default_data_dir_is_shared_under_user_home(self):
        with tempfile.TemporaryDirectory() as home_dir:
            self.assertEqual(
                config.resolve_data_dir(value=None, home=Path(home_dir)),
                Path(home_dir) / ".super-publisher" / "toutiao-publisher",
            )

    def test_relative_override_is_resolved_from_user_home(self):
        with tempfile.TemporaryDirectory() as home_dir:
            self.assertEqual(
                config.resolve_data_dir(
                    value="shared/toutiao-session",
                    home=Path(home_dir),
                ),
                Path(home_dir) / "shared" / "toutiao-session",
            )

    def test_absolute_override_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            absolute_dir = Path(temp_dir) / "toutiao-session"

            self.assertEqual(
                config.resolve_data_dir(value=str(absolute_dir)),
                absolute_dir,
            )


if __name__ == "__main__":
    unittest.main()
