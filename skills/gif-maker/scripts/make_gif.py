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
        raise ValueError(f"{input_path} not found for compression")
    if target_size_kb <= 0:
        raise ValueError("target_size_kb must be positive")
    with Image.open(input_path) as original:
        expected_size = original.size

    # Check initial size
    initial_size = os.path.getsize(input_path) / 1024
    print(f"[INFO] Initial size: {initial_size:.2f} KB")

    if initial_size <= target_size_kb:
        print(
            f"[INFO] Skipping compression. Size is already within target ({target_size_kb} KB)."
        )
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            import shutil
            shutil.copy2(input_path, output_path)
        return

    print(f"[INFO] Compressing to under {target_size_kb} KB...")

    # Compression must keep the original pixel dimensions.
    attempts = [
        (3, 30),
        (3, 80),
        (3, 120),
        (3, 200),
    ]

    # Temporary file for compression attempts
    temp_output = output_path + ".tmp.gif"

    for opt_level, lossy in attempts:
        cmd = ["gifsicle", "-O" + str(opt_level)]

        if lossy > 0:
            cmd.extend(["--lossy=" + str(lossy)])

        cmd.extend([input_path, "-o", temp_output])

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            new_size = os.path.getsize(temp_output) / 1024
            with Image.open(temp_output) as compressed:
                if compressed.size != expected_size:
                    raise ValueError("Compression changed GIF dimensions")
            print(
                f"  > Attempt (O{opt_level}, lossy={lossy}): {new_size:.2f} KB"
            )

            if new_size <= target_size_kb:
                print(f"[SUCCESS] Compressed to {new_size:.2f} KB")
                os.replace(temp_output, output_path)
                return

        except FileNotFoundError as e:
            raise ValueError("gifsicle is required for GIF compression") from e
        except (OSError, ValueError, subprocess.CalledProcessError) as e:
            print(f"[WARN] Error during compression attempt: {e}")
            if os.path.exists(temp_output):
                os.remove(temp_output)

    if os.path.exists(temp_output):
        os.remove(temp_output)
    raise ValueError("Could not meet GIF size target without changing dimensions")


def create_gif(source, output_path, fps=12, layout=None, max_size_kb=0):
    """
    Create a GIF from a sequence of images or a sprite sheet.
    """
    if fps <= 0:
        raise ValueError("fps must be positive")
    if os.path.exists(output_path):
        raise ValueError("Output already exists; choose a new version path")
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
            if rows <= 0 or cols <= 0:
                raise ValueError("Rows and columns must be positive")
        except ValueError:
            print("[ERROR] Layout format must be 'RowsxCols' (e.g., 4x4).")
            sys.exit(1)

        try:
            sheet = Image.open(source).convert("RGBA")
            sheet_w, sheet_h = sheet.size
            tile_w = sheet_w / cols
            tile_h = sheet_h / rows

            print(
                f"[INFO] Slicing {source} ({sheet_w}x{sheet_h}) into {rows}x{cols} grid (Tile: {tile_w}x{tile_h})."
            )

            for row in range(rows):
                for col in range(cols):
                    left = round(col * tile_w)
                    top = round(row * tile_h)
                    right = round((col + 1) * tile_w)
                    bottom = round((row + 1) * tile_h)

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
    if any(frame.size != frames[0].size for frame in frames):
        raise ValueError("Animation frames must have matching dimensions")

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

    try:
        create_gif(args.source, args.output, args.fps, args.layout, args.max_size)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"GIF generation failed: {exc}\n")


if __name__ == "__main__":
    main()
