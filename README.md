# Image Watermark & RAW Converter Tool

A lightweight, local desktop application designed for photographers and content creators. It automates image watermarking, converts professional camera RAW files (Sony, Canon, Nikon, etc.) into web-ready JPEGs, and strips all privacy-compromising EXIF metadata (GPS coordinates, camera models, dates) in one simple step.

## Features

- 📸 **RAW Camera Support:** Automatically develops and converts raw formats like Sony (`.ARW`), Canon (`.CR2`, `.CR3`), Nikon (`.NEF`), and Adobe (`.DNG`) into high-quality JPEGs.
- 🔀 **Dual Execution Modes:**
  - **Drag & Drop:** Drag files or folders directly onto the `.exe` to process them instantly.
  - **Batch Processing:** Scan and process all images inside the `raw_photos` folder at once.
- 🎯 **Centered Watermarking:** Automatically centers either your image logo (`my_logo.png`) or custom watermark text (e.g. `@MyBrand`) on any target photo.
- 🕵️ **Privacy Stripping:** Automatically removes all EXIF, GPS location tags, camera metadata, and device info during export to ensure your files are completely safe for the web.
- 🔄 **Orientation Correction:** Automatically respects EXIF orientation so vertical/portrait shots do not end up rotated sideways.

---

## Folder Structure

```text
Watermark Generator/
├── watermark_script.exe  # The compiled Windows application
├── watermark_script.py   # The open-source Python source code
├── README.md             # This instruction documentation
├── .gitignore            # Tells git which files to ignore
├── raw_photos/           # Folder for your raw inputs (for batch mode)
└── watermarked_photos/   # Folder where final, protected images are saved
```

---

## How to Use

### Method A: Drag & Drop (Quickest)
1. Select one or more photos (or a whole folder of photos) on your computer.
2. Drag and drop them directly onto `watermark_script.exe`.
3. The processed and watermarked images will be saved in the `watermarked_photos` directory.

### Method B: Batch Processing
1. Place all your original images inside the `raw_photos` folder.
2. Double-click `watermark_script.exe`.
3. The tool will process everything and output the results in the `watermarked_photos` folder.

---

## Watermark Customization

- **Image Logo:** Place a PNG image named `my_logo.png` next to the executable. The program will scale and overlay this image.
- **Text Logo:** If `my_logo.png` is not found, the tool will open a command window prompting you to enter custom text (e.g., `@MyBrand`). Pressing Enter without input will default the watermark to `© PROTECTED`.

---

## Running from Source (Python)

If you wish to run or modify the Python script directly, install the dependencies and run it:

```bash
# Install dependencies
pip install pillow rawpy numpy pyinstaller

# Run the script
python watermark_script.py

# Build your own executable
python -m PyInstaller --onefile watermark_script.py
```

## License

This project is open-source and available under the [MIT License](LICENSE).
