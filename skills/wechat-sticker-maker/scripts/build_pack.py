"""Build a checked static PNG sticker pack from one JSON specification."""

import argparse
import importlib.util
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from make_stickers import check_transparency, fit_center, slice_grid, visible_bbox, write_stickers
from render_captions import render_caption_with_details


ASSET_SIZES = {"cover": (240, 240), "chat_icon": (50, 50), "banner": (750, 400),
               "reward_guide": (750, 560), "reward_thanks": (750, 750)}


def validate_album(album):
    for field, limit in [("name", 8), ("description", 80), ("copyright", 10), ("tagline", 11)]:
        value = album.get(field, "")
        if (not isinstance(value, str) or "\n" in value or len(value) > limit
                or (field in {"name", "description"} and not value.strip())):
            raise ValueError(f"专辑{field}为空或超过本地长度约定{limit}")


def asset_processor():
    path = Path(__file__).resolve().parents[2] / "wechat-sticker-assets-designer/scripts/crop_and_resize.py"
    if not path.is_file():
        raise ValueError("完整打包需要同时安装wechat-sticker-assets-designer技能")
    spec = importlib.util.spec_from_file_location("sticker_asset_processor", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.process_image


def source_path(root, value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def crop_source(image, box):
    if box is None:
        return image
    if (len(box) != 4 or any(type(v) is not int for v in box)
            or not 0 <= box[0] < box[2] <= image.width
            or not 0 <= box[1] < box[3] <= image.height):
        raise ValueError("裁剪区域必须是图内的整数坐标[left,top,right,bottom]")
    return image.crop(tuple(box))


def preview(images, path, transparent=False):
    canvas = Image.new("RGBA", (1080, 1080))
    # The workflow currently authors 4x4 sheets; slicer itself supports other explicit layouts.
    for i, image in enumerate(images):
        row, col = divmod(i, 4)
        tile = Image.new("RGBA", (270, 270), (0, 0, 0, 0) if transparent
                         else ("#e6ece9" if (row + col) % 2 == 0 else "#283b3a"))
        tile.alpha_composite(image, (15, 15))
        canvas.alpha_composite(tile, (col * 270, row * 270))
    canvas.save(path, optimize=True)


def comparison_preview(baseline, styled, path):
    canvas = Image.new("RGB", (1080, 32 + 8 * 284), "#e6ece9")
    draw = ImageDraw.Draw(canvas)
    draw.text((15, 10), "A: uniform font + bottom caption    B: configured typography", fill="#283b3a")
    for i, pair in enumerate(zip(baseline, styled)):
        row, pair_col = divmod(i, 2)
        for j, image in enumerate(pair):
            x, y = (pair_col * 2 + j) * 270, 32 + row * 284
            draw.text((x + 15, y + 4), f"{i + 1:02d} {'AB'[j]}", fill="#283b3a")
            canvas.paste(image, (x + 15, y + 28), image)
    canvas.save(path, optimize=True)


def resolve_fonts(spec, root):
    fonts = {"regular": spec["font"]} if spec.get("font") else {}
    fonts.update(spec.get("fonts", {}))
    resolved = {}
    for role, value in fonts.items():
        value = {"path": value} if isinstance(value, str) else value
        resolved[role] = {"path": str(source_path(root, value["path"])),
                          "index": value.get("index", 0)}
    return resolved


def render_item(cell, item, fonts, defaults):
    style = dict(defaults, **item.get("typography", {}))
    role = style.get("font_role", "regular")
    if role not in fonts:
        raise ValueError(f"未配置字体角色：{role}")
    font = fonts[role]
    image, details = render_caption_with_details(cell, item["caption"], font["path"],
                                                style=style, font_index=font["index"])
    return image, dict(details, id=item["id"], caption=item["caption"])


def validate_asset_selection(assets, include_rewards=True):
    if type(include_rewards) is not bool:
        raise ValueError("include_rewards必须为布尔值；仅用户明确不要赞赏配图时设为false")
    if ("reward_guide" in assets) != ("reward_thanks" in assets):
        raise ValueError("赞赏引导图与致谢图须成对提供")
    required = set(ASSET_SIZES) if include_rewards else {"cover", "chat_icon", "banner"}
    missing = required - set(assets)
    if missing:
        raise ValueError(f"完整包缺少配套素材：{', '.join(sorted(missing))}；先看预览请用--preview-only")


def validate_pack(directory, require_assets=True):
    directory = Path(directory)
    fields = {}
    for line in (directory / "info.txt").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"【([^】]+)】(.*)", line)
        if match:
            fields[match[1]] = match[2]
    validate_album({key: fields.get(label, "") for key, label in [
        ("name", "表情名称"), ("description", "表情介绍"),
        ("copyright", "版权"), ("tagline", "一句话简介")]})
    lines = (directory / "meta.txt").read_text(encoding="utf-8").splitlines()
    names = [f"{i:02d}.png" for i in range(1, len(lines) + 1)]
    for expected, line in zip(names, lines):
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or parts[0] != expected or "[请输入" in parts[1]:
            raise ValueError("文案缺失、编号重复或顺序不匹配")
    if not names:
        raise ValueError("素材包为空")
    records = []
    for folder, size, limit in [("main", (240, 240), 100 * 1024),
                                 ("thumbnail", (120, 120), 50 * 1024),
                                 ("icon", (50, 50), 30 * 1024)]:
        actual = {p.name for p in (directory / folder).iterdir() if p.name != ".DS_Store"}
        if actual != set(names):
            raise ValueError(f"{folder}文件与文案编号不一致")
        for filename in names:
            path = directory / folder / filename
            with Image.open(path) as image:
                if image.format != "PNG" or image.size != size:
                    raise ValueError(f"尺寸或格式错误：{path}")
                rgba = image.convert("RGBA")
                check_transparency(rgba)
                box = visible_bbox(rgba)
                if box[0] < 2 or box[1] < 2 or box[2] > size[0] - 2 or box[3] > size[1] - 2:
                    raise ValueError(f"内容贴边，请检查：{path}")
            if path.stat().st_size > limit:
                raise ValueError(f"超过本地体积目标：{path}")
            records.append({"file": str(path.relative_to(directory)), "size": list(size),
                            "bytes": path.stat().st_size})
    if require_assets:
        assets = directory / "assets"
        present = {p.stem for p in assets.glob("*.png")}
        spec = json.loads((directory / "pack.json").read_text(encoding="utf-8"))
        validate_asset_selection(present, spec.get("include_rewards", True))
        for name in present:
            if name not in ASSET_SIZES:
                raise ValueError(f"未知配套素材：{name}")
            path = assets / f"{name}.png"
            with Image.open(path) as image:
                if image.format != "PNG" or image.size != ASSET_SIZES[name]:
                    raise ValueError(f"配套素材尺寸错误：{path}")
                rgba = image.convert("RGBA")
                if name in {"cover", "chat_icon"}:
                    check_transparency(rgba)
                elif rgba.getchannel("A").getextrema() != (255, 255):
                    raise ValueError(f"场景配图背景必须不透明：{path}")
            limit = {"cover": 80 * 1024, "chat_icon": 30 * 1024}.get(name, 500 * 1024)
            if path.stat().st_size > limit:
                raise ValueError(f"配套图超过本地体积目标：{path}")
            records.append({"file": f"assets/{name}.png", "size": list(ASSET_SIZES[name]),
                            "bytes": path.stat().st_size})
    return {"count": len(names), "files": records, "local_checks_passed": True,
            "platform_review_verified": False}


def build_pack(spec_path, output, preview_only=False, compare_typography=False):
    spec_path, output = Path(spec_path).resolve(), Path(output).resolve()
    archive = output.parent / f"{output.name}.zip"
    if output.exists() or (not preview_only and archive.exists()):
        raise ValueError("输出目录或ZIP已存在，请指定新的版本路径")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    album = spec["album"]
    validate_album(album)
    items = spec["items"]
    if spec["layout"] != "4x4":
        raise ValueError("整包预览当前采用4x4，请将其他布局交给独立切片脚本处理")
    if len(items) != 16 or [item["id"] for item in items] != list(range(1, 17)):
        raise ValueError("当前整包流程要求16个按1至16排列的条目")
    if any(not isinstance(item["caption"], str) or not item["caption"].strip()
           or "\n" in item["caption"] for item in items):
        raise ValueError("每个条目必须提供非空单行文案")
    mode = spec.get("caption_mode", "baked")
    if mode not in {"baked", "render", "none"}:
        raise ValueError("caption_mode需为baked、render或none")
    if compare_typography and mode != "render":
        raise ValueError("排版对照需要caption_mode=render的无字源图")
    root = spec_path.parent
    grid = source_path(root, spec["grid"])
    with Image.open(grid) as image:
        cells, cuts = slice_grid(image, spec["layout"], spec.get("boundaries"))
    if len(cells) != len(items):
        raise ValueError("网格布局与条目数量不一致")
    fonts = resolve_fonts(spec, root) if mode == "render" else {}
    defaults = spec.get("typography", {})
    images, typography, baseline = [], [], []
    for cell, item in zip(cells, items):
        if mode == "render":
            image, details = render_item(cell, item, fonts, defaults)
            typography.append(details)
            if compare_typography:
                base_style = dict(defaults, layout="bottom", angle=0)
                baseline.append(render_item(cell, {"id": item["id"], "caption": item["caption"]},
                                            fonts, base_style)[0])
        else:
            image = fit_center(cell, 240, 12)
        images.append(image)
    assets = spec.get("assets", {})
    if not preview_only:
        validate_asset_selection(assets, spec.get("include_rewards", True))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".build-stickers-", dir=output.parent) as temporary:
        stage = Path(temporary) / "pack"
        stage.mkdir()
        write_stickers(cells, stage)
        for i, image in enumerate(images, 1):
            for folder, size in [("main", 240), ("thumbnail", 120), ("icon", 50)]:
                image.resize((size, size), Image.Resampling.LANCZOS).save(
                    stage / folder / f"{i:02d}.png", optimize=True)
        (stage / "source").mkdir()
        grid_name = f"grid{grid.suffix.lower()}"
        shutil.copy2(grid, stage / "source" / grid_name)
        exported_spec = dict(spec, grid=f"source/{grid_name}")
        if mode == "render":
            if spec.get("font"):
                exported_spec["font"] = str(source_path(root, spec["font"]))
            if spec.get("fonts"):
                exported_spec["fonts"] = fonts
        if preview_only:
            exported_spec["assets"] = {
                name: dict(asset, source=str(source_path(root, asset["source"])))
                for name, asset in assets.items()}
        if spec.get("character", {}).get("reference"):
            reference = source_path(root, spec["character"]["reference"])
            reference_name = f"character{reference.suffix.lower()}"
            shutil.copy2(reference, stage / "source" / reference_name)
            exported_spec["character"] = dict(spec["character"], reference=f"source/{reference_name}")
        preview(images, stage / "preview.png")
        preview(images, stage / "grid.png", transparent=True)
        if compare_typography:
            comparison_preview(baseline, images, stage / "comparison.png")
        (stage / "meta.txt").write_text("".join(
            f"{item['id']:02d}.png\t{item['caption']}\n" for item in items), encoding="utf-8")
        (stage / "info.txt").write_text("\n".join(
            f"【{label}】{album.get(key, '')}" for key, label in [
                ("name", "表情名称"), ("description", "表情介绍"),
                ("copyright", "版权"), ("tagline", "一句话简介")]) + "\n", encoding="utf-8")
        processed = []
        if not preview_only:
            processor = asset_processor()
            (stage / "assets").mkdir()
            exported_spec["assets"] = {}
            for name, asset in assets.items():
                if name not in ASSET_SIZES:
                    raise ValueError(f"未知配套图类型：{name}")
                source = source_path(root, asset["source"])
                original = stage / "source" / f"{name}-original{source.suffix}"
                shutil.copy2(source, original)
                exported_spec["assets"][name] = dict(asset, source=str(original.relative_to(stage)))
                with Image.open(source) as image:
                    image = crop_source(image.convert("RGBA"), asset.get("crop"))
                    if name in {"cover", "chat_icon"}:
                        check_transparency(image)
                        fit_center(image, ASSET_SIZES[name][0], 12 if name == "cover" else 3).save(
                            stage / "assets" / f"{name}.png", optimize=True)
                        continue
                    if image.getchannel("A").getextrema() != (255, 255):
                        raise ValueError(f"{name}需要不透明的场景图")
                    cropped = Path(temporary) / f"{name}-crop.png"
                    image.convert("RGB").save(cropped)
                processed.append(dict(processor(cropped, *ASSET_SIZES[name],
                    anchor="top" if name == "reward_guide" else "center",
                    output_path=stage / "assets" / f"{name}.png", max_bytes=500 * 1024), name=name))
        (stage / "pack.json").write_text(json.dumps(exported_spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report = validate_pack(stage, require_assets=not preview_only)
        report.update(boundaries=cuts, caption_mode=mode, preview_only=preview_only,
                      typography=typography, typography_comparison=compare_typography,
                      asset_compression=[{"name": p["name"], "compression": p["compression"]} for p in processed],
                      warnings=["布局检查按alpha>24识别可见内容；仍需视觉检查角色、错字与裁剪。",
                                "尺寸和体积为本地制作约定，不代表微信审核已通过。"])
        (stage / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (stage / "README.txt").write_text(
            "静态透明PNG素材。main为主图，thumbnail为缩略图，assets为配套素材。\n"
            "grid.png是透明总览，preview.png是浅深背景检查图，source保存原图。\n"
            "pack.json保存动作、文案和路径；字体不随包分发，render模式需本机有相应字体。\n"
            "请视觉核对角色一致性和文案；未进行平台投稿或审核。\n", encoding="utf-8")
        if not preview_only:
            with zipfile.ZipFile(Path(temporary) / "pack.zip", "w", zipfile.ZIP_DEFLATED) as zipped:
                for path in sorted(stage.rglob("*")):
                    if path.is_file():
                        zipped.write(path, Path(output.name) / path.relative_to(stage))
            with zipfile.ZipFile(Path(temporary) / "pack.zip") as zipped:
                if zipped.testzip() is not None:
                    raise ValueError("ZIP完整性检查失败")
        stage.rename(output)
        if not preview_only:
            (Path(temporary) / "pack.zip").rename(archive)
    return {"output": str(output), "archive": None if preview_only else str(archive),
            "count": len(items), "preview_only": preview_only}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--compare-typography", action="store_true",
                        help="额外生成统一字体下置版与配置排版的A/B对照图；需render模式")
    args = parser.parse_args()
    try:
        print(json.dumps(build_pack(args.spec, args.output, args.preview_only,
                                   args.compare_typography), ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"打包失败：{exc}\n")


if __name__ == "__main__":
    main()
