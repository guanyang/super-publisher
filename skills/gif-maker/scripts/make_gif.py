"""Prepare continuous frames and publish a verified GIF with review artifacts."""

import argparse
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


ALPHA_VISIBLE = 24


def visible_bbox(image):
    return image.getchannel("A").point(lambda a: 255 if a > ALPHA_VISIBLE else 0).getbbox()


def natural_key(path):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", path.name.casefold())]


def open_frame(path):
    try:
        with Image.open(path) as image:
            if getattr(image, "is_animated", False):
                raise ValueError("Animated inputs must be unpacked into explicit frames")
            return image.convert("RGBA")
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read frame {path}: {exc}") from exc


def grid_cells(image, layout, boundaries=None):
    try:
        rows, cols = map(int, layout.lower().split("x"))
        if rows <= 0 or cols <= 0 or rows > image.height or cols > image.width:
            raise ValueError()
    except (AttributeError, ValueError):
        raise ValueError("Layout must be positive rows x columns within the image") from None
    transparent = image.getchannel("A").getextrema()[0] < 255
    slicer = Path(__file__).resolve().parents[2] / "wechat-sticker-maker/scripts/make_stickers.py"
    if slicer.is_file():
        spec = importlib.util.spec_from_file_location("gif_grid_slicer", slicer)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cells, cuts = module.slice_grid(image, layout, boundaries, allow_opaque=not transparent)
    else:
        # Standalone installation: equal or supplied cuts are accepted only if safe.
        cuts = {}
        for axis, count, length in [("x", cols, image.width), ("y", rows, image.height)]:
            values = (boundaries or {}).get(axis, [round(i * length / count) for i in range(count + 1)])
            if (len(values) != count + 1 or values[0] != 0 or values[-1] != length
                    or any(type(v) is not int for v in values)
                    or any(a >= b for a, b in zip(values, values[1:]))):
                raise ValueError(f"Invalid {axis} boundaries")
            if transparent:
                for position in values[1:-1]:
                    box = ((position, 0, position + 1, image.height) if axis == "x"
                           else (0, position, image.width, position + 1))
                    if image.getchannel("A").crop(box).getextrema()[1] > ALPHA_VISIBLE:
                        raise ValueError("Grid cut crosses artwork; install wechat-sticker-maker for gap search "
                                         "or supply safe boundaries / separate frames")
            cuts[axis] = values
        cells = [image.crop((cuts["x"][c], cuts["y"][r], cuts["x"][c+1], cuts["y"][r+1]))
                 for r in range(rows) for c in range(cols)]
    # Restore nominal cell coordinates after adaptive cuts; do not center each pose.
    offsets = [(cuts["x"][c] - round(c * image.width / cols),
                cuts["y"][r] - round(r * image.height / rows))
               for r in range(rows) for c in range(cols)]
    left, top = min(0, min(x for x, _ in offsets)), min(0, min(y for _, y in offsets))
    width = max(x + cell.width for cell, (x, _) in zip(cells, offsets)) - left
    height = max(y + cell.height for cell, (_, y) in zip(cells, offsets)) - top
    frames = []
    for cell, (x, y) in zip(cells, offsets):
        frame = Image.new("RGBA", (width, height))
        frame.alpha_composite(cell, (x-left, y-top))
        frames.append(frame)
    return frames, cuts


def load_frames(source, layout=None, boundaries=None):
    source = Path(source)
    if boundaries is not None and not isinstance(boundaries, dict):
        raise ValueError("Boundaries must be a JSON object containing x/y arrays")
    if source.is_dir():
        if layout or boundaries:
            raise ValueError("Layout and boundaries apply only to sprite sheets")
        paths = sorted((p for p in source.iterdir()
                        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}),
                       key=natural_key)
        if not paths:
            raise ValueError("No frame images found")
        frames = [open_frame(p) for p in paths]
        if any(f.size != frames[0].size for f in frames):
            raise ValueError("Animation frames must have matching dimensions")
        return frames, {"input_order": [str(p.resolve()) for p in paths]}
    if not source.is_file():
        raise ValueError(f"Source not found: {source}")
    if not layout:
        raise ValueError("Sprite sheets require an explicit --layout rows x columns")
    frames, cuts = grid_cells(open_frame(source), layout, boundaries)
    return frames, {"input_order": [str(source.resolve())], "grid_cuts": cuts}


