import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from publisher import should_upload_cover


class CoverUploadPolicyTest(unittest.TestCase):
    def test_skips_cover_upload_when_article_has_inline_images(self):
        self.assertFalse(
            should_upload_cover(
                cover_image_path="cover.png",
                content_images=[{"placeholder": "TTIMGPH_0"}],
            )
        )

    def test_uploads_cover_when_article_has_no_inline_images(self):
        self.assertTrue(
            should_upload_cover(
                cover_image_path="cover.png",
                content_images=[],
            )
        )


if __name__ == "__main__":
    unittest.main()
