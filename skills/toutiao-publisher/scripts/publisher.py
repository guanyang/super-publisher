#!/usr/bin/env python3
"""
Publisher script for Toutiao
Navigates to the publish page with authenticated session.
"""

import argparse
import contextlib
import html as html_lib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import PUBLISH_URL
from patchright.sync_api import sync_playwright
from auth_manager import (
    AUTH_PROBE_INTERVAL_SECONDS,
    AuthManager,
    is_login_url,
)
from browser_utils import BrowserFactory
from cli_utils import configure_json_argument_parser
from profile_lock import ProfileLockedError
from md2html import convert_with_images


EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_INVALID_INPUT = 2
EXIT_PROFILE_LOCKED = 3
PUBLISH_MODES = ("manual", "auto", "validate")
LOCAL_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class InputValidationError(ValueError):
    pass


@dataclass(frozen=True)
class PreparedArticle:
    title: Optional[str]
    content: Optional[str]
    content_base_dir: Path
    cover_image_path: Optional[str]
    html: str
    images: list[dict[str, str]]


@dataclass(frozen=True)
class PublishResult:
    ok: bool
    status: str
    message: str


def _validate_local_image(path, label):
    image_path = Path(path).expanduser().resolve()
    if not image_path.is_file():
        raise InputValidationError(f"{label} not found: {image_path}")
    if image_path.suffix.lower() not in LOCAL_IMAGE_SUFFIXES:
        raise InputValidationError(
            f"{label} must be PNG, JPG, JPEG, GIF, or WEBP: {image_path}"
        )
    if not os.access(image_path, os.R_OK):
        raise InputValidationError(f"{label} is not readable: {image_path}")
    return image_path


def prepare_article(
    title=None,
    content_file=None,
    content_text=None,
    cover_image_path=None,
    mode="manual",
    headless=False,
    no_cover=False,
    raw=False,
):
    """Validate and convert article input before opening Chrome."""
    if mode not in PUBLISH_MODES:
        raise InputValidationError(f"Unknown mode: {mode}")
    if headless and mode != "auto":
        raise InputValidationError("--headless is only valid with --mode auto")
    if content_file and content_text is not None:
        raise InputValidationError("Use either --content-file or --content-text, not both")
    if no_cover and cover_image_path:
        raise InputValidationError("Use either --no-cover or --cover, not both")

    has_article_input = any(
        value is not None for value in (title, content_file, content_text, cover_image_path)
    )
    if mode in {"auto", "validate"} or has_article_input:
        if title is None:
            raise InputValidationError("--title is required for article input")
        if content_file is None and content_text is None:
            raise InputValidationError(
                "--content-file or --content-text is required for article input"
            )

    normalized_title = title.strip() if title is not None else None
    if normalized_title is not None and not 2 <= len(normalized_title) <= 30:
        raise InputValidationError("Toutiao title must contain 2-30 characters")

    content = None
    content_base_dir = Path.cwd()
    if content_file is not None:
        content_path = Path(content_file).expanduser().resolve()
        if not content_path.is_file():
            raise InputValidationError(f"Content file not found: {content_path}")
        if not os.access(content_path, os.R_OK):
            raise InputValidationError(f"Content file is not readable: {content_path}")
        content = content_path.read_text(encoding="utf-8")
        content_base_dir = content_path.parent
    elif content_text is not None:
        content = content_text

    if content is not None and not content.strip():
        raise InputValidationError("Article content must not be empty")

    normalized_cover = None
    if cover_image_path:
        normalized_cover = str(_validate_local_image(cover_image_path, "Cover image"))

    converted_html = ""
    images = []
    if content:
        if raw:
            converted_html = "<p>" + html_lib.escape(content).replace("\n", "<br>\n") + "</p>"
        else:
            converted = convert_with_images(content, base_dir=content_base_dir)
            converted_html = converted.html
            images = converted.images
            for image in images:
                image_path = image["path"]
                if image_path.startswith(("http://", "https://", "data:")):
                    raise InputValidationError(
                        f"Inline image must be a local file: {image_path}"
                    )
                _validate_local_image(image_path, "Inline image")

    return PreparedArticle(
        title=normalized_title,
        content=content,
        content_base_dir=content_base_dir,
        cover_image_path=normalized_cover,
        html=converted_html,
        images=images,
    )


