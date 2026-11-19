#!/usr/bin/env python3
"""Export a static red packet cover and an offline composition review."""

import argparse
import json
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageCms, ImageColor, ImageOps


SIZE = (957, 1278)
MAX_BYTES = 500_000
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
REVIEW = Path(__file__).resolve().parents[1] / "assets" / "review.html"
# Half-open pixel rectangles from the official 20260114 Sketch design template.
CHARMS = {
    "cover": ("封面挂件", (1053, 1746), (96, 342, 957, 1650)),
    "bubble": ("气泡挂件", (480, 384), (0, 96, 480, 312)),
}
CHARM_MAX_BYTES = 300_000
# Position of the cover image in the cover charm canvas in the same template.
COVER_ORIGIN = (48, 114)


def check_charm_alpha(alpha, blocked):
    if alpha.getbbox() is None or alpha.getextrema()[0] != 0:
        raise ValueError("Use a non-empty PNG with transparent background pixels")
    overlap = alpha.crop(blocked).getbbox()
    if overlap:
        left, top = blocked[:2]
        x0, y0, x1, y1 = overlap
        raise ValueError(f"Nontransparent pixels in the template's blocked area at "
                         f"({x0 + left}, {y0 + top})–({x1 + left}, {y1 + top})")


def validate_upload(data, *, charm=None):
    if charm is None:
        size, limit, image_format, mode = SIZE, MAX_BYTES, "JPEG", "RGB"
    else:
        _, size, blocked = CHARMS[charm]
        limit, image_format, mode = CHARM_MAX_BYTES, "PNG", "RGBA"
    if len(data) > limit:
        raise ValueError(f"{image_format} is {len(data):,} bytes. The limit is {limit:,} bytes")
    with Image.open(BytesIO(data), formats=[image_format]) as image:
        if getattr(image, "is_animated", False) or (image.size, image.mode) != (size, mode):
            raise ValueError(f"Expected a static {size[0]} × {size[1]} {mode} {image_format}")
        profile = image.info.get("icc_profile")
        if not profile or "srgb" not in ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(BytesIO(profile))).casefold():
            raise ValueError(f"Expected an embedded sRGB profile in the {image_format}")
        image.load()
        if charm is not None:
            check_charm_alpha(image.getchannel("A"), blocked)
        return image


def crop_box(size, focus):
    width, height = size
    scale = min(width / SIZE[0], height / SIZE[1])
    crop_width, crop_height = SIZE[0] * scale, SIZE[1] * scale
    left = max(0, min(width - crop_width, focus[0] * width - crop_width / 2))
    top = max(0, min(height - crop_height, focus[1] * height - crop_height / 2))
    return left, top, min(width, left + crop_width), min(height, top + crop_height)


def load_art(source, *, png_only=False):
    with Image.open(source) as original:
        if getattr(original, "is_animated", False):
            raise ValueError("Use a static source image")
        if png_only and original.format != "PNG":
            raise ValueError("Charm source must be PNG")
        image = ImageOps.exif_transpose(original)

    profile = image.info.get("icc_profile")
    if profile:
        cms_input = image.convert("L") if image.mode == "LA" else image
        if cms_input.mode not in ("RGB", "CMYK", "L", "LAB"):
            cms_input = cms_input.convert("RGB")
        color = ImageCms.profileToProfile(cms_input, BytesIO(profile), SRGB, outputMode="RGB")
    else:
        color = image.convert("RGB")
    if "A" in image.getbands() or "transparency" in image.info:
        color.putalpha(image.convert("RGBA").getchannel("A"))
    return color


def prepare_art(source, focus, background):
    color = load_art(source)
    box = crop_box(color.size, focus)
    cover = color.resize(SIZE, Image.Resampling.LANCZOS, box=box)
    if cover.mode == "RGBA" and cover.getchannel("A").getextrema()[0] < 255:
        if background is None:
            raise ValueError("The cover contains transparent pixels. Set --background to the intended color")
        matte = Image.new("RGBA", SIZE, ImageColor.getcolor(background, "RGB"))
        cover = Image.alpha_composite(matte, cover)
    return cover.convert("RGB"), box, color.size


