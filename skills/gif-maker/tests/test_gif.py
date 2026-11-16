import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

spec = importlib.util.spec_from_file_location(
    "gif_maker", Path(__file__).resolve().parents[1] / "scripts/make_gif.py")
gif = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gif)


class GifTests(unittest.TestCase):
    def test_invalid_fps_and_existing_output_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out.gif"
            with self.assertRaises(ValueError):
                gif.create_gif(temporary, str(output), fps=0)
            output.write_bytes(b"existing")
            with self.assertRaises(ValueError):
                gif.create_gif(temporary, str(output))
            self.assertEqual(output.read_bytes(), b"existing")

    def test_unavailable_compressor_fails_without_changing_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "original.gif"
            Image.new("RGB", (240, 240), "brown").save(source)
            original = source.read_bytes()
            with patch.object(gif.subprocess, "run", side_effect=FileNotFoundError("gifsicle")):
                with self.assertRaises(ValueError):
                    gif.compress_gif(str(source), str(source), target_size_kb=0.001)
            self.assertEqual(source.read_bytes(), original)

    def test_dimension_changing_compression_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "original.gif"
            Image.new("RGB", (240, 240), "brown").save(source)
            original = source.read_bytes()
            def fake_compressor(command, **kwargs):
                self.assertNotIn("--scale", command)
                Image.new("RGB", (120, 120), "brown").save(command[-1])
            with patch.object(gif.subprocess, "run", side_effect=fake_compressor):
                with self.assertRaises(ValueError):
                    gif.compress_gif(str(source), str(source), target_size_kb=0.001)
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
