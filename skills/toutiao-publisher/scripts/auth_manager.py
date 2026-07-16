#!/usr/bin/env python3
"""
Authentication Manager for Toutiao Publisher
Handles Toutiao login and browser state persistence
"""

import json
import time
import contextlib
import shutil
import sys
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

from patchright.sync_api import sync_playwright, BrowserContext

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DATA_DIR,
    LOGIN_URL,
    PUBLISH_URL,
)
from browser_utils import BrowserFactory
from cli_utils import configure_json_argument_parser


AUTH_COOKIE_DOMAINS = ("toutiao.com", "bytedance.com", "snssdk.com")
AUTH_PROBE_INTERVAL_SECONDS = 3
EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_INVALID_STATE = 2


def ensure_private_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def ensure_private_file(path):
    path = Path(path)
    if path.exists():
        path.chmod(0o600)
    return path


def is_login_url(url: str) -> bool:
    """Return whether Toutiao redirected the browser to an authentication page."""
    normalized = (url or "").lower()
    return "auth/page/login" in normalized or "sso.toutiao.com" in normalized


def is_authenticated_url(url: str) -> bool:
    """Return whether a URL belongs to the authenticated creator console."""
    if not url or is_login_url(url):
        return False

    parsed = urlparse(url)
    return parsed.hostname == "mp.toutiao.com" and parsed.path.startswith(
        "/profile_v4"
    )


