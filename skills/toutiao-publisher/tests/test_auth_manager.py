import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import auth_manager
from auth_manager import AuthManager
from config import LOGIN_URL, PUBLISH_URL


class FakePage:
    def __init__(self):
        self.url = "about:blank"
        self.goto_calls = []

    def goto(self, url, **_kwargs):
        self.goto_calls.append(url)
        if url == PUBLISH_URL:
            self.url = PUBLISH_URL
        elif url == LOGIN_URL:
            self.url = LOGIN_URL


class FakeContext:
    def __init__(self):
        self.page = FakePage()
        self.pages = [self.page]
        self.closed = False

    def new_page(self):
        return self.page

    def storage_state(self, path):
        Path(path).write_text(
            json.dumps(
                {
                    "cookies": [
                        {
                            "name": "sessionid",
                            "domain": ".toutiao.com",
                            "value": "test-only",
                        }
                    ]
                }
            )
        )

    def close(self):
        self.closed = True


class FakePlaywright:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakePlaywrightStarter:
    def __init__(self, playwright):
        self.playwright = playwright

    def start(self):
        return self.playwright


class AuthManagerTest(unittest.TestCase):
    def make_manager(self, temp_dir):
        return AuthManager(data_dir=temp_dir)

    def test_setup_probes_protected_page_before_requesting_qr_login(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = self.make_manager(temp_dir)
            context = FakeContext()
            playwright = FakePlaywright()

            with (
                patch(
                    "auth_manager.sync_playwright",
                    return_value=FakePlaywrightStarter(playwright),
                ),
                patch(
                    "auth_manager.BrowserFactory.launch_persistent_context",
                    return_value=context,
                ) as launch_context,
            ):
                result = manager.setup_auth(timeout_minutes=0)

            self.assertTrue(result)
            self.assertEqual(context.page.goto_calls, [PUBLISH_URL])
            self.assertTrue(manager.state_file.exists())
            self.assertTrue(context.closed)
            self.assertTrue(playwright.stopped)
            self.assertEqual(
                launch_context.call_args.kwargs["user_data_dir"],
                str(manager.browser_profile_dir),
            )
            self.assertEqual(
                launch_context.call_args.kwargs["state_file"],
                str(manager.state_file),
            )
    def test_empty_state_file_is_not_reported_as_authenticated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = self.make_manager(temp_dir)
            manager.state_file.write_text(json.dumps({"cookies": []}))

            self.assertFalse(manager.is_authenticated())

    def test_toutiao_cookie_is_reusable_local_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = self.make_manager(temp_dir)
            manager.state_file.write_text(
                json.dumps(
                    {
                        "cookies": [
                            {
                                "name": "sessionid",
                                "domain": ".toutiao.com",
                                "value": "test-only",
                            }
                        ]
                    }
                )
            )

            self.assertTrue(manager.is_authenticated())

    def test_live_validation_checks_browser_profile_without_state_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = self.make_manager(temp_dir)
            context = FakeContext()
            playwright = FakePlaywright()

            with (
                patch(
                    "auth_manager.sync_playwright",
                    return_value=FakePlaywrightStarter(playwright),
                ),
                patch(
                    "auth_manager.BrowserFactory.launch_persistent_context",
                    return_value=context,
                ),
            ):
                result = manager.validate_auth()

            self.assertTrue(result)
            self.assertEqual(context.page.goto_calls, [PUBLISH_URL])
            self.assertTrue(manager.state_file.exists())

    def test_auth_files_and_directories_are_private(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = self.make_manager(Path(temp_dir) / "auth")
            context = FakeContext()

            manager.save_auth_state(context)

            self.assertEqual(manager.data_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual(manager.browser_state_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual(manager.browser_profile_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual(manager.state_file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(manager.auth_info_file.stat().st_mode & 0o777, 0o600)

    def test_existing_auth_files_are_repaired_to_private_permissions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "auth"
            browser_state_dir = data_dir / "browser_state"
            browser_state_dir.mkdir(parents=True)
            state_file = browser_state_dir / "state.json"
            auth_info_file = data_dir / "auth_info.json"
            state_file.write_text("{}")
            auth_info_file.write_text("{}")
            state_file.chmod(0o644)
            auth_info_file.chmod(0o644)

            self.make_manager(data_dir)

            self.assertEqual(state_file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(auth_info_file.stat().st_mode & 0o777, 0o600)

    def test_clear_requires_explicit_confirmation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = self.make_manager(temp_dir)
            manager.state_file.write_text("secret")

            self.assertFalse(manager.clear_auth())
            self.assertTrue(manager.state_file.exists())
            self.assertEqual(manager.last_status, "confirmation_required")

            self.assertTrue(manager.clear_auth(confirmed=True))
            self.assertFalse(manager.state_file.exists())

    def test_status_json_returns_nonzero_when_not_authenticated(self):
        stdout = StringIO()
        stderr = StringIO()
        fake_manager = unittest.mock.Mock()
        fake_manager.get_auth_info.return_value = {
            "authenticated": False,
            "state_file": "/tmp/state.json",
            "state_exists": False,
        }

        with (
            patch("auth_manager.AuthManager", return_value=fake_manager),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = auth_manager.main(["status", "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, auth_manager.EXIT_INVALID_STATE)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "not_authenticated")

    def test_argparse_error_is_json_when_requested(self):
        stdout = StringIO()
        stderr = StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                auth_manager.main(["unknown", "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(raised.exception.code, auth_manager.EXIT_INVALID_STATE)
        self.assertEqual(payload["status"], "invalid_arguments")

    def test_reauth_clears_before_setup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = self.make_manager(temp_dir)

            with (
                patch.object(manager, "_clear_auth_files") as clear_files,
                patch.object(manager, "setup_auth", return_value=True) as setup_auth,
            ):
                result = manager.re_auth(confirmed=True)

            self.assertTrue(result)
            clear_files.assert_called_once_with()
            setup_auth.assert_called_once_with(False, 10)


if __name__ == "__main__":
    unittest.main()
