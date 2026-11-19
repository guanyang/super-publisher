#!/usr/bin/env python3
"""Build an offline preview from exported sticker GIFs in the given order."""

import argparse
import base64
from html import escape
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageSequence


PAGE = """<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>动态表情审片</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0 auto;
    max-width: 64rem;
    padding: 1.5rem;
    background: #f8f8f5;
    color: #161a1e;
    font: 1rem/1.5 system-ui, sans-serif;
  }
  h1 { margin: 0 0 0.75rem; font-size: 1.5rem; }
  label { margin-right: 1rem; cursor: pointer; }
  main {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(10rem, 100%), 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
  }
  figure { margin: 0; min-width: 0; }
  .sticker {
    display: grid;
    place-items: center;
    height: 9rem;
    border: 1px solid #d9dfdc;
    border-radius: 0.5rem;
    background: #fff;
  }
  #dark:checked ~ main .sticker { background: #24292f; }
  #play:not(:checked) ~ main .animation,
  #play:checked ~ main .poster { display: none; }
  img { width: 7rem; height: 7rem; max-width: 100%; object-fit: contain; }
  figcaption { margin-top: 0.25rem; overflow-wrap: anywhere; }
</style>
<h1>动态表情审片</h1>
<input type="checkbox" id="play"><label for="play">播放动画</label>
<input type="checkbox" id="dark"><label for="dark">深色背景</label>
<main>
{cards}
</main>
</html>
"""


def sticker_card(path):
    data = path.read_bytes()
    with Image.open(BytesIO(data), formats=["GIF"]) as gif:
        duration, poster = -1, None
        for frame in ImageSequence.Iterator(gif):
            delay = frame.info.get("duration", 0)
            if delay > duration:
                duration, poster = delay, frame.convert("RGBA")
    poster.thumbnail((144, 144), Image.Resampling.LANCZOS)
    with BytesIO() as buffer:
        poster.save(buffer, format="PNG", optimize=True)
        still = base64.b64encode(buffer.getvalue()).decode("ascii")
    encoded = base64.b64encode(data).decode("ascii")
    return (
        '<figure><div class="sticker">'
        f'<img class="poster" src="data:image/png;base64,{still}" alt="">'
        f'<img class="animation" src="data:image/gif;base64,{encoded}" alt="">'
        f'</div><figcaption>{escape(path.stem)}</figcaption></figure>'
    )


def write_review(gifs, output):
    cards = "\n".join(sticker_card(path) for path in gifs)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(PAGE.replace("{cards}", cards))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gifs", type=Path, nargs="+", help="Exported GIFs in display order")
    parser.add_argument("--output", type=Path, required=True, help="New HTML output path")
    args = parser.parse_args()

    try:
        write_review(args.gifs, args.output)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
