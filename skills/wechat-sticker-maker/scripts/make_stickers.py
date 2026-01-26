import sys
import os
import argparse
from PIL import Image

try:
    from rembg import remove

    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


def determine_layout(img_width, img_height):
    """
    根据宽高比猜测网格布局
    """
    ratio = img_width / img_height
    # 宽高接近 -> 3x3 (9宫格) 或 2x2 (4宫格)
    if 0.9 < ratio < 1.1:
        return 3, 3
    # 竖屏 2:3 -> 3行2列 (6宫格 竖排)
    if 0.6 < ratio < 0.75:
        return 3, 2
    # 横屏 3:2 -> 2行3列 (6宫格 横排)
    if 1.3 < ratio < 1.6:
        return 2, 3
    # 竖屏 3:4 -> 4行3列 (12宫格)
    if 0.7 < ratio < 0.8:
        return 4, 3
    # 横屏 4:3 -> 3行4列 (12宫格)
    if 1.25 < ratio < 1.4:
        return 3, 4

    print(
        f"Warning: Cannot auto-detect layout for ratio {ratio:.2f}. Defaulting to 3x3."
    )
    return 3, 3


def process_image(image_path, layout_str, output_dir, remove_bg=False):
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)

    try:
        img = Image.open(image_path)
        # Ensure image is RGBA to verify transparency is handled correctly
        # This prevents P-mode (palette) images from turning black on resize/save
        img = img.convert("RGBA")
    except Exception as e:
        print(f"Error opening image: {e}")
        sys.exit(1)

    width, height = img.size
    print(f"Image Size: {width}x{height}")

    if remove_bg and not REMBG_AVAILABLE:
        print("Error: 'rembg' module not found. Please install it: pip install rembg")
        sys.exit(1)

    if remove_bg:
        print("AI Background removal enabled. Processing each sticker individually...")

    # OLD LOGIC: Full image background removal (Commented out/Removed)
    # Moving background removal to per-cell processing for better accuracy.

    if layout_str:
        try:
            rows, cols = map(int, layout_str.lower().split("x"))
        except ValueError:
            print("Error: Layout must be in format ROWSxCOLS (e.g. 3x3)")
            sys.exit(1)
    else:
        rows, cols = determine_layout(width, height)

    print(f"Layout: {rows} rows x {cols} cols (Total {rows * cols})")

    cell_width = width / cols
    cell_height = height / rows

    # Create directories
    main_dir = os.path.join(output_dir, "main")
    icon_dir = os.path.join(output_dir, "icon")

    os.makedirs(main_dir, exist_ok=True)
    os.makedirs(icon_dir, exist_ok=True)

    meta_file = os.path.join(output_dir, "meta.txt")
    info_file = os.path.join(output_dir, "info.txt")
    meta_lines = []

    count = 0
    total = rows * cols

    for r in range(rows):
        for c in range(cols):
            count += 1
            # Accurate floating point crop box
            left = c * cell_width
            upper = r * cell_height
            right = (c + 1) * cell_width
            lower = (r + 1) * cell_height

            box = (left, upper, right, lower)
            # Crop
            cell = img.crop(box)

            # AI Background Removal (Per Cell)
            if remove_bg:
                if not REMBG_AVAILABLE:
                    # Should be checked earlier, but just in case
                    print("Error: 'rembg' module missing.")
                    sys.exit(1)
                try:
                    # Remove bg for this specific cell with alpha matting for better edges
                    cell = remove(
                        cell,
                        alpha_matting=True,
                        alpha_matting_foreground_threshold=240,
                        alpha_matting_background_threshold=10,
                        alpha_matting_erode_size=10,
                    )
                except Exception as e:
                    print(f"Warning: Failed to remove bg for item {count}: {e}")

            # Stickers: 240x240 (Expression Image)
            sticker = cell.resize((240, 240), Image.Resampling.LANCZOS)
            sticker.save(os.path.join(main_dir, f"{count:02d}.png"), "PNG")

            # Icons: 50x50 (Chat Page Icon)
            icon = cell.resize((50, 50), Image.Resampling.LANCZOS)
            icon_path = os.path.join(icon_dir, f"{count:02d}.png")
            icon.save(icon_path, "PNG")

            # Save candidates from the first sticker (01.png)
            if count == 1:
                # Cover Candidate (240x240) - Same as main sticker
                # Note: Official spec requires transparent background, no square borders.
                # Our crop is rectangular/square. User needs to ensure source is transparent/appropriate.
                cover_candidate_path = os.path.join(output_dir, "cover_candidate.png")
                sticker.save(cover_candidate_path, "PNG")

                # Chat Icon Candidate (50x50) - Same as icon
                # Note: Official spec: Headshot preferred, no white border.
                chat_icon_candidate_path = os.path.join(
                    output_dir, "chat_icon_candidate.png"
                )
                icon.save(chat_icon_candidate_path, "PNG")

            # Add to meta lines
            meta_lines.append(f"{count:02d}.png\t[请输入表情含义]")

            if count % 3 == 0:
                print(f"Processed {count}/{total}...")

    print(f"Success! Generated {count} items.")
    print(f"  - Main Stickers (240x240): {main_dir}")
    print(f"  - Chat Icons (50x50):      {icon_dir}")

    # Write meta file
    with open(meta_file, "w", encoding="utf-8") as f:
        f.write("\n".join(meta_lines))
    print(f"  - Meta Info (Meanings):    {meta_file}")

    # Write info file (Name, Intro)
    info_content = """=== 微信表情专辑信息模板 ===
【表情名称】 (必填, 不超8个汉字, 无标点): 
【表情介绍】 (必填, 不超80个汉字): 
【一句话简介】 (必填, 不超11个汉字, 无标点): 

=== 图片素材要求 ===
1. [头像/封面图] (240x240, PNG, 透明背景): 已自动生成候选图 cover_candidate.png (取自第1张)
2. [聊天页图标] (50x50, PNG, 透明背景): 已自动生成候选图 chat_icon_candidate.png (取自第1张)
"""
    with open(info_file, "w", encoding="utf-8") as f:
        f.write(info_content)
    print(f"  - Album Info Template:     {info_file}")

    # Generate candidate Cover and Chat Icon from the first processed cell
    # Re-open the first image crop to avoid holding all in memory if possible,
    # but here we can just do it if we are still inside the loop?
    # Actually, let's just do it after the loop using the last 'cell' is risky if loop didn't run.
    # Safe way: Process the first cell again or save it during loop.
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WeChat Sticker Slicer")
    parser.add_argument("image", help="Path to the source grid image")
    parser.add_argument(
        "--layout", help="Grid layout, e.g., '3x3', '2x3'. If ignored, auto-detects."
    )
    parser.add_argument(
        "--output", default="sticker_output", help="Output directory path"
    )
    parser.add_argument(
        "--remove-bg",
        action="store_true",
        help="Automatically remove background using AI",
    )

    args = parser.parse_args()
    process_image(args.image, args.layout, args.output, args.remove_bg)
