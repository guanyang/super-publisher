"""
Browser Utilities for Toutiao Publisher Skill
Handles browser launching, stealth features, and common interactions
"""

import json
import time
import random
from pathlib import Path

from patchright.sync_api import Playwright, BrowserContext, Page
from config import BROWSER_PROFILE_DIR, PROFILE_LOCK_FILE, STATE_FILE, BROWSER_ARGS
from profile_lock import ProfileLock


class LockedBrowserContext:
    """Release the shared profile lock when the browser context closes."""

    def __init__(self, context, profile_lock):
        self._context = context
        self._profile_lock = profile_lock
        self._closed = False

    def __getattr__(self, name):
        return getattr(self._context, name)

    def close(self):
        if self._closed:
            return
        try:
            self._context.close()
        finally:
            self._profile_lock.release()
            self._closed = True


class BrowserFactory:
    """Factory for creating configured browser contexts"""

    @staticmethod
    def launch_persistent_context(
        playwright: Playwright,
        headless: bool = True,
        user_data_dir: str = str(BROWSER_PROFILE_DIR),
        lock_path: str = str(PROFILE_LOCK_FILE),
        state_file: str = str(STATE_FILE),
        profile_lock=None,
    ) -> BrowserContext:
        """
        Launch a persistent browser context with anti-detection features
        and cookie workaround.
        """
        profile_lock = profile_lock or ProfileLock(lock_path)
        if not profile_lock.acquired:
            profile_lock.acquire()
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",  # Use real Chrome
                headless=headless,
                no_viewport=True,
                ignore_default_args=["--enable-automation"],
                args=BROWSER_ARGS,
            )

            # Cookie Workaround for Playwright bug #36139
            # Session cookies (expires=-1) don't persist in user_data_dir automatically
            BrowserFactory._inject_cookies(context, state_file=state_file)
            return LockedBrowserContext(context, profile_lock)
        except Exception:
            profile_lock.release()
            raise

    @staticmethod
    def _inject_cookies(context: BrowserContext, state_file=STATE_FILE):
        """Inject cookies from state.json if available"""
        state_file = Path(state_file)
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    if "cookies" in state and len(state["cookies"]) > 0:
                        context.add_cookies(state["cookies"])
                        # print(f"  🔧 Injected {len(state['cookies'])} cookies from state.json")
            except Exception as e:
                print(f"  ⚠️  Could not load state.json: {e}")


class StealthUtils:
    """Human-like interaction utilities"""

    @staticmethod
    def random_delay(min_ms: int = 100, max_ms: int = 500):
        """Add random delay"""
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    @staticmethod
    def human_type(
        page: Page, selector: str, text: str, wpm_min: int = 320, wpm_max: int = 480
    ):
        """Type with human-like speed"""
        element = page.query_selector(selector)
        if not element:
            # Try waiting if not immediately found
            try:
                element = page.wait_for_selector(selector, timeout=2000)
            except:
                pass

        if not element:
            print(f"⚠️ Element not found for typing: {selector}")
            return

        # Click to focus
        element.click()

        # Type
        for char in text:
            element.type(char, delay=random.uniform(25, 75))
            if random.random() < 0.05:
                time.sleep(random.uniform(0.15, 0.4))

    @staticmethod
    def realistic_click(page: Page, selector: str):
        """Click with realistic movement"""
        element = page.query_selector(selector)
        if not element:
            return

        # Optional: Move mouse to element (simplified)
        box = element.bounding_box()
        if box:
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
            page.mouse.move(x, y, steps=5)

        StealthUtils.random_delay(100, 300)
        element.click()
        StealthUtils.random_delay(100, 300)
