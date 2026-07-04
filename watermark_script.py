import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import rawpy for RAW photo processing (.ARW, .DNG, .CR2, .CR3, etc.)
try:
    import rawpy
except ImportError:
    rawpy = None

def get_base_dir():
    # If compiled with PyInstaller, sys.executable points to the exe
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def apply_watermark(image, logo=None, text=None):
    """Apply a logo or text watermark to a PIL Image. Returns a new RGBA Image.

    Args:
        image: PIL Image (any mode — will be converted to RGBA internally).
        logo: Optional PIL Image (RGBA) to use as the watermark.
        text: Optional string to use as a text watermark (ignored if logo is provided).

    Returns:
        PIL Image in RGBA mode with the watermark composited.
    """
    working = image.convert("RGBA")
    overlay = Image.new("RGBA", working.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = working.size

    if logo:
        # Scale logo to 20% of image width, preserving aspect ratio
        scale_factor = 0.20
        logo_w, logo_h = logo.size
        aspect = logo_h / logo_w

        new_logo_w = int(width * scale_factor)
        new_logo_h = int(new_logo_w * aspect)

        # Clamp to minimum size while preserving aspect ratio
        if new_logo_w < 50:
            new_logo_w = 50
            new_logo_h = int(50 * aspect)

        # Clamp to image bounds while preserving aspect ratio
        if new_logo_w > width:
            new_logo_w = width
            new_logo_h = int(width * aspect)
        if new_logo_h > height:
            new_logo_h = height
            new_logo_w = int(height / aspect)

        resized_logo = logo.resize((new_logo_w, new_logo_h), Image.Resampling.LANCZOS)

        # Position: Centered
        x = (width - new_logo_w) // 2
        y = (height - new_logo_h) // 2
        overlay.paste(resized_logo, (x, y))

    elif text:
        # Font selection
        font_size = int(min(width, height) * 0.04)  # 4% of smaller dimension
        font_size = max(font_size, 12)

        font = None
        font_options = ["arial.ttf", "calibri.ttf", "segoeui.ttf", "DejaVuSans.ttf"]
        for font_name in font_options:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except IOError:
                continue
        if not font:
            font = ImageFont.load_default()

        # Calculate text dimensions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(text, font=font)

        # Position: Centered
        x = (width - text_w) // 2
        y = (height - text_h) // 2

        # Shadow + white text for visibility
        shadow_offset = max(1, int(font_size * 0.05))
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 180))

    return Image.alpha_composite(working, overlay)