def prepare_frames(frames, size=None, anchor="center", overlay=None):
    if anchor not in {"center", "bottom"}:
        raise ValueError("Anchor must be center or bottom")
    transform = {"size": list(frames[0].size), "scale": 1, "crop": None, "anchor": anchor}
    if size is not None:
        if type(size) is not int or size < 16:
            raise ValueError("Output size must be an integer >= 16")
        boxes = [b for frame in frames if (b := visible_bbox(frame)) is not None]
        if not boxes:
            raise ValueError("Animation is entirely transparent")
        w, h = frames[0].size
        box = (max(0, min(b[0] for b in boxes)-2), max(0, min(b[1] for b in boxes)-2),
               min(w, max(b[2] for b in boxes)+2), min(h, max(b[3] for b in boxes)+2))
        padding = max(1, round(size * 0.05))
        scale = min((size-2*padding)/(box[2]-box[0]), (size-2*padding)/(box[3]-box[1]))
        target = (round((box[2]-box[0])*scale), round((box[3]-box[1])*scale))
        position = ((size-target[0])//2,
                    size-padding-target[1] if anchor == "bottom" else (size-target[1])//2)
        prepared = []
        for frame in frames:
            canvas = Image.new("RGBA", (size, size))
            canvas.alpha_composite(frame.crop(box).resize(target, Image.Resampling.LANCZOS), position)
            prepared.append(canvas)
        frames = prepared
        transform.update(size=[size, size], crop=list(box), scale=scale, position=position)
    if overlay:
        layer = open_frame(overlay)
        if layer.size != frames[0].size:
            raise ValueError("Static overlay must match the final canvas dimensions")
        frames = [Image.alpha_composite(frame, layer) for frame in frames]
    return frames, transform


def frame_durations(count, fps, durations=None):
    if not math.isfinite(fps) or not 0 < fps <= 100:
        raise ValueError("FPS must be > 0 and <= 100 (GIF minimum delay is 10ms)")
    desired = [1000/fps] * count if durations is None else list(durations)
    if len(desired) != count or any(type(v) not in {int, float} or not math.isfinite(v)
                                    or not 10 <= v <= 655350 for v in desired):
        raise ValueError("Durations must match the playback sequence, each within 10..655350ms")
    ticks, elapsed, result = 0, 0, []
    for value in desired:
        elapsed += value
        end = round(elapsed/10)
        result.append((end-ticks)*10)
        ticks = end
    return result, sum(desired)


def quantize_frames(frames, alpha_cutoff=128):
    if type(alpha_cutoff) is not int or not 1 <= alpha_cutoff <= 255:
        raise ValueError("Alpha cutoff must be an integer within 1..255")
    colors = bytearray()
    for frame in frames:
        sample = frame.copy()
        sample.thumbnail((256, 256), Image.Resampling.LANCZOS)
        data = sample.tobytes()
        for i in range(0, len(data), 4):
            if data[i+3] >= alpha_cutoff:
                colors.extend(data[i:i+3])
    if not colors:
        raise ValueError("Animation has no visible pixels at the chosen alpha cutoff")
    count = len(colors)//3
    width = min(256, count)
    height = math.ceil(count/width)
    colors.extend(colors[-3:] * (width*height-count))
    sample = Image.frombytes("RGB", (width, height), bytes(colors))
    palette = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    values = (palette.getpalette() + [0]*765)[:765]
    occupied = {tuple(values[i:i+3]) for i in range(0, 765, 3)}
    reserved = next((255, 0, b) for b in range(256) if (255, 0, b) not in occupied)
    replacement = min(range(255), key=lambda i: sum((values[i*3+j]-reserved[j])**2 for j in range(3)))
    values += list(reserved)
    palette.putpalette(values)
    frames_p = []
    for frame in frames:
        indexed = frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        # Index 255 belongs exclusively to transparency, even for opaque magenta pixels.
        indexed = indexed.point(list(range(255)) + [replacement])
        indexed.putpalette(values)
        indexed.paste(255, mask=frame.getchannel("A").point(lambda a: 255 if a < alpha_cutoff else 0))
        indexed.info.update(transparency=255, background=255)
        frames_p.append(indexed)
    return frames_p, bytes(values)


def decode_gif(path):
    frames, durations = [], []
    with Image.open(path) as image:
        if image.format != "GIF":
            raise ValueError("Encoded output is not GIF")
        size, loop = image.size, image.info.get("loop")
        for i in range(image.n_frames):
            image.seek(i)
            frames.append(image.copy().convert("RGBA"))
            durations.append(image.info.get("duration", 0))
    return {"frames": frames, "durations": durations, "size": size, "loop": loop,
            "duration_ms": sum(durations)}


def same_timeline(a, b, pixels=True):
    if any(a[key] != b[key] for key in ["size", "loop", "duration_ms"]):
        return False

    def content(frame):
        if not pixels:
            return frame.getchannel("A").tobytes()
        clean = Image.new("RGBA", frame.size)
        clean.paste(frame, (0, 0), frame.getchannel("A"))
        return clean.tobytes()

    aa = [(content(f), d) for f, d in zip(a["frames"], a["durations"]) if d > 0]
    bb = [(content(f), d) for f, d in zip(b["frames"], b["durations"]) if d > 0]
    if not aa or not bb:
        return content(a["frames"][0]) == content(b["frames"][0])
    i = j = 0
    left, right = aa[0][1], bb[0][1]
    while i < len(aa) and j < len(bb):
        if aa[i][0] != bb[j][0]:
            return False
        step = min(left, right)
        left -= step
        right -= step
        if not left:
            i += 1
            if i < len(aa):
                left = aa[i][1]
        if not right:
            j += 1
            if j < len(bb):
                right = bb[j][1]
    return i == len(aa) and j == len(bb)


def compress_gif(input_path, output_path, target_size_kb=950, optimize=False):
    source, output = Path(input_path), Path(output_path)
    if not math.isfinite(target_size_kb) or target_size_kb < 0:
        raise ValueError("Size target must be nonnegative; zero disables the limit")
    if output.exists() and output.resolve() != source.resolve():
        raise ValueError("Compression output already exists")
    reference = decode_gif(source)
    within = not target_size_kb or source.stat().st_size <= target_size_kb*1024
    if within and not optimize and source.resolve() == output.resolve():
        return {"method": "none", "bytes": output.stat().st_size}
    with tempfile.TemporaryDirectory(prefix=".gif-compress-", dir=output.parent) as temporary:
        temp = Path(temporary)
        selected, method, warning = source, "none", None
        attempts = [0] if optimize else []
        if not within:
            attempts = [0, 30, 80, 120, 200]
        for lossy in attempts:
            candidate = temp / "candidate.gif"
            command = ["gifsicle", "-O3"] + ([f"--lossy={lossy}"] if lossy else [])
            command += [str(source), "-o", str(candidate)]
            try:
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE, timeout=60)
                decoded = decode_gif(candidate)
                if not same_timeline(reference, decoded, pixels=not lossy):
                    raise ValueError("Compression changed canvas, timeline, loop, pixels or transparency")
                if (candidate.stat().st_size < source.stat().st_size
                        and (not target_size_kb or candidate.stat().st_size <= target_size_kb*1024)):
                    selected, method = candidate, "lossless-O3" if not lossy else f"lossy-{lossy}"
                    break
            except FileNotFoundError as exc:
                if not within:
                    raise ValueError("gifsicle is required to meet the size target") from exc
                warning = "Optional lossless optimization skipped: gifsicle is unavailable"
                break
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                warning = str(exc)
        if not within and selected == source:
            raise ValueError("Could not meet GIF size target without changing dimensions or timing")
        if selected != source or output.resolve() != source.resolve():
            shutil.copyfile(selected, temp / "accepted.gif")
            if output.resolve() == source.resolve():
                os.replace(temp / "accepted.gif", output)
            else:
                os.link(temp / "accepted.gif", output)
        return {"method": method, "bytes": output.stat().st_size, "warning": warning}


