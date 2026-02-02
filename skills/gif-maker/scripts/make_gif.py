import os
import sys
import glob
import argparse
import subprocess
from PIL import Image


def compress_gif(input_path, output_path, target_size_kb=950):
    """
    Compress GIF consistently using gifsicle via subprocess.
    """
    if not os.path.exists(input_path):
        print(f"[ERROR] {input_path} not found for compression.")
        return

    # Check initial size
    initial_size = os.path.getsize(input_path) / 1024
    print(f"[INFO] Initial size: {initial_size:.2f} KB")

    if initial_size <= target_size_kb:
        print(
            f"[INFO] Skipping compression. Size is already within target ({target_size_kb} KB)."
        )
        return

    print(f"[INFO] Compressing to under {target_size_kb} KB...")

    # Optimization levels and lossy values to try
    attempts = [
        # (optimize level, lossy factor, scale)
        (3, 30, 1.0),
        (3, 80, 1.0),
        (3, 120, 1.0),
        (3, 200, 1.0),
        (3, 80, 0.9),
        (3, 120, 0.9),
        (3, 200, 0.8),
    ]

    # Temporary file for compression attempts
    temp_output = output_path + ".tmp.gif"

    for opt_level, lossy, scale in attempts:
        cmd = ["gifsicle", "-O" + str(opt_level)]

        if lossy > 0:
            cmd.extend(["--lossy=" + str(lossy)])

        if scale < 1.0:
            cmd.extend(["--scale", str(scale)])

        cmd.extend([input_path, "-o", temp_output])

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            new_size = os.path.getsize(temp_output) / 1024
            print(
                f"  > Attempt (O{opt_level}, lossy={lossy}, scale={scale}): {new_size:.2f} KB"
            )

            if new_size <= target_size_kb:
                print(f"[SUCCESS] Compressed to {new_size:.2f} KB")
                os.replace(temp_output, output_path)
                return

        except Exception as e:
            print(f"[WARN] Error during compression attempt: {e}")
            if os.path.exists(temp_output):
                os.remove(temp_output)

    print(
        "[WARN] Could not compress to target size with current settings. Keeping original."
    )
    if os.path.exists(temp_output):
        os.remove(temp_output)


def create_gif(source, output_path, fps=12, layout=None, max_size_kb=0):
    """
    Create a GIF from a sequence of images or a sprite sheet.
    """
    frames = []

    # Check if source is directory or file
    if os.path.isdir(source):
        print(f"[INFO] Source is a directory: {source}")
        # Find images in the directory
        image_files = sorted(
            glob.glob(os.path.join(source, "*.png"))
            + glob.glob(os.path.join(source, "*.jpg"))
            + glob.glob(os.path.join(source, "*.jpeg"))
        )

        if not image_files:
            print(f"[ERROR] No images found in {source}")
            sys.exit(1)

        print(f"[INFO] Found {len(image_files)} images.")
        for img_path in image_files:
            try:
                img = Image.open(img_path).convert("RGBA")
                frames.append(img)
            except Exception as e:
                print(f"[WARN] Skipped {img_path}: {e}")

    elif os.path.isfile(source):
        print(f"[INFO] Source is a file: {source}")
        if not layout:
            print(
                "[ERROR] When source is a single file (sprite sheet), you MUST provide --layout (e.g., 4x4)."
            )
            sys.exit(1)

        try:
            rows, cols = map(int, layout.lower().split("x"))
        except ValueError:
            print("[ERROR] Layout format must be 'RowsxCols' (e.g., 4x4).")
            sys.exit(1)

        try:
            sheet = Image.open(source).convert("RGBA")
            sheet_w, sheet_h = sheet.size
            tile_w = sheet_w // cols
            tile_h = sheet_h // rows

            print(
                f"[INFO] Slicing {source} ({sheet_w}x{sheet_h}) into {rows}x{cols} grid (Tile: {tile_w}x{tile_h})."
            )

            for row in range(rows):
                for col in range(cols):
                    left = col * tile_w
                    top = row * tile_h
                    right = left + tile_w
                    bottom = top + tile_h

                    frame = sheet.crop((left, top, right, bottom))
                    frames.append(frame)

        except Exception as e:
            print(f"[ERROR] Failed to process sprite sheet: {e}")
            sys.exit(1)

    else:
        print(f"[ERROR] Source not found: {source}")
        sys.exit(1)

    if not frames:
        print("[ERROR] No frames to save.")
        sys.exit(1)

    # Calculate duration per frame in milliseconds
    duration_ms = int(1000 / fps)

    print(
        f"[INFO] Saving GIF to {output_path} (FPS: {fps}, Duration per frame: {duration_ms}ms, Loop: Forever)"
    )

    # Save GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        optimize=False,
        duration=duration_ms,
        loop=0,
        disposal=2,  # Restore to background color
    )
    print(f"[SUCCESS] Created {output_path}")

    # Compression logic
    if max_size_kb > 0:
        compress_gif(output_path, output_path, target_size_kb=max_size_kb)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a GIF from a sprite sheet or a sequence of images."
    )
    parser.add_argument(
        "source", help="Path to a directory of images OR a single sprite sheet file."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output.gif",
        help="Output GIF filename (default: output.gif).",
    )
    parser.add_argument(
        "--fps", type=int, default=12, help="Frames per second (default: 12)."
    )
    parser.add_argument(
        "--layout",
        help="Grid layout for sprite sheet (e.g., '4x4'). Required if source is a file.",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=0,
        help="Maximum size in KB to compress the GIF (default: 0, disabled).",
    )

    args = parser.parse_args()

    create_gif(args.source, args.output, args.fps, args.layout, args.max_size)


if __name__ == "__main__":
    main()