def _run_command(command, args, input_data=None):
    result = subprocess.run(
        [command, *args],
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def copy_image_to_clipboard(image_path):
    system = platform.system()
    image_path = str(Path(image_path).resolve())

    if system == "Darwin":
        swift_source = """
import AppKit
import Foundation

let inputPath = CommandLine.arguments[1]
let pasteboard = NSPasteboard.general
pasteboard.clearContents()

guard let image = NSImage(contentsOfFile: inputPath) else {
  FileHandle.standardError.write("Failed to load image\\n".data(using: .utf8)!)
  exit(1)
}

if !pasteboard.writeObjects([image]) {
  FileHandle.standardError.write("Failed to write image to clipboard\\n".data(using: .utf8)!)
  exit(1)
}
"""
        with tempfile.TemporaryDirectory(prefix="toutiao-clipboard-") as temp_dir:
            swift_path = Path(temp_dir) / "clipboard.swift"
            swift_path.write_text(swift_source, encoding="utf-8")
            return _run_command("swift", [str(swift_path), image_path])

    if system == "Linux":
        mime = "image/png"
        ext = Path(image_path).suffix.lower()
        if ext in {".jpg", ".jpeg"}:
            mime = "image/jpeg"
        elif ext == ".gif":
            mime = "image/gif"
        elif ext == ".webp":
            mime = "image/webp"

        if shutil.which("wl-copy"):
            with open(image_path, "rb") as image_file:
                return _run_command("wl-copy", ["--type", mime], image_file.read())
        if shutil.which("xclip"):
            return _run_command("xclip", ["-selection", "clipboard", "-t", mime, "-i", image_path])
        print("  ⚠️ No clipboard tool found. Install wl-copy or xclip.")
        return False

    if system == "Windows":
        escaped = image_path.replace("'", "''")
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "Add-Type -AssemblyName System.Drawing;"
            f"$img = [System.Drawing.Image]::FromFile('{escaped}');"
            "[System.Windows.Forms.Clipboard]::SetImage($img);"
            "$img.Dispose()"
        )
        return _run_command("powershell.exe", ["-NoProfile", "-Sta", "-Command", ps])

    print(f"  ⚠️ Unsupported clipboard platform: {system}")
    return False


def paste_from_clipboard(page):
    system = platform.system()
    if system == "Darwin":
        if _run_command(
            "osascript",
            [
                "-e",
                'tell application "Google Chrome" to activate',
                "-e",
                'tell application "System Events" to keystroke "v" using command down',
            ],
        ):
            return True
    elif system == "Linux":
        if shutil.which("xdotool") and _run_command("xdotool", ["key", "ctrl+v"]):
            return True
        if shutil.which("ydotool") and _run_command("ydotool", ["key", "29:1", "47:1", "47:0", "29:0"]):
            return True
    elif system == "Windows":
        ps = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^v')"
        if _run_command("powershell.exe", ["-NoProfile", "-Command", ps]):
            return True

    try:
        modifier = "Meta" if system == "Darwin" else "Control"
        page.keyboard.press(f"{modifier}+V")
        return True
    except Exception as e:
        print(f"  ⚠️ Failed to send paste keystroke: {e}")
        return False


def select_placeholder(page, placeholder, retries=3):
    for attempt in range(1, retries + 1):
        selected = page.evaluate(
            """(placeholder) => {
            const editor = document.querySelector('.ProseMirror');
            if (!editor) return false;

            const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
            let node;
            while ((node = walker.nextNode())) {
                const text = node.textContent || '';
                let searchStart = 0;
                let idx;
                while ((idx = text.indexOf(placeholder, searchStart)) !== -1) {
                    const afterIdx = idx + placeholder.length;
                    const charAfter = text[afterIdx];
                    if (charAfter === undefined || !/\\d/.test(charAfter)) {
                        node.parentElement?.scrollIntoView({ block: 'center' });
                        const range = document.createRange();
                        range.setStart(node, idx);
                        range.setEnd(node, afterIdx);
                        const selection = window.getSelection();
                        selection.removeAllRanges();
                        selection.addRange(range);
                        editor.focus();
                        return true;
                    }
                    searchStart = afterIdx;
                }
            }
            return false;
        }""",
            placeholder,
        )
        if selected:
            selected_text = page.evaluate("window.getSelection()?.toString() || ''")
            if selected_text.strip() == placeholder:
                return True
        if attempt < retries:
            time.sleep(0.5)
    return False


