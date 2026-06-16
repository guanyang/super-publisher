#!/usr/bin/env python3
"""
Publisher script for Toutiao
Navigates to the publish page with authenticated session.
"""

import sys
import argparse
import time
from pathlib import Path
import os
import platform
import shutil
import subprocess
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import PUBLISH_URL
from patchright.sync_api import sync_playwright
from auth_manager import AuthManager
from browser_utils import BrowserFactory


from md2html import convert_with_images


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
    title=None,
    content_html=None,
    content_base_dir=None,
    cover_image_path=None,
    dry_run=False,
    headless=False,
    no_cover=False,
    raw=False,
    auto_publish=False,
    debug_screenshots=False,
    debug_dir=None,
):
    """
    Launches a browser to the Toutiao publishing page and automates the posting process.
    """
    # Optimize title to meet Toutiao constraints (2-30 chars)
    if title:
        original_title = title
        if len(title) > 30:
            title = title[:30]
            print(
                f"⚠️ Title optimized (truncated to 30 chars): '{original_title}' -> '{title}'"
            )
        elif len(title) < 2:
            title = f"{title}..."
            print(
                f"⚠️ Title optimized (extended to min 2 chars): '{original_title}' -> '{title}'"
            )

    # Check if we have valid auth
    auth_manager = AuthManager()
    # Auto-login feature integrated, skipping strict pre-check
    # if not auth_manager.is_authenticated():
    #     print(
    #         "❌ No valid authentication found. Please run 'auth_manager.py setup' first."
    #     )
    #     return False

    # Convert Markdown to HTML if content is provided
    final_html = ""
    content_images = []
    if content_html and not raw:
        print("🔄 Converting Markdown to HTML...")
        try:
            converted = convert_with_images(content_html, base_dir=content_base_dir)
            final_html = converted.html
            content_images = converted.images
            print(f"  HTML preview: {final_html[:100]}...")
            if content_images:
                print(f"  Found {len(content_images)} inline image(s).")
        except Exception as e:
            print(f"⚠️ Conversion failed, using raw text: {e}")
            final_html = content_html
    elif content_html:
        final_html = content_html

    print(f"🚀 Launching Toutiao Publisher (Headless: {headless})...")

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=headless)

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
            if "auth/page/login" in page.url or "sso.toutiao.com" in page.url:
                print("⚠️ Redirected to login page.")
                if headless:
                    print(
                        "❌ Cannot login in headless mode. Please run without --headless."
                    )
                    return False

                print("⏳ Waiting for user login (5 mins)...")
                print("   Please scan QR code in the browser window.")

                start_time = time.time()
                logged_in = False
                while time.time() - start_time < 300:
                    try:
                        # Check indicators
                        if (
                            "profile_v4" in page.url
                            or "mp.toutiao.com/graphic/publish" in page.url
                        ):
                            print("✅ Detected login! Saving state...")
                            # Save state for future use
                            try:
                                state_path = Path("data/browser_state/state.json")
                                state_path.parent.mkdir(parents=True, exist_ok=True)
                                context.storage_state(path=str(state_path))
                                print("   State saved.")
                            except Exception as e:
                                print(f"   Warning: Could not save state: {e}")

                            logged_in = True
                            break

                        # Also check if we are back on publish page
                        if PUBLISH_URL in page.url:
                            logged_in = True
                            break
                    except:
                        pass
                    time.sleep(1)

                if not logged_in:
                    print("❌ Login timeout.")
                    return False

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

                except Exception as e:
                    print(f"⚠️ Failed to fill title: {e}")

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

                    else:
                        print("⚠️ ProseMirror editor not found.")
                except Exception as e:
                    print(f"⚠️ Failed to fill content: {e}")

                take_screenshot("after_content")

                if content_images:
                    try:
                        insert_content_images(page, content_images)
                    except Exception as e:
                        print(f"⚠️ Failed to insert inline images: {e}")
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

            # 4. Final Publish Step (Optimized Two-Step Flow)
            if auto_publish and not dry_run:
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
                            return False

                    # Success Check
                    print("  Checking for success indicators...")
                    time.sleep(5)
                    take_screenshot("final_result")

                    # Common success texts
                    success_texts = ["发布成功", "主页查看", "已发布"]
                    for text in success_texts:
                        if page.get_by_text(text).is_visible():
                            print(f"✨ Publish Successful! Found text: {text}")
                            return True

                    return (
                        True  # Assume success if we clicked final button without error
                    )

                except Exception as e:
                    print(f"❌ Failed during publish sequence: {e}")
                    import traceback

                    traceback.print_exc()
                    return False
            else:
                print("🛑 Manual review mode: skipping final publish click.")
                print("   Please review the article in Chrome and click Publish manually.")
                if headless:
                    print("   Headless mode cannot stay open for manual publishing.")
                else:
                    print("   Press Ctrl+C in this terminal after you are done.")
                    try:
                        while True:
                            time.sleep(5)
                    except KeyboardInterrupt:
                        print("\n✅ Manual review finished.")

            print("✨ Operation completed.")
            return True

        except Exception as e:
            print(f"❌ Error during publishing: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            if not headless and auto_publish:
                print("browser open for inspection. Closing in 60s...")
                time.sleep(60)
            if context:
                try:
                    context.close()
                except Exception as e:
                    print(f"⚠️ Browser context close warning: {e}")


def main():
    parser = argparse.ArgumentParser(description="Toutiao Article Publisher")
    parser.add_argument("--title", help="Article title")
    parser.add_argument("--content", help="Article content (string or file path)")
    parser.add_argument("--cover", help="Path to cover image")
    parser.add_argument(
        "--dry-run", action="store_true", help="Fill fields but do not publish"
    )
    # Add headless and no-cover arguments
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
        help="Click the final publish buttons automatically after filling the article",
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

    args = parser.parse_args()

    content = args.content
    content_base_dir = Path.cwd()
    if content and os.path.exists(content):
        content_path = Path(content).resolve()
        content_base_dir = content_path.parent
        with open(content_path, "r", encoding="utf-8") as f:
            content = f.read()

    publish(
        title=args.title,
        content_html=content,
        content_base_dir=content_base_dir,
        cover_image_path=args.cover,
        dry_run=args.dry_run,
        headless=args.headless,
        no_cover=args.no_cover,
        raw=args.raw,
        auto_publish=args.auto_publish,
        debug_screenshots=args.debug_screenshots,
        debug_dir=args.debug_dir,
    )


if __name__ == "__main__":
    main()
