import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from publisher import make_screenshot_taker


class FakePage:
    def __init__(self):
        self.paths = []

    def screenshot(self, path):
        self.paths.append(path)


class PublisherDebugScreenshotTest(unittest.TestCase):
    def test_screenshot_taker_is_noop_when_disabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            page = FakePage()
            take_screenshot = make_screenshot_taker(
                page,
                enabled=False,
                debug_dir=Path(temp_dir) / "debug",
            )

            take_screenshot("after_title")

            self.assertEqual(page.paths, [])
            self.assertFalse((Path(temp_dir) / "debug").exists())

    def test_screenshot_taker_writes_to_debug_dir_when_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            page = FakePage()
            take_screenshot = make_screenshot_taker(
                page,
                enabled=True,
                debug_dir=Path(temp_dir) / "debug",
            )

            take_screenshot("after_title")

            self.assertEqual(len(page.paths), 1)
            self.assertTrue(page.paths[0].startswith(str(Path(temp_dir) / "debug")))
            self.assertTrue(page.paths[0].endswith("_after_title.png"))


if __name__ == "__main__":
    unittest.main()