def encode_cover(image):
    profile = SRGB.tobytes()
    for quality in range(94, 49, -4):
        with BytesIO() as buffer:
            image.save(buffer, format="JPEG", quality=quality, optimize=quality < 90,
                       subsampling=0 if quality >= 90 else 2, icc_profile=profile)
            data = buffer.getvalue()
        if len(data) <= MAX_BYTES:
            validate_upload(data)
            return data, quality
    raise ValueError("Could not fit the 500,000-byte limit at the target size")


def placement_bounds(alpha, bounds):
    # Ignore nearly invisible speckles when framing, then keep a margin for soft edges.
    visible = alpha.point(lambda value: 255 if value >= 12 else 0).getbbox()
    if visible is None or visible == bounds:
        return bounds
    left, top, right, bottom = visible
    margin = max(2, round(max(right - left, bottom - top) * 0.02))
    return (max(left - margin, bounds[0]), max(top - margin, bounds[1]),
            min(right + margin, bounds[2]), min(bottom + margin, bounds[3]))


def encode_charm(source, kind, box):
    _, size, blocked = CHARMS[kind]
    image = load_art(source, png_only=True).convert("RGBA")
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None or alpha.getextrema()[0] != 0:
        raise ValueError("Use a non-empty PNG with transparent background pixels")

    if box is not None:
        x, y, width, height = box
        if min(x, y) < 0 or min(width, height) < 1 or x + width > size[0] or y + height > size[1]:
            raise ValueError(f"Placement box must fit within the {size[0]} × {size[1]} canvas")
        art = ImageOps.contain(image.crop(placement_bounds(alpha, bounds)), (width, height), Image.Resampling.LANCZOS)
        image = Image.new("RGBA", size)
        image.alpha_composite(art, (x + (width - art.width) // 2, y + (height - art.height) // 2))
    elif image.size != size:
        raise ValueError(f"Provide a positioned {size[0]} × {size[1]} PNG or specify a placement box")

    check_charm_alpha(image.getchannel("A"), blocked)
    # Clear hidden RGB values to reduce PNG size without changing visible artwork.
    image = Image.alpha_composite(Image.new("RGBA", size), image)
    profile = SRGB.tobytes()
    with BytesIO() as buffer:
        image.save(buffer, format="PNG", optimize=True, icc_profile=profile)
        data = buffer.getvalue()
    final = validate_upload(data, charm=kind)
    if final.tobytes() != image.tobytes():
        raise ValueError("Encoded PNG pixels differ from the prepared charm")
    return data, image.getchannel("A").getbbox()


def charm_figure(name, label, size, blocked, byte_count):
    width, height = size
    x0, y0, x1, y1 = blocked
    inset = " ".join(f"{100 * distance / extent:.6g}%" for distance, extent in (
        (y0, height), (width - x1, width), (height - y1, height), (x0, width)
    ))
    return (
        f'<figure><figcaption>{label} · {width} × {height} px · {byte_count:,} 字节</figcaption>'
        f'<div class="art charm" style="aspect-ratio:{width}/{height}">'
        f'<img src="{name}" alt="{label}透明 PNG" width="{width}" height="{height}">'
        f'<div class="zone" style="inset:{inset}">模板避让区</div></div></figure>'
    )


def composition_review(image, charms, cover_charm_bottom, bubble_focus_y):
    figures = []
    if "cover" in charms:
        width, height = CHARMS["cover"][1]
        left, top = COVER_ORIGIN
        stage_height = max(top + SIZE[1], cover_charm_bottom)
        for title, scale in (("封面与挂件", ""), ("封面缩小效果", " small")):
            figures.append(
                f'<figure><figcaption>{title}</figcaption>'
                f'<div class="cover-stack{scale}" style="aspect-ratio:{width}/{stage_height}">'
                f'<img class="sheet" src="{image}" alt="红包封面" '
                f'style="left:{100 * left / width:.7g}%;top:{100 * top / stage_height:.7g}%;width:{100 * SIZE[0] / width:.7g}%">'
                f'<img class="layer" src="{charms["cover"]}" alt="封面挂件" style="height:{100 * height / stage_height:.7g}%">'
                '</div></figure>'
            )
    if "bubble" in charms:
        figures.append(
            '<figure><figcaption>气泡裁切与挂件</figcaption><div class="bubble-stack">'
            f'<img class="bubble-crop" src="{image}" alt="缩小的气泡裁切画面" '
            f'style="object-position:center {100 * bubble_focus_y:.7g}%">'
            f'<img class="layer" src="{charms["bubble"]}" alt="气泡挂件"></div></figure>'
        )
    if not figures:
        return ""
    return ('<h2>挂件合成示意</h2>\n<section aria-label="挂件合成示意">\n'
            + "\n".join(figures) + "\n</section>\n<h2>素材检查</h2>")


def build_cover(source, output, focus, background, preview_only, *, charms=(), bubble_focus_y=0.5):
    if not all(0 <= value <= 1 for value in (*focus, bubble_focus_y)):
        raise ValueError("Focus coordinates must be between 0 and 1")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Choose a new output directory instead of {output}")

    image, crop, source_size = prepare_art(source, focus, background)
    data, quality = encode_cover(image)
    image_name = "preview.jpg" if preview_only else "cover.jpg"
    charm_files, charm_info, figures = {}, {}, []
    cover_charm_bottom = 0
    for kind, charm_source, box in charms:
        label, size, blocked = CHARMS[kind]
        if charm_source is None:
            if box is not None:
                raise ValueError(f"--{kind}-charm-box requires --{kind}-charm")
            continue
        try:
            encoded, bounds = encode_charm(charm_source, kind, box)
        except (OSError, ValueError, ImageCms.PyCMSError) as error:
            raise ValueError(f"{label} — {error}") from error
        name = f"{kind}-charm{'-preview' if preview_only else ''}.png"
        if kind == "cover":
            cover_charm_bottom = bounds[3]
        charm_files[name] = encoded
        charm_info[kind] = {"path": str(output / name), "size": size, "bytes": len(encoded)}
        figures.append(charm_figure(name, label, size, blocked, len(encoded)))
    review = REVIEW.read_text(encoding="utf-8")
    review = review.replace("{{IMAGE}}", image_name)
    review = review.replace("{{SIZE}}", f"{SIZE[0]} × {SIZE[1]} px · {len(data):,} 字节")
    review = review.replace("{{CHARMS}}", "\n    ".join(figures))
    names = {kind: Path(info["path"]).name for kind, info in charm_info.items()}
    review = review.replace("{{COMPOSITION}}", composition_review(image_name, names, cover_charm_bottom, bubble_focus_y))

    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".cover-", dir=output.parent) as temporary:
        stage = Path(temporary) / "cover"
        stage.mkdir()
        (stage / "review.html").write_text(review, encoding="utf-8")
        (stage / image_name).write_bytes(data)
        for name, encoded in charm_files.items():
            (stage / name).write_bytes(encoded)
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Choose a new output directory instead of {output}")
        stage.rename(output)

    result = {"cover": None if preview_only else str(output / image_name),
              "preview_image": str(output / image_name) if preview_only else None,
              "review": str(output / "review.html"),
              "size": SIZE, "bytes": len(data), "quality": quality,
              "source_size": source_size, "crop": [round(value, 2) for value in crop]}
    if charm_info:
        result["charms"] = charm_info
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Static source image")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--focus", metavar=("X", "Y"), nargs=2, type=float, default=(0.5, 0.5))
    parser.add_argument("--background", help="Matte color for artwork with transparency")
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--bubble-focus-y", type=float, default=0.5, help="Vertical crop in the bubble mockup, from 0 to 1")
    for kind in CHARMS:
        parser.add_argument(f"--{kind}-charm", type=Path, help=f"Optional static {kind} charm PNG")
        parser.add_argument(f"--{kind}-charm-box", type=int, nargs=4, metavar=("X", "Y", "W", "H"),
                            help=f"Placement box for unpositioned {kind} charm artwork")
    args = parser.parse_args()
    try:
        charms = [(kind, getattr(args, f"{kind}_charm"), getattr(args, f"{kind}_charm_box")) for kind in CHARMS]
        result = build_cover(args.source, args.output.absolute(), args.focus, args.background,
                             args.preview_only, charms=charms, bubble_focus_y=args.bubble_focus_y)
    except (OSError, ValueError, ImageCms.PyCMSError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
