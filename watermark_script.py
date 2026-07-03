import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

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

def process_images():
    base_dir = get_base_dir()
    raw_dir = os.path.join(base_dir, "raw_photos")
    output_dir = os.path.join(base_dir, "watermarked_photos")
    logo_path = os.path.join(base_dir, "my_logo.png")

    print("=========================================")
    print("  IMAGE WATERMARK & RAW CONVERTER TOOL   ")
    print("=========================================")
    print(f"Working Directory: {base_dir}\n")

    if rawpy is None:
        print("[WARNING] 'rawpy' library is not available. RAW files (.ARW, .DNG, .CR2, .CR3) cannot be processed.")
        print("Install it via: pip install rawpy numpy\n")

    # Determine files to process (Drag-and-drop vs. Batch raw_photos folder)
    dragged_paths = sys.argv[1:]
    is_drag_and_drop = len(dragged_paths) > 0
    files_to_check = []

    if is_drag_and_drop:
        print(f"Detected {len(dragged_paths)} dragged item(s). Processing directly...")
        for path in dragged_paths:
            if os.path.isdir(path):
                # If a folder was dragged, find all files in it
                try:
                    for root, _, subfiles in os.walk(path):
                        for sf in subfiles:
                            files_to_check.append(os.path.join(root, sf))
                except Exception as e:
                    print(f"Error scanning dragged folder '{path}': {e}")
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

    # Check for logo
    has_logo = os.path.exists(logo_path)
    logo_img = None
    text_watermark = None

    if has_logo:
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            print(f"Found watermark logo: '{logo_path}'")
        except Exception as e:
            print(f"Warning: Could not open '{logo_path}': {e}. Falling back to text.")
            has_logo = False

    if not has_logo:
        print("No logo ('my_logo.png') found in the folder.")
        text_watermark = input("Enter the text watermark to use (e.g., '@MyBrand' or press Enter for default '© PROTECTED'): ").strip()
        if not text_watermark:
            text_watermark = "© PROTECTED"
        print(f"Using text watermark: '{text_watermark}'")

    # Prompt user for EXIF metadata preservation choice
    preserve_input = input("\nPreserve EXIF metadata (GPS location, camera details, settings) in output JPEGs? (y/N): ").strip().lower()
    preserve_exif = preserve_input == 'y'
    if preserve_exif:
        print("-> EXIF metadata will be preserved where possible.\n")
    else:
        print("-> EXIF metadata will be completely stripped for privacy.\n")

    # Find images
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')
    raw_extensions = ('.arw', '.cr2', '.cr3', '.nef', '.dng', '.raw')
    
    # Filter target files
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

    processed_count = 0
    for input_path, filename, is_raw in images_to_process:
        # For RAW images, output format is converted to .jpg
        if is_raw:
            base_name = os.path.splitext(filename)[0]
            output_filename = base_name + ".jpg"
        else:
            output_filename = filename
            
        output_path = os.path.join(output_dir, output_filename)

        try:
            # 1. Extract EXIF data if requested
            exif_bytes = None
            if preserve_exif:
                try:
                    # Pillow TIFF parser handles EXIF metadata blocks on TIFF-based files (ARW, CR2, NEF, DNG, JPG)
                    with Image.open(input_path) as temp_img:
                        exif_bytes = temp_img.info.get('exif')
                except Exception as e:
                    # Fail silently for files like CR3 that don't support TIFF headers directly in Pillow
                    pass

            # 2. Open / Decode the image
            if is_raw:
                print(f"Developing RAW: {filename}...")
                with rawpy.imread(input_path) as raw:
                    # Postprocess raw using camera white balance
                    rgb = raw.postprocess(use_camera_wb=True)
                    img = Image.fromarray(rgb)
            else:
                img = Image.open(input_path)
                # Rotate standard image according to EXIF orientation tag if present
                img = ImageOps.exif_transpose(img)
                
            # Convert to RGBA for watermark overlaying
            working_img = img.convert("RGBA")
            watermark_layer = Image.new("RGBA", working_img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)

            width, height = working_img.size

            if has_logo and logo_img:
                # Resize logo to fit nicely (e.g., 20% of the image's width/height)
                scale_factor = 0.20
                logo_w, logo_h = logo_img.size
                new_logo_w = int(width * scale_factor)
                new_logo_h = int(logo_h * (new_logo_w / logo_w))

                # Ensure it's not too small or too big
                new_logo_w = max(min(new_logo_w, width), 50)
                new_logo_h = max(min(new_logo_h, height), 50)

                resized_logo = logo_img.resize((new_logo_w, new_logo_h), Image.Resampling.LANCZOS)
                
                # Position: Centered
                x = (width - new_logo_w) // 2
                y = (height - new_logo_h) // 2

                # Paste logo onto the watermark layer
                watermark_layer.paste(resized_logo, (x, y))

            else:
                # Apply text watermark
                # Font selection
                font_size = int(min(width, height) * 0.04) # 4% of smaller dimension
                font_size = max(font_size, 12)
                
                # Try to use a clean font, fallback to default
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

                # Calculate position
                try:
                    bbox = draw.textbbox((0, 0), text_watermark, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                except AttributeError:
                    text_w, text_h = draw.textsize(text_watermark, font=font)

                # Position: Centered
                x = (width - text_w) // 2
                y = (height - text_h) // 2

                # Draw text twice (semi-transparent white text, semi-transparent black shadow for visibility)
                shadow_offset = max(1, int(font_size * 0.05))
                draw.text((x + shadow_offset, y + shadow_offset), text_watermark, font=font, fill=(0, 0, 0, 128))
                draw.text((x, y), text_watermark, font=font, fill=(255, 255, 255, 180))

            # Merge watermark layer with background image
            final_img = Image.alpha_composite(working_img, watermark_layer)

            # 3. Convert back to RGB and save
            save_args = {}
            if preserve_exif and exif_bytes:
                save_args["exif"] = exif_bytes

            if output_filename.lower().endswith(('.jpg', '.jpeg')):
                save_args["quality"] = 90
                final_img.convert("RGB").save(output_path, "JPEG", **save_args)
            elif output_filename.lower().endswith('.webp'):
                save_args["quality"] = 90
                final_img.convert("RGB").save(output_path, "WEBP", **save_args)
            else:
                final_img.save(output_path, **save_args)

            print(f"Processed & Protected: {filename} -> {output_path}")
            processed_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\nSuccess! Processed {processed_count} image(s).")
    print(f"Protected images saved in: '{output_dir}'")
    if preserve_exif:
        print("EXIF metadata has been preserved in the output images.")
    else:
        print("All location data and EXIF metadata have been stripped.")

if __name__ == "__main__":
    try:
        process_images()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    # This prevents the .exe window from closing instantly
    input("\nProcessing complete. Press Enter to exit...")
