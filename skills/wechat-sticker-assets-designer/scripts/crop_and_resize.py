import sys
import os
import argparse
from PIL import Image

def process_image(img_path, target_w, target_h, anchor='center'):
    if not os.path.exists(img_path):
        print(f"Error: File not found: {img_path}")
        sys.exit(1)
        
    try:
        img = Image.open(img_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        sys.exit(1)
        
    w, h = img.size
    
    # Check if already in target dimensions
    if w == target_w and h == target_h:
        print(f"Image {img_path} is already {target_w}x{target_h}. Skipping crop and resize.")
        return
        
    # Check if aspect ratio matches but only needs resizing
    target_ratio = target_w / target_h
    current_ratio = w / h
    
    # We allow a very small float discrepancy for aspect ratio check
    if abs(current_ratio - target_ratio) < 0.001:
        print(f"Aspect ratio matches. Resizing {img_path} from {w}x{h} to {target_w}x{target_h}...")
        resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        resized.save(img_path, "PNG")
        return
        
    # Crop and resize
    print(f"Aspect ratio mismatch ({w}x{h} vs {target_w}x{target_h}). Cropping and resizing...")
    if current_ratio > target_ratio:
        # Current is wider than target -> crop width (left/right)
        new_w = int(h * target_ratio)
        new_h = h
        if anchor == 'left':
            left = 0
        elif anchor == 'right':
            left = w - new_w
        else:
            left = (w - new_w) // 2
        top = 0
    else:
        # Current is taller than target -> crop height (top/bottom)
        new_w = w
        new_h = int(w / target_ratio)
        left = 0
        if anchor == 'top':
            top = 0
        elif anchor == 'bottom':
            top = h - new_h
        else:
            top = (h - new_h) // 2
            
    cropped = img.crop((left, top, left + new_w, top + new_h))
    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    resized.save(img_path, "PNG")
    print(f"Successfully processed {img_path} to {target_w}x{target_h}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Cropper and Resizer for WeChat Sticker Assets")
    parser.add_argument("image", help="Path to the image to process")
    parser.add_argument("--width", type=int, required=True, help="Target width")
    parser.add_argument("--height", type=int, required=True, help="Target height")
    parser.add_argument("--anchor", default="center", choices=["center", "top", "bottom", "left", "right"],
                        help="Anchor side to keep when cropping (default: center)")
                        
    args = parser.parse_args()
    process_image(args.image, args.width, args.height, args.anchor)
