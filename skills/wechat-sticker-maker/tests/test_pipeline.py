import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from build_pack import build_pack, validate_pack
from make_stickers import parse_layout, process_image, slice_grid, visible_bbox
from render_captions import render_caption, render_caption_with_details

asset_spec = importlib.util.spec_from_file_location(
    "asset_resize", SCRIPTS.parents[1] / "wechat-sticker-assets-designer/scripts/crop_and_resize.py")
asset_module = importlib.util.module_from_spec(asset_spec)
asset_spec.loader.exec_module(asset_module)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.grid = Image.new("RGBA", (400, 400))
        draw = ImageDraw.Draw(self.grid)
        for row in range(4):
            for col in range(4):
                draw.rectangle((col * 100 + 20, row * 100 + 22,
                                col * 100 + 76, row * 100 + 78), fill=(140, 75, 30, 255))
        self.grid.save(self.root / "grid.png")
        Image.new("RGB", (900, 600), "teal").save(self.root / "banner.png")
        self.spec = {
            "album": {"name": "测试河狸", "description": "打工日常"},
            "grid": "grid.png", "layout": "4x4", "caption_mode": "baked",
            "items": [{"id": i, "caption": f"动作{i}"} for i in range(1, 17)],
            "assets": {"cover": {"source": "grid.png", "crop": [0, 0, 100, 100]},
                       "chat_icon": {"source": "grid.png", "crop": [0, 0, 100, 100]},
                       "banner": {"source": "banner.png"},
                       "reward_guide": {"source": "banner.png"},
                       "reward_thanks": {"source": "banner.png"}},
        }

    def spec_path(self):
        path = self.root / "pack.json"
        path.write_text(json.dumps(self.spec, ensure_ascii=False), encoding="utf-8")
        return path

    def available_font(self):
        for path in ["DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]:
            try:
                return ImageFont.truetype(path, 24).path
            except OSError:
                pass
        self.skipTest("No test font installed")

    def test_layout_must_be_explicit_and_positive(self):
        for value in [None, "0x4", "4x-1", "square"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_layout(value)

    def test_non_square_cells_keep_aspect_and_center(self):
        image = Image.new("RGBA", (400, 240))
        ImageDraw.Draw(image).rectangle((40, 40, 120, 70), fill="brown")
        image.save(self.root / "wide.png")
        process_image(self.root / "wide.png", "1x1", self.root / "sliced")
        main = Image.open(self.root / "sliced/main/01.png")
        box = visible_bbox(main)
        self.assertGreater((box[2] - box[0]) / (box[3] - box[1]), 2)
        self.assertLessEqual(abs((box[0] + box[2]) / 2 - 120), 1)
        self.assertTrue((self.root / "sliced/thumbnail/01.png").exists())

    def test_opaque_and_empty_input_fail_without_output(self):
        for color in ["white", (0, 0, 0, 0)]:
            Image.new("RGBA", (400, 400), color).save(self.root / "invalid.png")
            with self.assertRaises(ValueError):
                process_image(self.root / "invalid.png", "4x4", self.root / "invalid_out")
            self.assertFalse((self.root / "invalid_out").exists())

    def test_crossing_separator_fails(self):
        image = Image.new("RGBA", (400, 400))
        ImageDraw.Draw(image).rectangle((40, 40, 360, 360), fill="brown")
        with self.assertRaisesRegex(ValueError, "间隙"):
            slice_grid(image, "4x4")

    def test_separator_moves_to_gap_instead_of_cutting_at_equal_width(self):
        image = Image.new("RGBA", (400, 400))
        draw = ImageDraw.Draw(image)
        for row in range(4):
            for left, right in [(40, 108), (120, 176), (220, 276), (320, 376)]:
                draw.rectangle((left, row * 100 + 25, right, row * 100 + 75), fill="brown")
        cells, cuts = slice_grid(image, "4x4")
        self.assertGreater(cuts["x"][1], 108)
        self.assertEqual(visible_bbox(cells[0])[2], 109)

    def test_manual_boundary_cannot_cut_artwork(self):
        with self.assertRaisesRegex(ValueError, "穿过"):
            slice_grid(self.grid, "4x4", {"x": [0, 70, 200, 300, 400]})

    def test_rerun_preserves_metadata_and_file_count(self):
        out = self.root / "sliced"
        process_image(self.root / "grid.png", "4x4", out)
        (out / "info.txt").write_text("用户已修改", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "存在"):
            process_image(self.root / "grid.png", "3x3", out)
        self.assertEqual((out / "info.txt").read_text(), "用户已修改")
        self.assertEqual(len(list((out / "main").glob("*.png"))), 16)

    def test_complete_build_contains_valid_zip_and_original(self):
        out = self.root / "complete"
        result = build_pack(self.spec_path(), out)
        self.assertEqual(validate_pack(out)["count"], 16)
        self.assertEqual((out / "source/grid.png").read_bytes(), (self.root / "grid.png").read_bytes())
        with zipfile.ZipFile(result["archive"]) as zipped:
            self.assertIsNone(zipped.testzip())
            self.assertIn("complete/assets/banner.png", zipped.namelist())
            self.assertIn("complete/assets/reward_guide.png", zipped.namelist())
            self.assertIn("complete/assets/reward_thanks.png", zipped.namelist())
        self.assertFalse(json.loads((out / "manifest.json").read_text())["platform_review_verified"])

    def test_preview_does_not_need_or_create_assets_or_zip(self):
        self.spec.pop("assets")
        out = self.root / "preview"
        result = build_pack(self.spec_path(), out, preview_only=True)
        self.assertIsNone(result["archive"])
        self.assertFalse((out / "assets").exists())
        self.assertFalse((self.root / "preview.zip").exists())
        self.assertEqual(Image.open(out / "grid.png").getchannel("A").getextrema(), (0, 255))

    def test_saved_pack_spec_can_be_rebuilt(self):
        first, second = self.root / "first", self.root / "second"
        build_pack(self.spec_path(), first)
        build_pack(first / "pack.json", second)
        self.assertEqual((first / "meta.txt").read_bytes(), (second / "meta.txt").read_bytes())
        self.assertEqual(validate_pack(second)["count"], 16)

    def test_failure_leaves_no_complete_directory(self):
        self.spec["assets"].pop("reward_thanks")
        with self.assertRaisesRegex(ValueError, "成对"):
            build_pack(self.spec_path(), self.root / "broken")
        self.assertFalse((self.root / "broken").exists())
        self.assertFalse((self.root / "broken.zip").exists())

    def test_complete_build_requires_reward_assets_by_default(self):
        for name in ["reward_guide", "reward_thanks"]:
            self.spec["assets"].pop(name)
        with self.assertRaisesRegex(ValueError, "reward_"):
            build_pack(self.spec_path(), self.root / "broken")
        self.assertFalse((self.root / "broken").exists())
        self.assertFalse((self.root / "broken.zip").exists())

    def test_explicit_reward_opt_out_survives_rebuild_and_validation(self):
        self.spec["include_rewards"] = False
        for name in ["reward_guide", "reward_thanks"]:
            self.spec["assets"].pop(name)
        first, second = self.root / "first", self.root / "second"
        build_pack(self.spec_path(), first)
        build_pack(first / "pack.json", second)
        self.assertEqual(validate_pack(second)["count"], 16)
        self.assertFalse((second / "assets/reward_guide.png").exists())
        self.assertFalse((second / "assets/reward_thanks.png").exists())

    def test_validation_rejects_missing_reward_pair_by_default(self):
        out = self.root / "complete"
        build_pack(self.spec_path(), out)
        for name in ["reward_guide", "reward_thanks"]:
            (out / f"assets/{name}.png").unlink()
        with self.assertRaisesRegex(ValueError, "reward_"):
            validate_pack(out)

    def test_validation_rejects_extra_old_sticker(self):
        out = self.root / "complete"
        build_pack(self.spec_path(), out)
        (out / "main/17.png").write_bytes((out / "main/01.png").read_bytes())
        with self.assertRaisesRegex(ValueError, "编号"):
            validate_pack(out)

    def test_validation_rejects_unfilled_album_information(self):
        out = self.root / "complete"
        build_pack(self.spec_path(), out)
        (out / "info.txt").write_text("【表情名称】\n【表情介绍】\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "专辑"):
            validate_pack(out)

    def test_asset_resize_never_overwrites_source(self):
        source = self.root / "banner.png"
        before = source.read_bytes()
        result = asset_module.process_image(source, 750, 400)
        self.assertEqual(source.read_bytes(), before)
        with Image.open(result["path"]) as image:
            self.assertEqual(image.size, (750, 400))
        with self.assertRaises(ValueError):
            asset_module.process_image(source, 750, 400, output_path=source)

    def test_failed_compression_does_not_publish_asset(self):
        out = self.root / "small.png"
        with self.assertRaises(ValueError):
            asset_module.process_image(self.root / "banner.png", 750, 400,
                                       output_path=out, max_bytes=1)
        self.assertFalse(out.exists())

    def test_caption_rendering_retains_transparency_and_padding(self):
        result = render_caption(self.grid.crop((0, 0, 100, 100)), "HELLO", self.available_font())
        self.assertEqual(result.size, (240, 240))
        self.assertEqual(result.getchannel("A").getextrema(), (0, 255))
        self.assertGreaterEqual(visible_bbox(result)[1], 10)

    def test_caption_layouts_keep_art_and_text_separate_and_centered(self):
        for layout in ["bottom", "top", "arc_top"]:
            with self.subTest(layout=layout):
                result, details = render_caption_with_details(
                    self.grid.crop((0, 0, 100, 100)), "HELLO", self.available_font(),
                    style={"layout": layout, "angle": 4})
                art, text, box = details["art_bbox"], details["text_bbox"], visible_bbox(result)
                self.assertEqual(result.getchannel("A").getextrema(), (0, 255))
                self.assertGreaterEqual(min(box[0], box[1], 240-box[2], 240-box[3]), 12)
                self.assertLessEqual(abs(box[0] + box[2] - 240), 2)
                self.assertLessEqual(abs(box[1] + box[3] - 240), 2)
                self.assertGreater(art[3] - art[1], 3 * (text[3] - text[1]))
                self.assertGreaterEqual(text[1] - art[3] if layout == "bottom"
                                        else art[1] - text[3], 7)

    def test_art_aspect_ratio_does_not_enlarge_caption(self):
        text_sizes = []
        for shape in [(20, 20, 80, 80), (5, 40, 95, 60)]:
            source = Image.new("RGBA", (100, 100))
            ImageDraw.Draw(source).rectangle(shape, fill="brown")
            result, details = render_caption_with_details(source, "HELLO", self.available_font())
            text = result.crop(details["text_bbox"])
            text_sizes.append((text.size, details["font_size"]))
        self.assertEqual(text_sizes[0], text_sizes[1])
        self.assertLessEqual(text_sizes[0][1], 23)

    def test_caption_rejects_overflow_missing_glyph_and_invalid_style(self):
        cell, font = self.grid.crop((0, 0, 100, 100)), self.available_font()
        for caption, style, message in [("HELLO" * 100, {}, "安全区"),
                                         ("\U0010ffff", {}, "缺少"),
                                         ("HELLO", {"layout": "sideways"}, "布局"),
                                         ("HELLO", {"font_szie": 23}, "未知")]:
            with self.subTest(caption=caption[:10]), self.assertRaisesRegex(ValueError, message):
                render_caption(cell, caption, font, style=style)

    def test_item_typography_and_comparison_survive_saved_spec_rebuild(self):
        import shutil
        font = Path(self.available_font())
        shutil.copyfile(font, self.root / font.name)
        self.spec.update(caption_mode="render", fonts={"regular": font.name,
                          "relaxed": {"path": font.name, "index": 0}},
                         typography={"font_size": 22, "fill": "#426b65"})
        for item in self.spec["items"]:
            item["caption"] = "HELLO"
        self.spec["items"][0]["typography"] = {"font_role": "relaxed", "layout": "arc_top", "angle": 3}
        first, second = self.root / "first", self.root / "second"
        build_pack(self.spec_path(), first, preview_only=True, compare_typography=True)
        report = json.loads((first / "manifest.json").read_text())
        self.assertTrue(report["typography_comparison"])
        self.assertEqual(report["typography"][0]["font_role"], "relaxed")
        self.assertEqual(report["typography"][0]["layout"], "arc_top")
        self.assertEqual(report["typography"][1]["fill"], "#426b65")
        self.assertTrue((first / "comparison.png").is_file())
        saved = json.loads((first / "pack.json").read_text())
        self.assertTrue(Path(saved["fonts"]["relaxed"]["path"]).is_absolute())
        build_pack(first / "pack.json", second, preview_only=True)
        self.assertFalse((second / "comparison.png").exists())
        for i in range(1, 17):
            self.assertEqual((first / f"main/{i:02d}.png").read_bytes(),
                             (second / f"main/{i:02d}.png").read_bytes())

    def test_legacy_single_font_config_and_unknown_role_failure(self):
        self.spec.update(caption_mode="render", font=self.available_font())
        for item in self.spec["items"]:
            item["caption"] = "HELLO"
        build_pack(self.spec_path(), self.root / "legacy", preview_only=True)
        self.spec["items"][0]["typography"] = {"font_role": "missing"}
        with self.assertRaisesRegex(ValueError, "未配置字体"):
            build_pack(self.spec_path(), self.root / "broken", preview_only=True)
        self.assertFalse((self.root / "broken").exists())
        self.spec["caption_mode"] = "baked"
        with self.assertRaisesRegex(ValueError, "render"):
            build_pack(self.spec_path(), self.root / "baked_compare", compare_typography=True)

    def test_ttc_index_selects_actual_font_variant(self):
        font = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
        if not font.exists():
            self.skipTest("No TTC test fixture installed")
        cell = self.grid.crop((0, 0, 100, 100))
        light, a = render_caption_with_details(cell, "HELLO", font, font_index=0)
        bold, b = render_caption_with_details(cell, "HELLO", font, font_index=2)
        self.assertNotEqual(a["font"]["variant"], b["font"]["variant"])
        self.assertEqual(b["font"]["index"], 2)
        self.assertNotEqual(light.tobytes(), bold.tobytes())


if __name__ == "__main__":
    unittest.main()
