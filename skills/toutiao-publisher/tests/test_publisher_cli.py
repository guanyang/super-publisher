import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import publisher


class PublisherInputTest(unittest.TestCase):
    def test_argparse_error_is_json_when_requested(self):
        stdout = StringIO()
        stderr = StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                publisher.main(["--mode", "unknown", "--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(raised.exception.code, publisher.EXIT_INVALID_INPUT)
        self.assertEqual(payload["status"], "invalid_arguments")

    def test_rejects_manual_headless_mode(self):
        with self.assertRaisesRegex(publisher.InputValidationError, "headless"):
            publisher.prepare_article(mode="manual", headless=True)

    def test_rejects_invalid_title_before_opening_browser(self):
        with self.assertRaisesRegex(publisher.InputValidationError, "2-30"):
            publisher.prepare_article(
                title="x",
                content_text="body",
                mode="manual",
            )

    def test_content_option_is_a_file_and_missing_file_fails(self):
        with self.assertRaisesRegex(publisher.InputValidationError, "not found"):
            publisher.prepare_article(
                title="Valid title",
                content_file="missing.md",
                mode="manual",
            )

    def test_rejects_missing_inline_image_during_preflight(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            article_path = Path(temp_dir) / "article.md"
            article_path.write_text("![missing](images/missing.png)")

            with self.assertRaisesRegex(publisher.InputValidationError, "Inline image"):
                publisher.prepare_article(
                    title="Valid title",
                    content_file=article_path,
                    mode="validate",
                )

    def test_validate_mode_converts_without_opening_browser(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            article_path = Path(temp_dir) / "article.md"
            article_path.write_text("# Heading\n\nBody")

            article = publisher.prepare_article(
                title="Valid title",
                content_file=article_path,
                mode="validate",
            )

            self.assertIn("<h1>Heading</h1>", article.html)
            self.assertEqual(article.content_base_dir, Path(temp_dir).resolve())

    def test_json_failure_is_machine_readable_and_nonzero(self):
        stdout = StringIO()
        stderr = StringIO()
        result = publisher.PublishResult(False, "publish_failed", "UI changed")

        with (
            patch("publisher.prepare_article") as prepare,
            patch("publisher.publish", return_value=result),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            prepare.return_value = publisher.PreparedArticle(
                title=None,
                content=None,
                content_base_dir=Path.cwd(),
                cover_image_path=None,
                html="",
                images=[],
            )
            exit_code = publisher.main(["--json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, publisher.EXIT_FAILURE)
        self.assertEqual(payload["status"], "publish_failed")


class FakeTextLocator:
    def __init__(self, text="", visible=True):
        self.text = text
        self.visible = visible

    def is_visible(self):
        return self.visible

    def inner_text(self):
        return self.text


class FakeTextLocators:
    def __init__(self, texts):
        self.items = [FakeTextLocator(text) for text in texts]

    def count(self):
        return len(self.items)

    def nth(self, index):
        return self.items[index]


class FakeSuccessPage:
    def __init__(self, toast_texts=None, page_texts=None):
        self.toast_texts = list(toast_texts or [])
        self.page_texts = set(page_texts or [])

    def locator(self, _selector):
        return FakeTextLocators(self.toast_texts)


class PublisherSuccessTest(unittest.TestCase):
    def test_success_requires_explicit_toutiao_indicator(self):
        self.assertEqual(
            publisher.detect_publish_success(
                FakeSuccessPage(toast_texts={"发布成功"}),
                timeout_seconds=0,
            ),
            "发布成功",
        )
        self.assertIsNone(
            publisher.detect_publish_success(
                FakeSuccessPage(page_texts={"发布成功", "主页查看"}),
                timeout_seconds=0,
            )
        )


if __name__ == "__main__":
    unittest.main()
