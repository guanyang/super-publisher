import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from md2html import convert_with_images


class MarkdownImageConversionTest(unittest.TestCase):
    def test_replaces_local_images_with_placeholders_and_returns_metadata(self):
        markdown = "Intro\n\n![Chart](assets/chart.png)\n\nOutro"

        result = convert_with_images(markdown, base_dir=Path("/tmp/article"))

        self.assertIn("<p>Intro</p>", result.html)
        self.assertIn("<p>TTIMGPH_0</p>", result.html)
        self.assertIn("<p>Outro</p>", result.html)
        self.assertEqual(
            result.images,
            [
                {
                    "placeholder": "TTIMGPH_0",
                    "path": str(Path("/tmp/article/assets/chart.png").resolve()),
                    "alt": "Chart",
                }
            ],
        )

    def test_supports_common_blog_markdown(self):
        markdown = """# Guide

Read [the docs](https://example.com) and use `code`.

1. First
2. Second

> Important note

| Name | Value |
| --- | --- |
| A | **Bold** |
"""

        result = convert_with_images(markdown)

        self.assertIn('<a href="https://example.com">the docs</a>', result.html)
        self.assertIn("<code>code</code>", result.html)
        self.assertIn("<ol>", result.html)
        self.assertIn("<blockquote>", result.html)
        self.assertIn("<table>", result.html)
        self.assertIn("<strong>Bold</strong>", result.html)

    def test_supports_angle_bracket_image_paths_with_spaces(self):
        result = convert_with_images(
            "![Chart](<assets/my chart.png>)",
            base_dir=Path("/tmp/article"),
        )

        self.assertEqual(
            result.images[0]["path"],
            str(Path("/tmp/article/assets/my chart.png").resolve()),
        )

    def test_does_not_extract_images_from_tilde_code_fences(self):
        result = convert_with_images(
            "~~~markdown\n![Example](assets/example.png)\n~~~"
        )

        self.assertEqual(result.images, [])
        self.assertIn("![Example](assets/example.png)", result.html)


if __name__ == "__main__":
    unittest.main()
