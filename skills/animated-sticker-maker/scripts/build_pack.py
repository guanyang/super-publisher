#!/usr/bin/env python3
"""Export an ordered sticker manifest to verified GIFs and an offline review."""

import argparse
import importlib.util
import json
import math
import re
import shutil
import unicodedata
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageDraw, ImageFont

from build_review import write_review


def load_encoder():
    path = Path(__file__).resolve().parents[2] / "gif-maker/scripts/make_gif.py"
    if not path.is_file():
        raise ValueError("GIF runtime missing. Run from the Super Publisher checkout or install both skill directories together.")
    spec = importlib.util.spec_from_file_location("sticker_gif_encoder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def caption_layer(caption, font, size):
    missing = bytes(font.getmask("\uffff"))
    if not caption.strip() or "\n" in caption or any(bytes(font.getmask(char)) == missing for char in caption):
        raise ValueError("Caption must be a single line supported by the configured font")
    layer = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(layer)
    stroke = max(1, round(size * 0.008))
    left, top, right, bottom = draw.textbbox((0, 0), caption, font=font, stroke_width=stroke)
    width = right - left
    y = round(size * 0.81)
    if width > size * 0.9 or y + bottom - top > size * 0.97:
        raise ValueError("Caption is too large for the canvas")
    draw.text(((size - width) // 2 - left, y - top), caption, font=font,
              fill="#fff2d6", stroke_width=stroke, stroke_fill="#542e20")
    return layer


def export_sticker(item, recipe, root, destination, scratch, encoder):
    source = root / item["source"]
    layout = item.get("layout")
    size = recipe.get("size", 320)
    caption = item.get("caption")
    overlay = None
    if caption is not None:
        if not isinstance(caption, str) or not recipe.get("font"):
            raise ValueError("Set a text caption and a shared font path, or omit caption for composed frames")
        font = ImageFont.truetype(str(root / recipe["font"]), round(size * 0.125),
                                  index=recipe.get("font_index", 0))
        overlay = scratch / "caption.png"
        caption_layer(caption, font, size).save(overlay)

    frames, _ = encoder.load_frames(source, layout)
    needs_resize = frames[0].size != (size, size)
    if needs_resize and overlay is not None:
        art_size = round(size * 0.84)
        frames, _ = encoder.prepare_frames(frames, art_size)
        directory = scratch / "frames"
        directory.mkdir()
        for index, frame in enumerate(frames, 1):
            canvas = Image.new("RGBA", (size, size))
            canvas.alpha_composite(frame, ((size - art_size) // 2, 0))
            canvas.save(directory / f"{index:04}.png")
        source, layout, needs_resize = directory, None, False

    encoder.create_gif(
        source, scratch / "sticker.gif", layout=layout,
        size=size if needs_resize else None,
        sequence=item.get("sequence"), durations=item.get("durations_ms"),
        overlay=overlay, max_size_kb=recipe.get("max_kib", 0),
    )
    shutil.copyfile(scratch / "sticker.gif", destination)


def verify_gif(path, recipe, encoder):
    decoded = encoder.decode_gif(path)
    size = recipe.get("size", 320)
    frames = decoded["frames"]
    if decoded["size"] != (size, size) or decoded["loop"] != 0 or len(frames) < 2:
        raise ValueError("Expected a multiframe GIF with the requested dimensions and continuous loop")
    if recipe.get("transparent", True) and any(frame.getchannel("A").getextrema()[0] != 0 for frame in frames):
        raise ValueError("Expected transparent pixels on every frame")
    limit = recipe.get("max_kib", 0)
    if limit and path.stat().st_size > limit * 1024:
        raise ValueError("GIF exceeds max_kib")


def build_pack(spec_path, output, include_zip=False):
    spec_path = spec_path.resolve()
    recipe = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(recipe, dict) or not isinstance(recipe.get("stickers"), list) or not recipe["stickers"]:
        raise ValueError("Manifest requires a non-empty stickers array")
    size, limit = recipe.get("size", 320), recipe.get("max_kib", 0)
    if type(size) is not int or size < 16 or type(limit) not in (int, float) or not math.isfinite(limit) or limit < 0:
        raise ValueError("Use an integer size of at least 16 and a nonnegative max_kib")
    if type(recipe.get("transparent", True)) is not bool:
        raise ValueError("transparent must be a boolean")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Choose a new output directory instead of {output}")
    encoder = load_encoder()
    output.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix=".animated-stickers-", dir=output.parent) as temporary:
        stage = Path(temporary)
        pack = stage / "pack"
        (pack / "gifs").mkdir(parents=True)
        gifs, names = [], set()
        for index, item in enumerate(recipe["stickers"], 1):
            name = item.get("name") if isinstance(item, dict) else None
            if not isinstance(name, str) or not name.strip() or name != name.strip() or re.search(r'[<>:"/\\|?*\x00-\x1f]|\.$', name):
                raise ValueError(f"Sticker {index} needs a usable filename stem as its name")
            key = unicodedata.normalize("NFC", name).casefold()
            if key in names:
                raise ValueError(f"Duplicate sticker name {name}")
            names.add(key)
            destination = pack / "gifs" / f"{name}.gif"
            try:
                if "gif" in item and item.keys() == {"name", "gif"}:
                    shutil.copyfile(spec_path.parent / item["gif"], destination)
                elif "source" in item and "gif" not in item:
                    scratch = stage / str(index)
                    scratch.mkdir()
                    export_sticker(item, recipe, spec_path.parent, destination, scratch, encoder)
                else:
                    raise ValueError("Supply a source or a finished GIF. Reused GIF entries only need name and gif")
                verify_gif(destination, recipe, encoder)
            except (OSError, TypeError, ValueError) as error:
                raise ValueError(f"{name} — {error}") from error
            gifs.append(destination)

        write_review(gifs, pack / "review.html")
        if include_zip:
            with ZipFile(pack / "stickers.zip", "x", compression=ZIP_DEFLATED) as archive:
                for gif in gifs:
                    archive.write(gif, arcname=gif.name)

        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Choose a new output directory instead of {output}")
        pack.rename(output)

    return {"gifs": [str(output / "gifs" / gif.name) for gif in gifs],
            "review": str(output / "review.html"),
            "zip": str(output / "stickers.zip") if include_zip else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True, help="Ordered JSON manifest")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--zip", action="store_true", help="Archive the GIFs")
    args = parser.parse_args()
    try:
        result = build_pack(args.spec, args.output.absolute(), include_zip=args.zip)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