class AuthManager:
    """
    Manages authentication and browser state for Toutiao
    """

    def __init__(self, data_dir=None):
        """Initialize the authentication manager"""
        self.data_dir = Path(data_dir) if data_dir is not None else DATA_DIR
        self.browser_state_dir = self.data_dir / "browser_state"
        self.browser_profile_dir = self.browser_state_dir / "browser_profile"
        self.state_file = self.browser_state_dir / "state.json"
        self.auth_info_file = self.data_dir / "auth_info.json"
        self.last_status = "unknown"

        # Ensure directories exist
        ensure_private_directory(self.data_dir)
        ensure_private_directory(self.browser_state_dir)
        ensure_private_directory(self.browser_profile_dir)
        ensure_private_file(self.state_file)
        ensure_private_file(self.auth_info_file)

    def is_authenticated(self) -> bool:
        """Check whether reusable Toutiao cookies exist in storage state."""
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError):
            return False

        cookies = state.get("cookies", [])
        has_toutiao_cookie = any(
            cookie.get("value")
            and any(
                domain in cookie.get("domain", "").lower()
                for domain in AUTH_COOKIE_DOMAINS
            )
            for cookie in cookies
        )
        if not has_toutiao_cookie:
            return False

        # Check if state file is not too old (7 days)
        age_days = (time.time() - self.state_file.stat().st_mtime) / 86400
        if age_days > 7:
            print(
                f"⚠️ Browser state is {age_days:.1f} days old, may need re-authentication"
            )

        return True

    def get_auth_info(self) -> Dict[str, Any]:
        """Get authentication information"""
        info = {
            "authenticated": self.is_authenticated(),
            "state_file": str(self.state_file),
            "state_exists": self.state_file.exists(),
        }

        if self.auth_info_file.exists():
            try:
                with open(self.auth_info_file, "r") as f:
                    saved_info = json.load(f)
                    info.update(saved_info)
            except Exception:
                pass

        if info["state_exists"]:
            age_hours = (time.time() - self.state_file.stat().st_mtime) / 3600
            info["state_age_hours"] = age_hours

        return info

    def setup_auth(
        self,
        headless: bool = False,
        timeout_minutes: int = 10,
    ) -> bool:
        """
        Perform interactive authentication setup

        Args:
            headless: Run browser in headless mode (False for login)
            timeout_minutes: Maximum time to wait for login

        Returns:
            True if authentication successful
        """
        print("🔐 Starting authentication setup...")
        print(f"  Timeout: {timeout_minutes} minutes")

        playwright = None
        context = None

        try:
            playwright = sync_playwright().start()

            # Launch using factory
            context = BrowserFactory.launch_persistent_context(
                playwright,
                headless=headless,
                user_data_dir=str(self.browser_profile_dir),
                state_file=str(self.state_file),
            )

            # Probe a protected page first. Visiting the login page is not a
            # reliable session check because it may remain visible even when
            # the persistent profile already has valid cookies.
            page = context.new_page()
            page.goto(PUBLISH_URL, wait_until="domcontentloaded")

            detected_url = self.detect_authenticated_url(context)
            if detected_url:
                print("  ✅ Already authenticated!")
                self.save_auth_state(context)
                self.last_status = "authenticated"
                return True

            if not is_login_url(page.url):
                page.goto(LOGIN_URL, wait_until="domcontentloaded")

            # Wait for manual login
            print("\n  ⏳ Please log in to your Toutiao account...")
            print(f"  ⏱️  Waiting up to {timeout_minutes} minutes for login...")
            print("  (Please scan the QR code or login with password)")

            try:
                # Wait for URL to be the home page or dashboard, implying login success
                # Often it redirects to https://mp.toutiao.com/profile_v4/index or similar
                # timeout_ms = int(timeout_minutes * 60 * 1000)

                start_time = time.time()
                last_probe_time = start_time - AUTH_PROBE_INTERVAL_SECONDS
                while time.time() - start_time < (timeout_minutes * 60):
                    detected_url = self.detect_authenticated_url(context)

                    now = time.time()
                    if (
                        not detected_url
                        and now - last_probe_time >= AUTH_PROBE_INTERVAL_SECONDS
                    ):
                        detected_url = self.detect_authenticated_url(
                            context, include_network_probe=True
                        )
                        last_probe_time = now

                    if detected_url:
                        print(f"  ✅ Login successful! (Detected: {detected_url})")
                        self.save_auth_state(context)
                        self.last_status = "authenticated"
                        return True

                    time.sleep(1)

                print("  ❌ Timeout waiting for login redirect")
                self.last_status = "login_timeout"
                return False

            except Exception as e:
                print(f"  ❌ Authentication error: {e}")
                self.last_status = "authentication_failed"
                return False

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.last_status = "authentication_failed"
            return False

        finally:
            # Clean up browser resources
            if context:
                try:
                    context.close()
                except Exception:
                    pass

            if playwright:
                try:
                    playwright.stop()
                except Exception:
                    pass

    def detect_authenticated_url(
        self, context: BrowserContext, include_network_probe: bool = False
    ):
        """Return an authenticated console URL from tabs or a protected probe."""
        authenticated_page = self._find_authenticated_page(context)
        if authenticated_page:
            return authenticated_page.url
        if include_network_probe:
            return self._probe_authenticated_session(context)
        return None

    def _find_authenticated_page(self, context: BrowserContext):
        """Find an authenticated creator-console tab in the current context."""
        for page in context.pages:
            try:
                if is_authenticated_url(page.url):
                    return page
            except Exception:
                continue
        return None

    def _probe_authenticated_session(self, context: BrowserContext):
        """Probe a protected URL without navigating away from the QR login tab."""
        try:
            response = context.request.get(
                PUBLISH_URL,
                timeout=10000,
                fail_on_status_code=False,
            )
            return response.url if is_authenticated_url(response.url) else None
        except Exception:
            return None

    def _save_browser_state(self, context: BrowserContext):
        """Save browser state to disk"""
        try:
            # Save storage state (cookies, localStorage)
            context.storage_state(path=str(self.state_file))
            ensure_private_file(self.state_file)
            print(f"  💾 Saved browser state to: {self.state_file}")
        except Exception as e:
            print(f"  ❌ Failed to save browser state: {e}")
            raise

    def save_auth_state(self, context: BrowserContext):
        """Persist browser storage and authentication metadata together."""
        self._save_browser_state(context)
        self._save_auth_info()

    def _save_auth_info(self):
        """Save authentication metadata"""
        try:
            info = {
                "authenticated_at": time.time(),
                "authenticated_at_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(self.auth_info_file, "w") as f:
                json.dump(info, f, indent=2)
            ensure_private_file(self.auth_info_file)
        except Exception:
            pass  # Non-critical

    def clear_auth(self, confirmed: bool = False) -> bool:
        """
        Clear all authentication data

        Returns:
            True if cleared successfully
        """
        if not confirmed:
            print("❌ Refusing to clear the shared profile without explicit confirmation.")
            print("   Re-run the command with --yes after the user confirms.")
            self.last_status = "confirmation_required"
            return False

        print("🗑️ Clearing authentication data...")
        try:
            self._clear_auth_files()
            self.last_status = "cleared"
            return True
        except Exception as e:
            print(f"  ❌ Error clearing auth: {e}")
            self.last_status = "clear_failed"
            return False

    def _clear_auth_files(self):
        if self.state_file.exists():
            self.state_file.unlink()
            print("  ✅ Removed browser state")

        if self.auth_info_file.exists():
            self.auth_info_file.unlink()
            print("  ✅ Removed auth info")

        if self.browser_state_dir.exists():
            shutil.rmtree(self.browser_state_dir)
        ensure_private_directory(self.browser_state_dir)
        ensure_private_directory(self.browser_profile_dir)
        print("  ✅ Cleared browser data")

    def re_auth(
        self,
        headless: bool = False,
        timeout_minutes: int = 10,
        confirmed: bool = False,
    ) -> bool:
        """
        Perform re-authentication (clear and setup)

        Args:
            headless: Run browser in headless mode
            timeout_minutes: Login timeout in minutes

        Returns:
            True if successful
        """
        print("🔄 Starting re-authentication...")
        if not confirmed:
            print("❌ Refusing to clear the shared profile without explicit confirmation.")
            print("   Re-run the command with --yes after the user confirms.")
            self.last_status = "confirmation_required"
            return False

        try:
            print("🗑️ Clearing authentication data...")
            self._clear_auth_files()
            return self.setup_auth(headless, timeout_minutes)
        except Exception as e:
            print(f"  ❌ Re-authentication failed: {e}")
            self.last_status = "authentication_failed"
            return False

    def validate_auth(self) -> bool:
        """
        Validate that stored authentication works
        """
        print("🔍 Validating authentication...")

        playwright = None
        context = None

        try:
            playwright = sync_playwright().start()

            # Launch using factory
            context = BrowserFactory.launch_persistent_context(
                playwright,
                headless=True,
                user_data_dir=str(self.browser_profile_dir),
                state_file=str(self.state_file),
            )

            # A protected creator URL is a stronger signal than the public
            # home page and can also recover cookies from browser_profile when
            # state.json has not been exported yet.
            page = context.new_page()
            page.goto(PUBLISH_URL, wait_until="domcontentloaded", timeout=30000)

            if not is_authenticated_url(page.url):
                print("  ❌ Authentication is invalid (redirected to login)")
                self.last_status = "not_authenticated"
                return False

            self.save_auth_state(context)
            print("  ✅ Authentication is valid")
            self.last_status = "authenticated"
            return True

        except Exception as e:
            print(f"  ❌ Validation failed: {e}")
            self.last_status = "validation_failed"
            return False

        finally:
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            if playwright:
                try:
                    playwright.stop()
                except Exception:
                    pass


def _add_json_argument(parser):
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write one machine-readable JSON result to stdout",
    )


