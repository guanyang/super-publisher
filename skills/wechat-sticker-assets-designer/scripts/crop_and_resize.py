"""Fit asset dimensions without overwriting the original image."""

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


def encode_png(image, max_bytes=None):
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    if max_bytes is None or len(buffer.getvalue()) <= max_bytes:
        return buffer.getvalue(), "lossless"
    if image.mode == "RGBA" and image.getchannel("A").getextrema()[0] < 255:
        raise ValueError("透明PNG超过体积目标，保留原alpha，不自动量化或缩小尺寸")
    rgb = image.convert("RGB")
    for colors in [256, 128, 64]:
        palette = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        reduced = rgb.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
        buffer = BytesIO()
        reduced.save(buffer, format="PNG", optimize=True)
        if len(buffer.getvalue()) <= max_bytes:
            return buffer.getvalue(), f"palette-{colors}-dithered"
    raise ValueError("无法在保留尺寸的前提下达到体积目标；请调整素材或显式选择其他格式")


def process_image(img_path, target_w, target_h, anchor="center", output_path=None, max_bytes=None):
    source = Path(img_path)
    if target_w <= 0 or target_h <= 0 or (max_bytes is not None and max_bytes <= 0):
        raise ValueError("尺寸和体积目标必须为正数")
    output = Path(output_path) if output_path else source.with_name(
        f"{source.stem}-{target_w}x{target_h}.png")
    if output.resolve() == source.resolve() or output.exists():
        raise ValueError("拒绝覆盖原图或已存在的输出，请使用新路径")
    centering = {"center": (0.5, 0.5), "top": (0.5, 0), "bottom": (0.5, 1),
                 "left": (0, 0.5), "right": (1, 0.5)}[anchor]
    with Image.open(source) as original:
        image = original.convert("RGBA")
        if image.getchannel("A").getextrema() == (255, 255):
            image = image.convert("RGB")
        image = ImageOps.fit(image, (target_w, target_h), Image.Resampling.LANCZOS,
                             centering=centering)
    encoded, compression = encode_png(image, max_bytes)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    return {"path": str(output), "size": [target_w, target_h],
            "bytes": len(encoded), "compression": compression}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--anchor", default="center", choices=["center", "top", "bottom", "left", "right"])
    parser.add_argument("--output")
    parser.add_argument("--max-bytes", type=int)
    args = parser.parse_args()
    try:
        print(process_image(args.image, args.width, args.height, args.anchor, args.output, args.max_bytes))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"错误：{exc}\n")


if __name__ == "__main__":
    main()
