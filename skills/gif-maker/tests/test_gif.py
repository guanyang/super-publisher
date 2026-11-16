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


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.frames = self.root / "frames"
        self.frames.mkdir()

    def solid_frames(self, names=("1.png", "2.png", "10.png")):
        for name, color in zip(names, ["red", "green", "blue"]):
            image = Image.new("RGBA", (40, 40), color)
            if Path(name).suffix.lower() in {".jpg", ".jpeg"}:
                image = image.convert("RGB")
            image.save(self.frames / name)

    def read_report(self, stem="out"):
        import json
        return json.loads((self.root / f"{stem}.animation.json").read_text())

    def test_natural_order_across_formats_and_case(self):
        self.solid_frames(("1.PNG", "2.webp", "10.jpeg"))
        gif.create_gif(self.frames, self.root / "out.gif", fps=10)
        decoded = gif.decode_gif(self.root / "out.gif")
        colors = [f.getpixel((20, 20))[:3] for f in decoded["frames"]]
        self.assertEqual([max(range(3), key=lambda i: c[i]) for c in colors], [0, 1, 2])
        self.assertEqual([Path(p).name for p in self.read_report()["input_order"]],
                         ["1.PNG", "2.webp", "10.jpeg"])

    def test_transparent_noise_and_reserved_index_do_not_damage_opaque_colors(self):
        from PIL import ImageDraw
        for i in range(2):
            frame = Image.new("RGBA", (40, 40))
            draw = ImageDraw.Draw(frame)
            draw.rectangle((10+i, 10, 28+i, 28), fill="brown")
            draw.point((1, 1), fill=(255, 0, 0, 1))
            draw.point((2, 1), fill=(0, 0, 255, 127))
            draw.point((3, 1), fill=(0, 0, 255, 128))
            draw.point((4, 1), fill=(0, 0, 0, 255))
            draw.point((5, 1), fill=(255, 0, 255, 255))
            frame.save(self.frames / f"{i}.png")
        gif.create_gif(self.frames, self.root / "out.gif", fps=10)
        for frame in gif.decode_gif(self.root / "out.gif")["frames"]:
            self.assertEqual(frame.getpixel((1, 1))[3], 0)
            self.assertEqual(frame.getpixel((2, 1))[3], 0)
            self.assertEqual(frame.getpixel((3, 1))[3], 255)
            self.assertEqual(frame.getpixel((4, 1)), (0, 0, 0, 255))
            self.assertEqual(frame.getpixel((5, 1)), (255, 0, 255, 255))
        gif.create_gif(self.frames, self.root / "higher.gif", alpha_cutoff=150)
        self.assertEqual(gif.decode_gif(self.root / "higher.gif")["frames"][0].getpixel((3, 1))[3], 0)

    def test_24fps_preserves_one_second_over_24_frames(self):
        for i in range(24):
            Image.new("RGB", (20, 20), (i*10, 10, 100)).save(self.frames / f"{i}.png")
        gif.create_gif(self.frames, self.root / "out.gif", fps=24)
        report = self.read_report()
        self.assertEqual(report["duration_ms"], 1000)
        self.assertEqual(set(report["playback_durations_ms"]), {40, 50})
        self.assertAlmostEqual(report["requested_duration_ms"], 1000)

    def test_sequence_holds_survive_identical_frame_merging(self):
        self.solid_frames()
        gif.create_gif(self.frames, self.root / "out.gif", sequence=[1, 3, 2, 2, 1],
                       durations=[100, 200, 350, 50, 100])
        decoded = gif.decode_gif(self.root / "out.gif")
        elapsed, timeline = 0, []
        for frame, delay in zip(decoded["frames"], decoded["durations"]):
            timeline.append((elapsed, elapsed+delay, frame.getpixel((20, 20))[:3]))
            elapsed += delay
        self.assertEqual(elapsed, 800)
        for time, expected in [(0, (255, 0, 0)), (150, (0, 0, 255)),
                               (500, (0, 128, 0)), (750, (255, 0, 0))]:
            self.assertEqual(next(c for start, end, c in timeline if start <= time < end), expected)
        report = self.read_report()
        self.assertEqual(report["source_frame_count"], 3)
        self.assertEqual(report["playback_sequence"], [1, 3, 2, 2, 1])
        self.assertLessEqual(report["encoded_frame_count"], 5)

    def test_bad_frame_stops_without_publishing(self):
        self.solid_frames()
        (self.frames / "2.png").write_bytes(b"broken PNG")
        with self.assertRaisesRegex(ValueError, "2.png"):
            gif.create_gif(self.frames, self.root / "out.gif")
        self.assertFalse(list(self.root.glob("out.*")))

    def test_compression_failure_leaves_no_output_or_sidecars(self):
        self.solid_frames()
        original = (self.frames / "1.png").read_bytes()
        with patch.object(gif.subprocess, "run", side_effect=FileNotFoundError("gifsicle")):
            with self.assertRaises(ValueError):
                gif.create_gif(self.frames, self.root / "out.gif", max_size_kb=0.001)
        self.assertFalse(list(self.root.glob("out.*")))
        self.assertFalse(list(self.root.glob(".gif-*")))
        self.assertEqual((self.frames / "1.png").read_bytes(), original)

    def test_optional_optimizer_can_be_missing_when_output_already_fits(self):
        self.solid_frames()
        with patch.object(gif.subprocess, "run", side_effect=FileNotFoundError("gifsicle")):
            gif.create_gif(self.frames, self.root / "out.gif", max_size_kb=950, optimize=True)
        report = self.read_report()
        self.assertEqual(report["compression"]["method"], "none")
        self.assertIn("unavailable", report["compression"]["warning"])
        self.assertTrue(report["local_checks_passed"])

    def test_nondivisible_transparent_sprite_uses_common_canvas(self):
        from PIL import ImageDraw
        sheet = Image.new("RGBA", (101, 63))
        draw = ImageDraw.Draw(sheet)
        for row in range(2):
            for col in range(3):
                x, y = round(col*101/3)+8, round(row*63/2)+7
                draw.rectangle((x, y, x+14, y+15), fill=(50+row*90, 30+col*70, 20, 255))
        source = self.root / "sheet.png"
        sheet.save(source)
        gif.create_gif(source, self.root / "out.gif", layout="2x3", size=64)
        report = self.read_report()
        self.assertEqual(report["source_frame_count"], 6)
        self.assertEqual(report["size"], [64, 64])
        self.assertEqual(len(report["grid_cuts"]["x"]), 4)
        self.assertEqual(len(report["grid_cuts"]["y"]), 3)

    def test_gap_search_preserves_art_and_nominal_frame_coordinates(self):
        from PIL import ImageDraw
        sheet = Image.new("RGBA", (100, 50))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((10, 15, 52, 35), fill="red")
        draw.rectangle((66, 15, 90, 35), fill="blue")
        source = self.root / "sheet.png"
        sheet.save(source)
        gif.create_gif(source, self.root / "out.gif", layout="1x2")
        decoded = gif.decode_gif(self.root / "out.gif")
        self.assertGreater(self.read_report()["grid_cuts"]["x"][1], 52)
        self.assertEqual(decoded["frames"][0].getchannel("A").getbbox(), (10, 15, 53, 36))
        self.assertEqual(decoded["frames"][1].getchannel("A").getbbox(), (16, 15, 41, 36))
        with self.assertRaises(ValueError):
            gif.create_gif(source, self.root / "cut.gif", layout="1x2", boundaries={"x": [0, 50, 100]})
        self.assertFalse(list(self.root.glob("cut.*")))

    def test_global_crop_and_bottom_anchor_preserve_real_motion(self):
        from PIL import ImageDraw
        for i, box in enumerate([(30, 50, 50, 70), (40, 20, 60, 40)]):
            im = Image.new("RGBA", (100, 100))
            ImageDraw.Draw(im).rectangle(box, fill="brown")
            im.save(self.frames / f"{i}.png")
        gif.create_gif(self.frames, self.root / "out.gif", size=100, anchor="bottom")
        decoded = gif.decode_gif(self.root / "out.gif")
        a, b = [f.getchannel("A").getbbox() for f in decoded["frames"]]
        scale = self.read_report()["transform"]["scale"]
        self.assertAlmostEqual(b[0]-a[0], 10*scale, delta=1)
        self.assertAlmostEqual(b[1]-a[1], -30*scale, delta=1)
        self.assertTrue(all(f.size == (100, 100) for f in decoded["frames"]))

    def test_static_overlay_is_reused_and_dimensions_are_checked(self):
        self.solid_frames()
        overlay = Image.new("RGBA", (64, 64))
        overlay.putpixel((2, 2), (255, 255, 0, 255))
        overlay.save(self.root / "label.png")
        gif.create_gif(self.frames, self.root / "out.gif", size=64, overlay=self.root / "label.png")
        for frame in gif.decode_gif(self.root / "out.gif")["frames"]:
            self.assertEqual(frame.getpixel((2, 2)), (255, 255, 0, 255))
        with self.assertRaisesRegex(ValueError, "overlay"):
            gif.create_gif(self.frames, self.root / "bad.gif", overlay=self.root / "label.png")

    def test_invalid_timing_sequence_and_animated_inputs_fail(self):
        self.solid_frames()
        for kwargs in [{"fps": 0}, {"fps": 101}, {"fps": float("nan")},
                       {"sequence": [0]}, {"sequence": []}, {"durations": [100]},
                       {"durations": [0, 100, 100]}, {"alpha_cutoff": 0}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                gif.create_gif(self.frames, self.root / "bad.gif", **kwargs)
        a, b = Image.new("RGB", (10, 10), "red"), Image.new("RGB", (10, 10), "blue")
        a.save(self.frames / "animated.png", save_all=True, append_images=[b], duration=100, loop=0)
        with self.assertRaisesRegex(ValueError, "Animated"):
            gif.create_gif(self.frames, self.root / "bad.gif")
        self.assertFalse(list(self.root.glob("bad.*")))

    def test_existing_review_files_and_publication_failure_do_not_overwrite(self):
        self.solid_frames()
        report = self.root / "out.animation.json"
        report.write_text("user content")
        with self.assertRaises(ValueError):
            gif.create_gif(self.frames, self.root / "out.gif")
        self.assertEqual(report.read_text(), "user content")
        link = gif.os.link
        calls = []
        def failing_link(src, dst):
            calls.append(dst)
            if len(calls) == 3:
                raise OSError("Publication interrupted")
            link(src, dst)
        with patch.object(gif.os, "link", side_effect=failing_link):
            with self.assertRaises(OSError):
                gif.create_gif(self.frames, self.root / "other.gif")
        self.assertFalse(list(self.root.glob("other.*")))
        self.assertEqual(report.read_text(), "user content")

    def test_disposal_clears_vacated_pixels_including_blank_frames(self):
        from PIL import ImageDraw
        for i, box in enumerate([(2, 10, 12, 25), (25, 10, 35, 25), None]):
            frame = Image.new("RGBA", (40, 40))
            if box:
                ImageDraw.Draw(frame).rectangle(box, fill="brown")
            frame.save(self.frames / f"{i}.png")
        gif.create_gif(self.frames, self.root / "out.gif", fps=10)
        frames = gif.decode_gif(self.root / "out.gif")["frames"]
        self.assertEqual(frames[1].getpixel((7, 15))[3], 0)
        self.assertEqual(frames[1].getpixel((30, 15))[3], 255)
        self.assertIsNone(frames[2].getchannel("A").getbbox())

    def test_standalone_grid_fallback_accepts_safe_cuts_and_rejects_crossings(self):
        from PIL import ImageDraw
        original_is_file = Path.is_file
        def without_slicer(path):
            if path.name == "make_stickers.py":
                return False
            return original_is_file(path)
        sheet = Image.new("RGBA", (100, 50))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((10, 15, 30, 35), fill="red")
        draw.rectangle((66, 15, 90, 35), fill="blue")
        sheet.save(self.root / "sheet.png")
        with patch.object(Path, "is_file", without_slicer):
            gif.create_gif(self.root / "sheet.png", self.root / "out.gif", layout="1x2")
            draw.rectangle((31, 15, 52, 35), fill="red")
            sheet.save(self.root / "sheet.png")
            with self.assertRaisesRegex(ValueError, "crosses artwork"):
                gif.create_gif(self.root / "sheet.png", self.root / "bad.gif", layout="1x2")
        self.assertFalse(list(self.root.glob("bad.*")))


if __name__ == "__main__":
    unittest.main()