def build_config():
    """Parse CLI arguments. Falls back to interactive prompts for missing values.

    Returns a namespace with: paths, text, logo, preserve_exif, output, quality, workers, no_interactive, interactive
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Image Watermark & RAW Converter Tool",
        epilog="Drag files onto the executable, or run with --help for CLI options."
    )
    parser.add_argument("paths", nargs="*", help="Files or folders to process (drag-and-drop)")
    parser.add_argument("--text", default=None, help="Text watermark (e.g. '@MyBrand'). Overrides logo.")
    parser.add_argument("--logo", default=None, help="Path to logo PNG (default: my_logo.png next to script)")
    parser.add_argument("--output", default=None, help="Output directory (default: watermarked_photos/)")
    parser.add_argument("--preserve-exif", action="store_true", default=None,
                        help="Preserve EXIF metadata in output files")
    parser.add_argument("--strip-exif", dest="preserve_exif", action="store_false",
                        help="Strip all EXIF metadata (default)")
    parser.add_argument("--quality", type=int, default=90, help="JPEG/WebP quality 1-100 (default: 90)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of parallel workers (default: CPU cores - 1)")
    parser.add_argument("--no-interactive", action="store_true",
                        help="Disable interactive prompts (use defaults for unset options)")

    args = parser.parse_args()

    # Interactive if --no-interactive is NOT set
    args.interactive = not args.no_interactive

    return args

def process_single_image(input_path, output_path, is_raw, logo_path_or_none, 
                         text_watermark, preserve_exif, quality):
    """Process a single image. Designed to run in a separate process.

    Args:
        input_path: Path to source image.
        output_path: Path to write output image.
        is_raw: Whether the file is a RAW format requiring rawpy.
        logo_path_or_none: Path to logo PNG, or None to use text.
        text_watermark: Text string for watermark (used if logo_path_or_none is None).
        preserve_exif: Whether to preserve EXIF metadata.
        quality: JPEG/WebP output quality (1-100).

    Returns:
        (filename, True, "") on success, (filename, False, error_message) on failure.
    """
    filename = os.path.basename(input_path)
    try:
        # Load logo fresh in each process (PIL Images can't cross process boundaries)
        logo_img = None
        if logo_path_or_none:
            try:
                logo_img = Image.open(logo_path_or_none).convert("RGBA")
            except Exception:
                pass

        # Extract EXIF if requested
        exif_bytes = None
        if preserve_exif:
            try:
                with Image.open(input_path) as temp_img:
                    exif_bytes = temp_img.info.get('exif')
            except Exception:
                pass

        # Open / decode image
        if is_raw:
            import rawpy as _rawpy
            with _rawpy.imread(input_path) as raw:
                rgb = raw.postprocess(use_camera_wb=True)
                img = Image.fromarray(rgb)
        else:
            img = Image.open(input_path)
            img = ImageOps.exif_transpose(img)

        # Apply watermark
        if logo_img:
            final_img = apply_watermark(img, logo=logo_img)
        else:
            final_img = apply_watermark(img, text=text_watermark)

        # Save
        save_args = {}
        if preserve_exif and exif_bytes:
            save_args["exif"] = exif_bytes

        output_lower = output_path.lower()
        if output_lower.endswith(('.jpg', '.jpeg')):
            save_args["quality"] = quality
            final_img.convert("RGB").save(output_path, "JPEG", **save_args)
        elif output_lower.endswith('.webp'):
            save_args["quality"] = quality
            final_img.convert("RGB").save(output_path, "WEBP", **save_args)
        else:
            final_img.save(output_path, **save_args)

        return (filename, True, "")
    except Exception as e:
        return (filename, False, str(e))

def process_images(config):
    base_dir = get_base_dir()
    raw_dir = os.path.join(base_dir, "raw_photos")
    output_dir = config.output or os.path.join(base_dir, "watermarked_photos")
    logo_path = os.path.join(base_dir, "my_logo.png")

    print("=========================================")
    print("  IMAGE WATERMARK & RAW CONVERTER TOOL   ")
    print("=========================================")
    print(f"Working Directory: {base_dir}\n")

    if rawpy is None:
        print("[WARNING] 'rawpy' library is not available. RAW files (.ARW, .DNG, .CR2, .CR3) cannot be processed.")
        print("Install it via: pip install rawpy numpy\n")

    # Determine files to process
    dragged_paths = config.paths
    is_drag_and_drop = len(dragged_paths) > 0
    files_to_check = []

    if is_drag_and_drop:
        print(f"Detected {len(dragged_paths)} dragged item(s). Processing directly...")
        for path in dragged_paths:
            if os.path.isdir(path):
                try:
                    for root, _, subfiles in os.walk(path):
                        for sf in subfiles:
                            files_to_check.append(os.path.join(root, sf))
                except Exception as e:
                    print(f"Error scanning folder '{path}': {e}")
            elif os.path.isfile(path):
                files_to_check.append(path)
    else:
        print("Running in batch mode (scanning 'raw_photos' folder)...")
        # Create directories if they don't exist
        if not os.path.exists(raw_dir):
            os.makedirs(raw_dir)
            print(f"Created folder: '{raw_dir}'")
            print("--> Please drop your photos (JPG, PNG, ARW, DNG, etc.) into the 'raw_photos' folder.")
            print("--> Then run this app again.")
            return

        try:
            files_to_check = [os.path.join(raw_dir, f) for f in os.listdir(raw_dir)]
        except Exception as e:
            print(f"Error reading raw folder: {e}")
            return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output folder: '{output_dir}'")

    # Resolve watermark source
    logo_img = None
    text_watermark = None

    if config.text:
        text_watermark = config.text
        print(f"Using text watermark: '{text_watermark}'")
    else:
        # Check logo
        effective_logo_path = config.logo or logo_path
        if os.path.exists(effective_logo_path):
            try:
                logo_img = Image.open(effective_logo_path).convert("RGBA")
                print(f"Found watermark logo: '{effective_logo_path}'")
                logo_img.close()  # Just testing opening; individual processes will open as needed
            except Exception as e:
                print(f"Warning: Could not open '{effective_logo_path}': {e}. Falling back to text.")

        if logo_img is None:
            print("No logo found.")
            if config.interactive:
                text_watermark = input("Enter text watermark (or Enter for '© PROTECTED'): ").strip()
            if not text_watermark:
                text_watermark = "© PROTECTED"
            print(f"Using text watermark: '{text_watermark}'")

    # Resolve EXIF preference
    if config.preserve_exif is not None:
        preserve_exif = config.preserve_exif
    elif config.interactive:
        resp = input("\nPreserve EXIF metadata (GPS location, camera details, settings) in output JPEGs? (y/N): ").strip().lower()
        preserve_exif = resp == 'y'
    else:
        preserve_exif = False

    if preserve_exif:
        print("-> EXIF metadata will be preserved where possible.\n")
    else:
        print("-> EXIF metadata will be completely stripped for privacy.\n")

    # Find images
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')
    raw_extensions = ('.arw', '.cr2', '.cr3', '.nef', '.dng', '.raw')
    
    images_to_process = []
    for filepath in files_to_check:
        filename = os.path.basename(filepath)
        f_lower = filename.lower()
        if f_lower.endswith(valid_extensions):
            images_to_process.append((filepath, filename, False))
        elif f_lower.endswith(raw_extensions):
            if rawpy is not None:
                images_to_process.append((filepath, filename, True))
            else:
                print(f"Skipping RAW file '{filename}' (rawpy library missing).")

    if not images_to_process:
        if is_drag_and_drop:
            print("No supported files were found in the dragged items.")
        else:
            print("No supported images (JPG, PNG, WebP, ARW, DNG, etc.) found in 'raw_photos' folder.")
            print("Drop some images in there and run the tool again.")
        return

    print(f"Processing {len(images_to_process)} image(s)...")

    # Build tasks
    tasks = []
    for input_path, filename, is_raw in images_to_process:
        if is_raw:
            base_name = os.path.splitext(filename)[0]
            output_filename = base_name + ".jpg"
        else:
            output_filename = filename
        output_path = os.path.join(output_dir, output_filename)

        effective_logo = None
        if logo_img is not None or (config.logo and os.path.exists(config.logo)):
            effective_logo = config.logo or logo_path
        
        tasks.append((input_path, output_path, is_raw, effective_logo,
                      text_watermark, preserve_exif, config.quality))

    # Process images (parallel or sequential)
    total = len(tasks)
    processed_count = 0
    workers = config.workers or max(1, (os.cpu_count() or 2) - 1)

    if workers == 1 or total == 1:
        # Sequential - simpler output, better for debugging or single files
        for i, task in enumerate(tasks, 1):
            fname, ok, err = process_single_image(*task)
            if ok:
                processed_count += 1
                print(f"[{i}/{total}] Done: {fname}")
            else:
                print(f"[{i}/{total}] FAILED: {fname}: {err}")
    else:
        print(f"Using {workers} parallel workers...\n")
        with ProcessPoolExecutor(max_workers=workers) as pool:
            future_to_idx = {}
            for i, task in enumerate(tasks, 1):
                future = pool.submit(process_single_image, *task)
                future_to_idx[future] = i

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                fname, ok, err = future.result()
                if ok:
                    processed_count += 1
                    print(f"[{idx}/{total}] Done: {fname}")
                else:
                    print(f"[{idx}/{total}] FAILED: {fname}: {err}")

    print(f"\nSuccess! Processed {processed_count} image(s).")
    print(f"Protected images saved in: '{output_dir}'")
    if preserve_exif:
        print("EXIF metadata has been preserved in the output images.")
    else:
        print("All location data and EXIF metadata have been stripped.")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    try:
        config = build_config()
        process_images(config)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    # Only pause for Enter when running interactively (e.g. no --no-interactive flag)
    if '--no-interactive' not in sys.argv:
        input("\nProcessing complete. Press Enter to exit...")

