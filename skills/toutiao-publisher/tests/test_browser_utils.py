import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from browser_utils import BrowserFactory
from profile_lock import ProfileLockedError


class FakeChromium:
    def __init__(self):
        self.launch_kwargs = None

    def launch_persistent_context(self, **kwargs):
        self.launch_kwargs = kwargs
        return FakeContext()


class FakeContext:
    def close(self):
        pass


class FakePlaywright:
    def __init__(self):
        self.chromium = FakeChromium()


class BrowserFactoryTest(unittest.TestCase):
    def test_real_chrome_user_agent_is_not_overridden(self):
        playwright = FakePlaywright()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(BrowserFactory, "_inject_cookies"):
                context = BrowserFactory.launch_persistent_context(
                    playwright,
                    user_data_dir=str(Path(temp_dir) / "browser_profile"),
                    lock_path=str(Path(temp_dir) / "profile.lock"),
                )

        self.assertNotIn("user_agent", playwright.chromium.launch_kwargs)
        context.close()

    def test_shared_profile_lock_is_held_until_context_closes(self):
        playwright = FakePlaywright()

        with tempfile.TemporaryDirectory() as temp_dir:
            kwargs = {
                "user_data_dir": str(Path(temp_dir) / "browser_profile"),
                "lock_path": str(Path(temp_dir) / "profile.lock"),
            }
            with patch.object(BrowserFactory, "_inject_cookies"):
                first = BrowserFactory.launch_persistent_context(playwright, **kwargs)
                with self.assertRaises(ProfileLockedError):
                    BrowserFactory.launch_persistent_context(playwright, **kwargs)

                first.close()
                second = BrowserFactory.launch_persistent_context(playwright, **kwargs)
                second.close()


if __name__ == "__main__":
    unittest.main()