def write_review(decoded, path):
    frames = decoded["frames"]
    indices = sorted({round(i*(len(frames)-1)/min(11, len(frames)-1))
                      for i in range(min(12, len(frames)))}) if len(frames) > 1 else [0]
    thumb = frames[0].copy()
    thumb.thumbnail((240, 240), Image.Resampling.LANCZOS)
    w, h = thumb.size
    tile_w, tile_h = w+16, h+30
    canvas = Image.new("RGB", (4*tile_w, math.ceil(len(indices)/2)*tile_h), "#e6ece9")
    draw = ImageDraw.Draw(canvas)
    for n, index in enumerate(indices):
        for dark in [0, 1]:
            slot = n*2+dark
            x, y = slot%4*tile_w, slot//4*tile_h
            tile = Image.new("RGBA", (w, h), "#283b3a" if dark else "#e6ece9")
            tile.alpha_composite(frames[index].resize((w, h), Image.Resampling.LANCZOS))
            canvas.paste(tile.convert("RGB"), (x+8, y+24))
            draw.text((x+8, y+5), f"Frame {index+1}: {decoded['durations'][index]}ms", fill="#121c1b")
    canvas.save(path, optimize=True)
    return [i+1 for i in indices]


def create_gif(source, output_path, fps=12, layout=None, max_size_kb=0, *,
               alpha_cutoff=128, size=None, anchor="center", boundaries=None,
               sequence=None, durations=None, overlay=None, optimize=False):
    output = Path(output_path).resolve()
    report_path = output.with_suffix(".animation.json")
    preview_path = output.with_suffix(".preview.png")
    if any(p.exists() for p in [output, report_path, preview_path]):
        raise ValueError("Output or review artifacts already exist; choose a new version path")
    if not math.isfinite(max_size_kb) or max_size_kb < 0:
        raise ValueError("Size target must be nonnegative")
    frames, inputs = load_frames(source, layout, boundaries)
    order = list(range(1, len(frames)+1)) if sequence is None else list(sequence)
    if not order or any(type(i) is not int or not 1 <= i <= len(frames) for i in order):
        raise ValueError("Sequence must contain valid 1-based frame indices")
    delays, requested_ms = frame_durations(len(order), fps, durations)
    prepared, transform = prepare_frames([frames[i-1] for i in order], size, anchor, overlay)
    indexed, palette = quantize_frames(prepared, alpha_cutoff)
    expected = {"frames": [f.copy().convert("RGBA") for f in indexed], "durations": delays,
                "size": indexed[0].size, "loop": 0, "duration_ms": sum(delays)}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".gif-build-", dir=output.parent) as temporary:
        temp = Path(temporary)
        encoded = temp / "output.gif"
        indexed[0].save(encoded, save_all=True, append_images=indexed[1:], duration=delays,
                        loop=0, disposal=2, transparency=255, background=255,
                        palette=palette, optimize=False)
        if not same_timeline(expected, decode_gif(encoded)):
            raise ValueError("GIF encoding changed the expected timeline or transparent pixels")
        compression = compress_gif(encoded, encoded, max_size_kb, optimize)
        decoded = decode_gif(encoded)
        if not same_timeline(expected, decoded, pixels=not compression["method"].startswith("lossy")):
            raise ValueError("Final GIF failed decoded timeline verification")
        sampled = write_review(decoded, temp / "preview.png")
        report = dict(inputs, source=str(Path(source).resolve()), output=str(output),
                      source_frame_count=len(frames), playback_sequence=order,
                      playback_durations_ms=delays, requested_duration_ms=requested_ms,
                      encoded_frame_count=len(decoded["frames"]), duration_ms=decoded["duration_ms"],
                      size=list(decoded["size"]), loop=decoded["loop"], alpha_cutoff=alpha_cutoff,
                      shared_palette=True, transform=transform,
                      overlay=str(Path(overlay).resolve()) if overlay else None,
                      compression=compression, preview_sampled_encoded_frames=sampled,
                      preview=preview_path.name, local_checks_passed=True, platform_review_verified=False)
        (temp / "animation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
        published = []
        try:
            for src, dest in [(temp/"preview.png", preview_path), (temp/"animation.json", report_path),
                              (encoded, output)]:
                os.link(src, dest)  # Atomic, refuses overwrite; GIF is the final success marker.
                published.append(dest)
        except OSError:
            for path in published:
                path.unlink()
            raise
    return {"output": str(output), "report": str(report_path), "preview": str(preview_path),
            "frames": report["encoded_frame_count"], "duration_ms": report["duration_ms"],
            "bytes": output.stat().st_size}


def comma_list(value, cast):
    try:
        return [cast(v.strip()) for v in value.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError("Use a comma-separated numeric list") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Continuous frame directory or sprite sheet")
    parser.add_argument("--output", "-o", default="output.gif")
    parser.add_argument("--fps", type=float, default=12)
    parser.add_argument("--layout", help="Explicit rows x columns for sprite sheets")
    parser.add_argument("--max-size", type=float, default=0, help="Maximum KiB; zero disables limit")
    parser.add_argument("--alpha-cutoff", type=int, default=128)
    parser.add_argument("--size", type=int, help="Optional square output canvas, e.g. 240")
    parser.add_argument("--anchor", choices=["center", "bottom"], default="center")
    parser.add_argument("--boundaries", type=Path, help="JSON containing x/y boundary arrays")
    parser.add_argument("--sequence", type=lambda v: comma_list(v, int), help="1-based frame order, e.g. 1,2,3,2")
    parser.add_argument("--durations", type=lambda v: comma_list(v, float), help="Per playback-frame milliseconds")
    parser.add_argument("--overlay", type=Path, help="Static RGBA layer matching the final canvas")
    parser.add_argument("--optimize", action="store_true", help="Try optional lossless gifsicle -O3 even below limit")
    args = parser.parse_args()
    boundaries = None
    try:
        if args.boundaries:
            boundaries = json.loads(args.boundaries.read_text())
        result = create_gif(args.source, args.output, args.fps, args.layout, args.max_size,
                            alpha_cutoff=args.alpha_cutoff, size=args.size, anchor=args.anchor,
                            boundaries=boundaries, sequence=args.sequence, durations=args.durations,
                            overlay=args.overlay, optimize=args.optimize)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(2, f"GIF generation failed: {exc}\n")


if __name__ == "__main__":
    main()