def _exit_code_for_status(status):
    if status in {"not_authenticated", "confirmation_required"}:
        return EXIT_INVALID_STATE
    return EXIT_FAILURE


def main(argv=None):
    """Command-line interface for authentication management"""
    cli_argv = list(argv if argv is not None else sys.argv[1:])
    parser_class = configure_json_argument_parser(cli_argv)
    parser = parser_class(description="Manage Toutiao authentication")

    subparsers = parser.add_subparsers(
        dest="command",
        help="Commands",
        parser_class=parser_class,
    )

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup authentication")
    setup_parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode"
    )
    setup_parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="Login timeout in minutes (default: 10)",
    )
    _add_json_argument(setup_parser)

    # Status command
    status_parser = subparsers.add_parser("status", help="Check authentication status")
    status_parser.add_argument(
        "--verify",
        action="store_true",
        help="Launch the stored browser profile and verify it against Toutiao",
    )
    _add_json_argument(status_parser)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate authentication"
    )
    _add_json_argument(validate_parser)

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear authentication")
    clear_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm clearing the profile shared by every local Agent",
    )
    _add_json_argument(clear_parser)

    # Re-auth command
    reauth_parser = subparsers.add_parser(
        "reauth", help="Re-authenticate (clear + setup)"
    )
    reauth_parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="Login timeout in minutes (default: 10)",
    )
    reauth_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm clearing the profile shared by every local Agent",
    )
    _add_json_argument(reauth_parser)

    args = parser.parse_args(cli_argv)
    if not args.command:
        parser.print_help()
        return EXIT_INVALID_STATE

    auth = AuthManager()
    json_output = bool(getattr(args, "json", False))
    json_stream = sys.stdout
    output_context = (
        contextlib.redirect_stdout(sys.stderr)
        if json_output
        else contextlib.nullcontext()
    )
    payload = {"ok": False, "command": args.command, "status": "failed"}
    exit_code = EXIT_FAILURE

    with output_context:
        if args.command == "setup":
            ok = auth.setup_auth(
                headless=args.headless,
                timeout_minutes=args.timeout,
            )
            print(
                "\n✅ Authentication setup complete!"
                if ok
                else "\n❌ Authentication setup failed"
            )
            payload.update(ok=ok, status=auth.last_status)
            exit_code = EXIT_OK if ok else _exit_code_for_status(auth.last_status)

        elif args.command == "status":
            live_valid = auth.validate_auth() if args.verify else None
            info = auth.get_auth_info()
            valid = live_valid if args.verify else info["authenticated"]
            status = auth.last_status if args.verify else (
                "authenticated" if valid else "not_authenticated"
            )
            print("\n🔐 Authentication Status:")
            print(f"  Stored session: {'Yes' if info['authenticated'] else 'No'}")
            if info.get("state_age_hours") is not None:
                print(f"  State age: {info['state_age_hours']:.1f} hours")
            if info.get("authenticated_at_iso"):
                print(f"  Last auth: {info['authenticated_at_iso']}")
            print(f"  State file: {info['state_file']}")
            if args.verify:
                print(f"  Live check: {'Valid' if live_valid else 'Invalid or expired'}")
            payload.update(
                ok=bool(valid),
                status=status,
                stored_session=bool(info["authenticated"]),
                live_valid=live_valid,
                state_file=info["state_file"],
                state_age_hours=info.get("state_age_hours"),
            )
            exit_code = EXIT_OK if valid else _exit_code_for_status(status)

        elif args.command == "validate":
            ok = auth.validate_auth()
            print(
                "Authentication is valid and working"
                if ok
                else "Authentication is invalid or expired"
            )
            if not ok:
                print("Run: auth_manager.py setup")
            payload.update(ok=ok, status=auth.last_status)
            exit_code = EXIT_OK if ok else _exit_code_for_status(auth.last_status)

        elif args.command == "clear":
            ok = auth.clear_auth(confirmed=args.yes)
            if ok:
                print("Authentication cleared")
            payload.update(ok=ok, status=auth.last_status)
            exit_code = EXIT_OK if ok else _exit_code_for_status(auth.last_status)

        elif args.command == "reauth":
            ok = auth.re_auth(
                timeout_minutes=args.timeout,
                confirmed=args.yes,
            )
            print(
                "\n✅ Re-authentication complete!"
                if ok
                else "\n❌ Re-authentication failed"
            )
            payload.update(ok=ok, status=auth.last_status)
            exit_code = EXIT_OK if ok else _exit_code_for_status(auth.last_status)

    if json_output:
        print(json.dumps(payload, ensure_ascii=False), file=json_stream)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
