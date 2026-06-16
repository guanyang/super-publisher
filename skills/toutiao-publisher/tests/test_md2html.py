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


if __name__ == "__main__":
    unittest.main()