def insert_content_images(page, images):
    if not images:
        return True

    print(f"🖼️ Inserting {len(images)} inline image(s)...")
    success = True

    for index, image in enumerate(images, start=1):
        placeholder = image["placeholder"]
        image_path = image["path"]
        print(f"  [{index}/{len(images)}] Replacing {placeholder}...")

        if image_path.startswith(("http://", "https://", "data:")):
            print(f"  ⚠️ Skipping non-local image: {image_path}")
            success = False
            continue

        if not os.path.exists(image_path):
            print(f"  ⚠️ Image file not found: {image_path}")
            success = False
            continue

        if not copy_image_to_clipboard(image_path):
            print("  ⚠️ Failed to copy image to clipboard.")
            success = False
            continue

        if not select_placeholder(page, placeholder):
            print(f"  ⚠️ Could not select placeholder: {placeholder}")
            success = False
            continue

        before_count = page.locator(".ProseMirror img").count()
        page.keyboard.press("Backspace")
        time.sleep(0.3)

        if not paste_from_clipboard(page):
            print("  ⚠️ Failed to paste image.")
            success = False
            continue

        inserted = False
        start = time.time()
        while time.time() - start < 20:
            if page.locator(".ProseMirror img").count() > before_count:
                inserted = True
                break
            time.sleep(1)

        if inserted:
            print("  ✅ Image inserted.")
        else:
            print("  ⚠️ Image insertion was not detected.")
            success = False

    remaining = page.evaluate(
        """() => {
        const text = document.querySelector('.ProseMirror')?.innerText || '';
        return Array.from(text.matchAll(/TTIMGPH_\\d+/g)).map(match => match[0]);
    }"""
    )
    if remaining:
        print(f"  ⚠️ Remaining image placeholders: {', '.join(remaining)}")
        success = False

    return success


def click_locator_with_fallback(locator, description):
    try:
        locator.click(timeout=3000)
        return True
    except Exception as e:
        print(f"  ⚠️ Normal click failed for {description}: {e}")

    try:
        locator.click(force=True, timeout=3000)
        return True
    except Exception as e:
        print(f"  ⚠️ Force click failed for {description}: {e}")

    try:
        locator.evaluate("(el) => el.click()")
        return True
    except Exception as e:
        print(f"  ⚠️ JS click failed for {description}: {e}")
        return False


def click_button_by_text(page, texts, description, timeout_ms=5000):
    end_time = time.time() + timeout_ms / 1000
    while time.time() < end_time:
        result = page.evaluate(
            """(texts) => {
            const buttons = Array.from(document.querySelectorAll('button, .byte-btn'));
            for (const button of buttons) {
                const text = (button.textContent || '').trim();
                if (texts.some(item => text.includes(item))) {
                    button.scrollIntoView({ block: 'center' });
                    button.click();
                    return text || 'clicked';
                }
            }
            return '';
        }""",
            texts,
        )
        if result:
            print(f"  Clicked {description}: {result}")
            return True
        time.sleep(0.5)
    print(f"  ⚠️ Could not find {description}.")
    return False


def should_upload_cover(cover_image_path=None, content_images=None):
    return bool(cover_image_path) and not bool(content_images)


def detect_publish_success(page, timeout_seconds=15, poll_interval=0.5):
    success_selectors = (
        ".byte-message-success",
        ".byte-notification-success",
        "[role='alert']",
    )
    deadline = time.time() + timeout_seconds
    while True:
        for selector in success_selectors:
            try:
                messages = page.locator(selector)
                for index in range(messages.count()):
                    message = messages.nth(index)
                    if not message.is_visible():
                        continue
                    text = (message.inner_text() or "").strip()
                    if "发布成功" in text or "主页查看" in text:
                        return text
            except Exception:
                continue
        if time.time() >= deadline:
            return None
        time.sleep(poll_interval)


