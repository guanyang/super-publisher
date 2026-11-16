"""Render small captions separately from reusable character artwork."""

from PIL import Image, ImageDraw, ImageFont, ImageOps

from make_stickers import visible_bbox


DEFAULT_STYLE = {"font_role": "regular", "font_size": 23, "layout": "bottom",
                 "angle": 0, "fill": "#563323", "stroke_fill": "#fff3dc",
                 "stroke_width": 1.5}


def text_layer(text, font, style, scale):
    stroke = round(style["stroke_width"] * scale)

    def draw_text(value):
        box = font.getbbox(value, stroke_width=stroke)
        image = Image.new("RGBA", (box[2] - box[0] + 8, box[3] - box[1] + 8))
        ImageDraw.Draw(image).text((4 - box[0], 4 - box[1]), value, font=font,
                                  fill=style["fill"], stroke_width=stroke,
                                  stroke_fill=style["stroke_fill"])
        return image.crop(image.getbbox())

    if style["layout"] == "arc_top":
        # A shallow arch keeps characters together as one readable phrase.
        glyphs = []
        for i, char in enumerate(text):
            t = (i / (len(text) - 1) if len(text) > 1 else 0.5) * 2 - 1
            glyph = draw_text(char).rotate(-3 * t, Image.Resampling.BICUBIC, expand=True)
            glyphs.append((glyph, round(font.size * 0.14 * t * t)))
        gap = max(1, round(font.size * 0.04))
        layer = Image.new("RGBA", (sum(g.width for g, _ in glyphs) + gap * (len(glyphs) - 1),
                                   max(g.height + y for g, y in glyphs)))
        x = 0
        for glyph, y in glyphs:
            layer.alpha_composite(glyph, (x, y))
            x += glyph.width + gap
    else:
        layer = draw_text(text)
    if style["angle"]:
        layer = layer.rotate(style["angle"], Image.Resampling.BICUBIC, expand=True)
    return layer.crop(layer.getbbox())


def render_caption_with_details(image, caption, font_path, size=240, *, style=None, font_index=0):
    if not isinstance(caption, str) or not caption.strip() or "\n" in caption:
        raise ValueError("文案必须是非空单行文本")
    style = style or {}
    if set(style) - set(DEFAULT_STYLE):
        raise ValueError(f"未知排版字段：{sorted(set(style) - set(DEFAULT_STYLE))}")
    style = dict(DEFAULT_STYLE, **style)
    if style["layout"] not in {"bottom", "top", "arc_top"}:
        raise ValueError("文案布局需为bottom、top或arc_top")
    for key in ["font_size", "angle", "stroke_width"]:
        if type(style[key]) not in {int, float}:
            raise ValueError(f"{key}必须为数值")
    if not 12 <= style["font_size"] <= size or not 0 <= style["stroke_width"] <= size / 20:
        raise ValueError("字号需在12至画布尺寸之间，描边需在0至画布尺寸的5%之间")
    if not -15 <= style["angle"] <= 15:
        raise ValueError("倾斜角度需在-15至15度之间；特殊艺术字请单独设计")
    if type(font_index) is not int or font_index < 0:
        raise ValueError("字体index必须为非负整数")

    scale = 2
    padding, gap = round(size * 0.05) * scale, round(size / 30) * scale
    inner = size * scale - 2 * padding
    font = ImageFont.truetype(str(font_path), round(style["font_size"] * scale), index=font_index)
    missing = (font.getmask("\uffff").size, bytes(font.getmask("\uffff")))
    if any((font.getmask(c).size, bytes(font.getmask(c))) == missing
           for c in caption if not c.isspace()):
        raise ValueError("指定字体缺少文案字符，请选择支持文案的字体")

    # Shrink only when necessary. Never enlarge the finished composition to fill a cell.
    minimum = round(min(18, style["font_size"]) * scale)
    for pixels in range(font.size, minimum - 1, -1):
        font = ImageFont.truetype(str(font_path), pixels, index=font_index)
        label = text_layer(caption, font, style, scale)
        if label.width <= inner and label.height <= size * scale * 0.18:
            break
    else:
        raise ValueError("文案无法在安全区内清晰排版，请缩短文案或调整字体、角度")

    image = image.convert("RGBA")
    box = visible_bbox(image)
    if box is None:
        raise ValueError("发现空白角色素材")
    box = (max(0, box[0] - 2), max(0, box[1] - 2),
           min(image.width, box[2] + 2), min(image.height, box[3] + 2))
    art = ImageOps.contain(image.crop(box), (inner, inner - label.height - gap),
                           Image.Resampling.LANCZOS)
    width, height = max(art.width, label.width), art.height + gap + label.height
    origin = ((size * scale - width) // 2, (size * scale - height) // 2)
    art_y, text_y = ((0, art.height + gap) if style["layout"] == "bottom"
                     else (label.height + gap, 0))
    art_pos = (origin[0] + (width - art.width) // 2, origin[1] + art_y)
    text_pos = (origin[0] + (width - label.width) // 2, origin[1] + text_y)
    canvas = Image.new("RGBA", (size * scale, size * scale))
    canvas.alpha_composite(art, art_pos)
    canvas.alpha_composite(label, text_pos)
    result = canvas.resize((size, size), Image.Resampling.LANCZOS)
    actual = visible_bbox(result)
    shift = (round((size - actual[0] - actual[2]) / 2),
             round((size - actual[1] - actual[3]) / 2))
    centered = Image.new("RGBA", (size, size))
    centered.alpha_composite(result, shift)
    result = centered

    def bounds(layer, position):
        b = visible_bbox(layer)
        return [round((b[i] + position[i % 2]) / scale) + shift[i % 2] for i in range(4)]

    details = dict(style, font_size=font.size / scale,
                   font={"path": str(font_path), "index": font_index,
                         "family": font.getname()[0], "variant": font.getname()[1]},
                   art_bbox=bounds(art, art_pos), text_bbox=bounds(label, text_pos),
                   bbox=list(visible_bbox(result)))
    return result, details


def render_caption(image, caption, font_path, size=240, *, style=None, font_index=0):
    return render_caption_with_details(image, caption, font_path, size,
                                       style=style, font_index=font_index)[0]
