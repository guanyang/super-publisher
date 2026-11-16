"""Slice explicitly specified sticker grids without guessing their layout."""

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


ALPHA_THRESHOLD = 24


def parse_layout(layout):
    try:
        rows, cols = map(int, layout.lower().split("x"))
    except (AttributeError, ValueError):
        raise ValueError("必须明确指定行数x列数，例如 --layout 4x4") from None
    if rows <= 0 or cols <= 0:
        raise ValueError("行列数必须为正数")
    return rows, cols


def check_transparency(image):
    low, high = image.getchannel("A").getextrema()
    if low != 0 or high <= ALPHA_THRESHOLD:
        raise ValueError("需要含有效图案和真实透明背景的图片；转成RGBA不等于去底")


def visible_bbox(image):
    return image.getchannel("A").point(
        lambda value: 255 if value > ALPHA_THRESHOLD else 0
    ).getbbox()


def fit_center(image, size, padding=12):
    box = visible_bbox(image)
    if box is None:
        raise ValueError("发现空白切片")
    box = (max(0, box[0] - 2), max(0, box[1] - 2),
           min(image.width, box[2] + 2), min(image.height, box[3] + 2))
    artwork = ImageOps.contain(image.crop(box), (size - 2 * padding,) * 2,
                               Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size))
    canvas.alpha_composite(artwork, ((size - artwork.width) // 2,
                                    (size - artwork.height) // 2))
    return canvas


def axis_boundaries(image, count, axis, explicit=None, allow_opaque=False):
    length = image.width if axis == "x" else image.height
    if explicit is not None:
        if (len(explicit) != count + 1 or explicit[0] != 0 or explicit[-1] != length
                or any(type(v) is not int for v in explicit)
                or any(a >= b for a, b in zip(explicit, explicit[1:]))):
            raise ValueError(f"{axis}轴边界必须从0递增至{length}，共{count + 1}项")
        boundaries = list(explicit)
    elif allow_opaque:
        boundaries = [round(i * length / count) for i in range(count + 1)]
    else:
        alpha = image.getchannel("A")
        boundaries = [0]
        for i in range(1, count):
            expected = i * length / count
            radius = max(2, round(length / count * 0.15))
            start, stop = max(1, round(expected) - radius), min(length, round(expected) + radius)
            runs, run = [], []
            for position in range(start, stop):
                box = ((position, 0, position + 1, image.height) if axis == "x"
                       else (0, position, image.width, position + 1))
                if alpha.crop(box).getextrema()[1] <= ALPHA_THRESHOLD:
                    run.append(position)
                else:
                    if len(run) >= 2:
                        runs.append(run)
                    run = []
            if len(run) >= 2:
                runs.append(run)
            if not runs:
                raise ValueError(f"{axis}轴第{i}处分隔线附近没有可靠透明间隙，请检查图片或提供边界")
            gap = min(runs, key=lambda values: abs((values[0] + values[-1]) / 2 - expected))
            boundaries.append(round((gap[0] + gap[-1]) / 2))
        boundaries.append(length)
    if not allow_opaque:
        alpha = image.getchannel("A")
        for position in boundaries[1:-1]:
            box = ((position, 0, position + 1, image.height) if axis == "x"
                   else (0, position, image.width, position + 1))
            if alpha.crop(box).getextrema()[1] > ALPHA_THRESHOLD:
                raise ValueError(f"{axis}轴边界{position}穿过可见内容，拒绝切割")
    return boundaries


def slice_grid(image, layout, boundaries=None, allow_opaque=False):
    rows, cols = parse_layout(layout)
    image = image.convert("RGBA")
    if not allow_opaque:
        check_transparency(image)
    boundaries = boundaries or {}
    xs = axis_boundaries(image, cols, "x", boundaries.get("x"), allow_opaque)
    ys = axis_boundaries(image, rows, "y", boundaries.get("y"), allow_opaque)
    cells = [image.crop((xs[c], ys[r], xs[c + 1], ys[r + 1]))
             for r in range(rows) for c in range(cols)]
    if any(visible_bbox(cell) is None for cell in cells):
        raise ValueError("发现空白格子，请检查布局与边界")
    return cells, {"x": xs, "y": ys}


def write_stickers(cells, output):
    for folder in ["main", "thumbnail", "icon", "original_slices"]:
        (output / folder).mkdir()
    for number, cell in enumerate(cells, 1):
        filename = f"{number:02d}.png"
        cell.save(output / "original_slices" / filename, optimize=True)
        for folder, size, pad in [("main", 240, 12), ("thumbnail", 120, 6), ("icon", 50, 3)]:
            fit_center(cell, size, pad).save(output / folder / filename, optimize=True)


def process_image(image_path, layout_str, output_dir, boundaries=None, allow_opaque=False):
    output = Path(output_dir)
    if output.exists():
        raise ValueError("输出目录已存在，请使用新的版本目录；不会覆盖文案或混入旧文件")
    with Image.open(image_path) as image:
        cells, cuts = slice_grid(image, layout_str, boundaries, allow_opaque)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".stickers-", dir=output.parent) as temporary:
        stage = Path(temporary) / "pack"
        stage.mkdir()
        write_stickers(cells, stage)
        (stage / "source").mkdir()
        shutil.copy2(image_path, stage / "source" / Path(image_path).name)
        (stage / "meta.txt").write_text("".join(
            f"{i:02d}.png\t[请输入表情含义]\n" for i in range(1, len(cells) + 1)), encoding="utf-8")
        (stage / "info.txt").write_text("【表情名称】\n【表情介绍】\n【一句话简介】\n", encoding="utf-8")
        (stage / "cuts.json").write_text(json.dumps(cuts, indent=2) + "\n", encoding="utf-8")
        stage.rename(output)
    print(f"已切分{len(cells)}张；元数据仍需填写，不代表已通过整包校验：{output.resolve()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--layout", required=True, help="明确行数x列数，例如4x4")
    parser.add_argument("--output", default="sticker_output")
    parser.add_argument("--boundaries", type=Path, help='包含x/y边界数组的JSON')
    parser.add_argument("--allow-opaque", action="store_true", help="仅用户明确要求保留不透明背景时使用")
    args = parser.parse_args()
    try:
        cuts = json.loads(args.boundaries.read_text()) if args.boundaries else None
        process_image(args.image, args.layout, args.output, cuts, args.allow_opaque)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"错误：{exc}\n")


if __name__ == "__main__":
    main()