def make_screenshot_taker(page, enabled=False, debug_dir=None):
    if not enabled:
        return lambda name: None

    target_dir = Path(debug_dir or "output/toutiao-publisher-debug") / str(int(time.time()))

    def take_screenshot(name):
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            ts = int(time.time())
            filename = target_dir / f"{ts}_{name}.png"
            page.screenshot(path=str(filename))
            print(f"  📸 Saved screenshot: {filename}")
        except Exception as e:
            print(f"  ⚠️ Screenshot failed: {e}")

    return take_screenshot


def publish(
    article,
    mode="manual",
    headless=False,
    no_cover=False,
    debug_screenshots=False,
    debug_dir=None,
    event_callback=None,
):
    """
    Launches a browser to the Toutiao publishing page and automates the posting process.
    """
    title = article.title
    content_html = article.content
    cover_image_path = article.cover_image_path
    final_html = article.html
    content_images = article.images

    # Check if we have valid auth
    auth_manager = AuthManager()
    # Auto-login feature integrated, skipping strict pre-check
    # if not auth_manager.is_authenticated():
    #     print(
    #         "❌ No valid authentication found. Please run 'auth_manager.py setup' first."
    #     )
    #     return False

    if final_html:
        print(f"  HTML preview: {final_html[:100]}...")
    if content_images:
        print(f"  Found {len(content_images)} inline image(s).")

    print(f"🚀 Launching Toutiao Publisher (Headless: {headless})...")

    with sync_playwright() as p:
        try:
            context = BrowserFactory.launch_persistent_context(
                p,
                headless=headless,
                user_data_dir=str(auth_manager.browser_profile_dir),
                lock_path=str(auth_manager.profile_lock_file),
                state_file=str(auth_manager.state_file),
            )
        except ProfileLockedError as e:
            print(f"❌ {e}")
            return PublishResult(False, "profile_locked", str(e))

        # Get the page (persistent context usually has one page open or we create one)
        page = context.pages[0] if context.pages else context.new_page()

        take_screenshot = make_screenshot_taker(
            page,
            enabled=debug_screenshots,
            debug_dir=debug_dir,
        )

        try:
            # Navigate to publishing page
            print(f"🌐 Navigating to {PUBLISH_URL}...")
            try:
                page.goto(PUBLISH_URL, timeout=60000)
                # Relaxed wait condition as networkidle is too strict for Toutiao
                page.wait_for_load_state("domcontentloaded")
            except Exception as e:
                print(f"⚠️ Navigation warning (proceeding anyway): {e}")

            # Check if we were redirected to login
            if is_login_url(page.url):
                print("⚠️ Redirected to login page.")
                if headless:
                    print(
                        "❌ Cannot login in headless mode. Please run without --headless."
                    )
                    return PublishResult(
                        False,
                        "login_required",
                        "Stored login is unavailable in headless mode",
                    )

                print("⏳ Waiting for user login (5 mins)...")
                print("   Please scan QR code in the browser window.")

                start_time = time.time()
                last_probe_time = start_time - AUTH_PROBE_INTERVAL_SECONDS
                logged_in = False
                while time.time() - start_time < 300:
                    try:
                        detected_url = auth_manager.detect_authenticated_url(context)
                        now = time.time()
                        if (
                            not detected_url
                            and now - last_probe_time >= AUTH_PROBE_INTERVAL_SECONDS
                        ):
                            detected_url = auth_manager.detect_authenticated_url(
                                context, include_network_probe=True
                            )
                            last_probe_time = now

                        if detected_url:
                            print(f"✅ Detected login: {detected_url}")
                            auth_manager.save_auth_state(context)
                            logged_in = True
                            break
                    except:
                        pass
                    time.sleep(1)

                if not logged_in:
                    print("❌ Login timeout.")
                    return PublishResult(False, "login_timeout", "Login timed out")

                # If we logged in but are not on publish page, go there
                if PUBLISH_URL not in page.url:
                    print(f"🔄 Redirecting to publish page: {PUBLISH_URL}")
                    page.goto(PUBLISH_URL)
                    page.wait_for_load_state("networkidle")

            print("✅ Publishing page loaded.")
            time.sleep(3)  # Wait a bit for dynamic content

            # Handle potential overlays (e.g. AI assistant drawer)
            print("  Checking for obstructing overlays...")
            try:
                # Common overlay selectors
                overlays = [
                    ".byte-drawer-mask",
                    ".ai-assistant-drawer",
                    ".byte-modal-mask",
                ]
                for sel in overlays:
                    if page.locator(sel).is_visible():
                        print(f"  ⚠️ Found overlay: {sel}. Attempting to close/hide...")
                        # Try clicking it to dismiss
                        page.locator(sel).click(force=True, position={"x": 10, "y": 10})
                        # Or execute JS to remove
                        page.evaluate(f"document.querySelector('{sel}')?.remove()")
                        time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Error handling overlays: {e}")

            # 1. Fill Title
            if title:
                print(f"✍️ Filling title: {title[:20]}...")
                try:
                    title_filled = False

                    # Method A: Placeholder Contains "标题"
                    print("  Attempting to fill title...")
                    title_input = page.locator("textarea").first
                    if title_input.count() > 0:
                        title_input.fill(title)
                        title_filled = True
                        print("  Filled first textarea with title.")
                    else:
                        # Fallback
                        print("  Falling back to placeholder search...")
                        title_input_ph = page.get_by_placeholder("标题", exact=False)
                        if title_input_ph.count() > 0:
                            title_input_ph.first.fill(title)
                            title_filled = True
                            print("  Filled by placeholder.")

                    if not title_filled:
                        print("❌ Could not identify title input.")
                        return PublishResult(
                            False,
                            "title_fill_failed",
                            "Could not identify the title input",
                        )

                except Exception as e:
                    print(f"⚠️ Failed to fill title: {e}")
                    return PublishResult(False, "title_fill_failed", str(e))

                take_screenshot("after_title")

            # 2. Fill Content
            if content_html:
                print("📝 Filling article content with HTML paste...")
                try:
                    # Toutiao uses ProseMirror
                    # Wait for it to appear
                    try:
                        page.wait_for_selector(".ProseMirror", timeout=5000)
                    except Exception:
                        print("  ⚠️ Timeout waiting for .ProseMirror")

                    editor = page.locator(".ProseMirror").first
                    if editor.count() > 0:
                        editor.click()
                        editor.clear()

                        # Prepare plain text version (original markdown or stripped)
                        # We pass 'content_html' (which is actually the raw text/markdown passed to func if conversion failed,
                        # but in our flow 'content_html' arg to publish() IS the markdown if we called it right)
                        # Wait, let's look at the arguments.
                        # publish(content_html=...) receives the raw file content.
                        # Then we convert it to 'final_html'.
                        # So 'content_html' is the plain text source.

                        # Use robust argument passing to avoid JS parsing errors
                        print("  Attempting content fill via execCommand...")

                        # Pass data safely to JS environment
                        eval_args = {"html": final_html}

                        filled = page.evaluate(
                            """(data) => {
                            const editor = document.querySelector('.ProseMirror');
                            if (editor) {
                                editor.focus();
                                // Try insertHTML first - usually most reliable for WYSIWYG
                                const success = document.execCommand('insertHTML', false, data.html);
                                if (!success) {
                                    // Fallback to clipboard event
                                    console.log('execCommand failed, trying clipboard event');
                                    const clipboardData = new DataTransfer();
                                    clipboardData.setData('text/html', data.html);
                                    // Create paste event
                                    const pasteEvent = new ClipboardEvent('paste', {
                                        bubbles: true,
                                        cancelable: true,
                                        clipboardData: clipboardData
                                    });
                                    editor.dispatchEvent(pasteEvent);
                                }
                                return true;
                            }
                            return false;
                        }""",
                            eval_args,
                        )

                        if not filled:
                            return PublishResult(
                                False,
                                "content_fill_failed",
                                "ProseMirror rejected the article content",
                            )

                        time.sleep(3)
                        print("✅ Content pasted via JS event.")

                        # Verify Draft Saved Status
                        print("  Checking save status...")
                        saved_successfully = False
                        for _ in range(10):
                            if page.get_by_text("保存失败").is_visible():
                                print("❌ Alert: 'Save Failed' detected!")
                                take_screenshot("save_failed")

                                # Attempt retrieval: Click "Save Draft" button if exists
                                save_btn = page.get_by_text("保存草稿")
                                if save_btn.is_visible():
                                    print("  Clicking 'Save Draft' manually...")
                                    save_btn.click()
                                else:
                                    # Try typing a space
                                    print("  Typing space to trigger autosave...")
                                    editor.type(" ")
                                time.sleep(3)

                            if page.get_by_text("草稿已保存").is_visible():
                                print("✅ Draft saved successfully.")
                                saved_successfully = True
                                break
                            time.sleep(1)

                        if not saved_successfully:
                            print(
                                "⚠️ Warning: content might not be saved. Publishing might fail."
                            )
                            if mode == "auto":
                                return PublishResult(
                                    False,
                                    "draft_not_saved",
                                    "Toutiao did not confirm that the draft was saved",
                                )

                    else:
                        print("⚠️ ProseMirror editor not found.")
                        return PublishResult(
                            False,
                            "content_fill_failed",
                            "ProseMirror editor was not found",
                        )
                except Exception as e:
                    print(f"⚠️ Failed to fill content: {e}")
                    return PublishResult(False, "content_fill_failed", str(e))

                take_screenshot("after_content")

                if content_images:
                    try:
                        if not insert_content_images(page, content_images):
                            return PublishResult(
                                False,
                                "inline_image_failed",
                                "One or more inline images were not inserted",
                            )
                    except Exception as e:
                        print(f"⚠️ Failed to insert inline images: {e}")
                        return PublishResult(False, "inline_image_failed", str(e))
                    take_screenshot("after_inline_images")

            # 3. Cover Image Processing
            if cover_image_path and content_images:
                print("🖼️ Article has inline images; skipping explicit cover upload.")

            if should_upload_cover(cover_image_path, content_images):
                print(f"🖼️ Uploading cover image: {cover_image_path}...")
                try:
                    # check if file exists
                    if not os.path.exists(cover_image_path):
                        print(f"  ❌ Cover image not found at: {cover_image_path}")
                    else:
                        # 3.1 Click "Add Cover" area
                        print("  Clicking 'Add Cover' area...")
                        add_cover_btn = page.locator("div.article-cover-add").first
                        if add_cover_btn.is_visible():
                            add_cover_btn.click()
                        else:
                            # Try finding by text if class selector fails
                            page.locator("div, span").filter(
                                has_text="添加封面"
                            ).last.click()
                        time.sleep(1)

                        # 3.2 Select "Upload Local Image" tab/button
                        print("  Clicking 'Upload Local' button...")
                        # Try the specific class from reference
                        upload_tab = page.locator(
                            "div.btn-upload-handle.upload-handler"
                        ).first
                        if upload_tab.is_visible():
                            click_locator_with_fallback(upload_tab, "Upload Local button")
                        else:
                            # Fallback text search
                            upload_text = page.locator("div, span").filter(
                                has_text="本地上传"
                            ).last
                            click_locator_with_fallback(upload_text, "本地上传 button")
                        time.sleep(1)

                        # 3.3 Upload File
                        print("  Setting file input...")
                        # Playwright handles file uploads gracefully with set_input_files
                        # We look for the file input inside the upload handler or globally
                        file_input = page.locator("input[type='file']").first
                        file_input.set_input_files(cover_image_path)
                        print("  File sent to input.")

                        # 3.4 Confirm Upload
                        print("  Waiting for confirm button...")
                        # Reference script used: button[data-e2e='imageUploadConfirm-btn']
                        confirm_btn = page.locator(
                            "button[data-e2e='imageUploadConfirm-btn']"
                        )

                        # Wait for it to be clickable (upload processing)
                        try:
                            confirm_btn.wait_for(state="visible", timeout=30000)
                            # Sometimes button is disabled while processing
                            time.sleep(2)
                            if not click_locator_with_fallback(confirm_btn, "upload confirm button"):
                                raise RuntimeError("upload confirm click failed")
                            print("  ✅ Cover image uploaded and confirmed.")
                        except Exception as e:
                            print(f"  ⚠️ Confirm button issue: {e}")
                            if not click_button_by_text(page, ["确定", "确认"], "fallback upload confirm button"):
                                raise

                        time.sleep(2)
                        take_screenshot("cover_uploaded")

                except Exception as e:
                    print(f"⚠️ Failed to upload cover: {e}")
                    return PublishResult(False, "cover_upload_failed", str(e))

            elif no_cover:
                print("🖼️ Selecting 'No Cover' (无封面) mode...")
                try:
                    # Robust selection for No Cover
                    no_cover_loc = (
                        page.locator("div, span, label").filter(has_text="无封面").last
                    )
                    if no_cover_loc.is_visible():
                        no_cover_loc.click()
                        print("  Clicked '无封面' option.")
                    else:
                        # Fallback: try checking if a radio exists
                        page.locator("input[type='radio'][value='0']").click()

                    time.sleep(2)
                    take_screenshot("cover_mode_selected")
                except Exception as e:
                    print(f"⚠️ Failed to select no cover: {e}")
                    return PublishResult(False, "cover_mode_failed", str(e))

            # 4. Final Publish Step (Optimized Two-Step Flow)
            if mode == "auto":
                print("🚀 Submitting article (Final Step)...")
                try:
                    take_screenshot("before_publish_click")

                    # Step 4.1: Click "Preview & Publish" or "Publish"
                    print("  Step 1: Clicking initial Publish/Preview button...")

                    # Strategy: Try specific text locators first
                    # "预览并发布" (Preview & Publish) is preferred
                    initial_btn = (
                        page.locator("button").filter(has_text="预览并发布").last
                    )
                    if not initial_btn.is_visible():
                        print(
                            "  'Preview & Publish' not found, trying generic 'Publish'..."
                        )
                        # Exclude modal buttons logic can be complex in generic selectors,
                        # but usually the main publish button is prominent
                        initial_btn = (
                            page.locator("button").filter(has_text="发布").last
                        )

                    if initial_btn.is_visible() and initial_btn.is_enabled():
                        initial_btn.click()
                        print("  ✅ Initial button clicked.")
                    else:
                        print(
                            "  ⚠️ Could not find initial publish button! Attempting blind JS click on .publish-btn..."
                        )
                        page.evaluate("document.querySelector('.publish-btn')?.click()")

                    # Step 4.2: Wait for potential preview/modal
                    print("  Waiting for interface response (10s)...")
                    time.sleep(10)

                    # Step 4.3: Final Confirmation Button
                    print("  Step 2: Looking for Final Confirm button...")
                    # Reference script indicates class: .publish-btn-last
                    final_btn = page.locator(".publish-btn-last").first

                    if final_btn.is_visible():
                        print("  Found .publish-btn-last. Clicking...")
                        final_btn.click()
                    else:
                        # Fallback: Look for the primary button in a modal
                        print(
                            "  Main locator failed. Checking for modal confirmation..."
                        )
                        modal_confirm = (
                            page.locator(".byte-modal .byte-btn-primary")
                            .filter(has_text="确定")
                            .or_(
                                page.locator(".byte-modal .byte-btn-primary").filter(
                                    has_text="确认发布"
                                )
                            )
                            .last
                        )

                        if modal_confirm.is_visible():
                            print("  Found modal confirm button. Clicking...")
                            modal_confirm.click()
                        else:
                            print(
                                "  ❌ Critical: Could not find final confirmation button!"
                            )
                            return PublishResult(
                                False,
                                "publish_failed",
                                "Could not find the final confirmation button",
                            )

                    # Success Check
                    print("  Checking for success indicators...")
                    success_indicator = detect_publish_success(
                        page,
                        timeout_seconds=20,
                    )
                    take_screenshot("final_result")
                    if success_indicator:
                        print(
                            f"✨ Publish Successful! Found text: {success_indicator}"
                        )
                        return PublishResult(
                            True,
                            "published",
                            "Confirmed by Toutiao success indicator: "
                            f"{success_indicator}",
                        )

                    return PublishResult(
                        False,
                        "publish_unconfirmed",
                        "Final button was clicked but no success indicator was found",
                    )

                except Exception as e:
                    print(f"❌ Failed during publish sequence: {e}")
                    import traceback

                    traceback.print_exc()
                    return PublishResult(False, "publish_failed", str(e))
            else:
                print("🛑 Manual review mode: skipping final publish click.")
                print("   Please review the article in Chrome and click Publish manually.")
                if headless:
                    print("   Headless mode cannot stay open for manual publishing.")
                else:
                    print("   Press Ctrl+C in this terminal after you are done.")
                    if event_callback:
                        event_callback(
                            PublishResult(
                                True,
                                "awaiting_manual_review",
                                "Draft is ready for user review in Chrome",
                            )
                        )
                    try:
                        while True:
                            time.sleep(5)
                    except KeyboardInterrupt:
                        print("\n✅ Manual review finished.")

            print("✨ Operation completed.")
            return PublishResult(
                True,
                "manual_review_finished",
                "User ended the manual review session",
            )

        except Exception as e:
            print(f"❌ Error during publishing: {e}")
            import traceback

            traceback.print_exc()
            return PublishResult(False, "publish_failed", str(e))
        finally:
            if not headless and mode == "auto":
                print("browser open for inspection. Closing in 60s...")
                time.sleep(60)
            if context:
                try:
                    context.close()
                except Exception as e:
                    print(f"⚠️ Browser context close warning: {e}")


def _result_payload(result, mode):
    return {
        "ok": result.ok,
        "status": result.status,
        "message": result.message,
        "mode": mode,
    }


def main(argv=None):
    cli_argv = list(argv if argv is not None else sys.argv[1:])
    parser_class = configure_json_argument_parser(cli_argv)
    parser = parser_class(description="Toutiao Article Publisher")
    parser.add_argument("--title", help="Article title")
    content_group = parser.add_mutually_exclusive_group()
    content_group.add_argument(
        "--content",
        "--content-file",
        dest="content_file",
        help="Path to a UTF-8 Markdown file",
    )
    content_group.add_argument(
        "--content-text",
        help="Article body provided directly on the command line",
    )
    parser.add_argument("--cover", help="Path to cover image")
    parser.add_argument(
        "--mode",
        choices=PUBLISH_MODES,
        help="manual: fill and wait; auto: publish; validate: preflight only",
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode (no UI)"
    )
    parser.add_argument(
        "--no-cover", action="store_true", help="Select 'No Cover' option"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Paste content as raw text (no HTML conversion)",
    )
    parser.add_argument(
        "--auto-publish",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--debug-screenshots",
        action="store_true",
        help="Save step-by-step debug screenshots under output/toutiao-publisher-debug/",
    )
    parser.add_argument(
        "--debug-dir",
        help="Directory for debug screenshots when --debug-screenshots is enabled",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write newline-delimited JSON events to stdout",
    )

    args = parser.parse_args(cli_argv)
    if args.auto_publish and args.dry_run:
        parser.error("--auto-publish and --dry-run cannot be combined")
    if args.auto_publish and args.mode not in {None, "auto"}:
        parser.error("--auto-publish conflicts with the selected --mode")
    if args.dry_run and args.mode not in {None, "validate"}:
        parser.error("--dry-run conflicts with the selected --mode")

    mode = args.mode or (
        "auto" if args.auto_publish else "validate" if args.dry_run else "manual"
    )
    json_stream = sys.stdout
    output_context = (
        contextlib.redirect_stdout(sys.stderr)
        if args.json
        else contextlib.nullcontext()
    )

    def emit_result(result):
        if args.json:
            print(
                json.dumps(_result_payload(result, mode), ensure_ascii=False),
                file=json_stream,
                flush=True,
            )

    with output_context:
        try:
            article = prepare_article(
                title=args.title,
                content_file=args.content_file,
                content_text=args.content_text,
                cover_image_path=args.cover,
                mode=mode,
                headless=args.headless,
                no_cover=args.no_cover,
                raw=args.raw,
            )
        except (InputValidationError, UnicodeError, OSError) as e:
            result = PublishResult(False, "invalid_input", str(e))
            print(f"❌ Input validation failed: {e}")
            emit_result(result)
            return EXIT_INVALID_INPUT

        if mode == "validate":
            result = PublishResult(
                True,
                "input_valid",
                f"Preflight passed with {len(article.images)} inline image(s)",
            )
            print("✅ Input preflight passed. Browser was not opened.")
            emit_result(result)
            return EXIT_OK

        try:
            result = publish(
                article=article,
                mode=mode,
                headless=args.headless,
                no_cover=args.no_cover,
                debug_screenshots=args.debug_screenshots,
                debug_dir=args.debug_dir,
                event_callback=emit_result,
            )
        except Exception as e:
            result = PublishResult(False, "publish_failed", str(e))
            print(f"❌ Publisher failed: {e}")

        emit_result(result)
        if result.ok:
            return EXIT_OK
        if result.status == "profile_locked":
            return EXIT_PROFILE_LOCKED
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
