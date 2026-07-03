# Image Watermark & RAW Converter Tool

A lightweight, local desktop application designed for photographers and content creators. It automates image watermarking, converts professional camera RAW files (Sony, Canon, Nikon, etc.) into web-ready JPEGs, and strips all privacy-compromising EXIF metadata (GPS coordinates, camera models, dates) in one simple step.

---

## Features

- 📸 **RAW Camera Support:** Automatically develops and converts raw formats like Sony (`.ARW`), Canon (`.CR2`, `.CR3`), Nikon (`.NEF`), and Adobe (`.DNG`) into high-quality JPEGs.
- 🔀 **Dual Execution Modes:**
  - **Drag & Drop:** Drag files or folders directly onto the application launcher to process them instantly.
  - **Batch Processing:** Scan and process all images inside the `raw_photos` folder at once.
- 🎯 **Centered Watermarking:** Automatically centers either your image logo (`my_logo.png`) or custom watermark text (e.g. `@MyBrand`) on any target photo.
- 🕵️ **Privacy Stripping:** Automatically removes all EXIF, GPS location tags, camera metadata, and device info during export to ensure your files are completely safe for the web.
- 🔄 **Orientation Correction:** Automatically respects EXIF orientation so vertical/portrait shots do not end up rotated sideways.

---

## Folder Structure

```text
Watermark Generator/
├── watermark_script.exe   # Windows compiled executable
├── run.command            # macOS double-click launcher
├── watermark_script.py    # The open-source Python source code
├── README.md              # This instruction documentation
├── .gitignore             # Git settings to keep assets/photos private
├── raw_photos/            # Folder for raw inputs (for batch mode)
└── watermarked_photos/    # Folder where final, protected images are saved
```

---

## Installation & Download

To get started, **both Windows and macOS users should download the full repository folder** to ensure you have the complete file structure (including the `raw_photos` and `watermarked_photos` directories):

### Step 1: Download the Project Folder
* **Option A (ZIP file):** Click the green **Code** button at the top of this GitHub page, select **Download ZIP**, and extract the ZIP file onto your computer (e.g., your Desktop).
* **Option B (Git):** Clone this repository using Git:
  ```bash
  git clone https://github.com/bovas85/watermark-generator.git
  ```

### Step 2: Setup the Executable/Launcher

#### For Windows Users
1. Go to the **Releases** section on the right-hand side of this GitHub repository page.
2. Download the latest `watermark_script.exe`.
3. Move `watermark_script.exe` into the extracted project folder, placing it directly next to the `raw_photos` and `watermarked_photos` folders.

#### For macOS Users
You do not need to download any separate executable. The launcher is already included in your downloaded folder as `run.command` (see the macOS instructions below).

---

## How to Use

### 💻 For Windows Users

#### Method A: Drag & Drop (Quickest)
1. Select one or more photos (or a whole folder of photos) on your computer.
2. Drag and drop them directly onto `watermark_script.exe`.
3. The processed and watermarked JPEGs will appear in the `watermarked_photos` folder.

#### Method B: Batch Processing
1. Place all your original images inside the `raw_photos` folder.
2. Double-click `watermark_script.exe`.
3. The tool will process everything and output the results in the `watermarked_photos` folder.

---

### 🍎 For macOS Users

To support macOS without pre-compiled binaries, we provide a double-clickable launcher script named `run.command`.

#### First-time setup (required by macOS security):
1. Open the macOS **Terminal** app.
2. Type `chmod +x ` (make sure to include a trailing space).
3. Drag the `run.command` file from Finder into the Terminal window (this automatically inputs the path) and press **Enter**.
*(This grants macOS permission to execute the launcher script).*

#### Method A: Drag & Drop
1. Open a Terminal window.
2. Drag `run.command` into the Terminal, press space, and then drag the photo files you wish to watermark into the terminal window. Press **Enter**.
3. Processed JPEGs will appear in the `watermarked_photos` folder.

#### Method B: Batch Processing
1. Place your photos inside the `raw_photos` folder.
2. Double-click the `run.command` file in Finder.
3. The launcher will automatically detect your Python environment, install any missing dependencies (`pillow`, `rawpy`, `numpy`), process your images, and save them to `watermarked_photos`.

---

## Watermark Customization & Logo Guidelines

You can watermark your images using an image logo or custom text:

### 1. Image Logo (Recommended)
Place a PNG image named exactly `my_logo.png` next to the executable/launcher. The script will automatically detect it and overlay it.

#### 💡 Suggested Logo Specifications:
* **Format:** Use `.png` with a transparent background. Avoid JPEG logos as they will overlay a solid white or black background box.
* **Resolution (High-Res is Best):** We recommend a logo resolution of at least **1500px to 3000px wide**. 
  * *Why?* The script automatically scales the logo down to **20%** of the target photo's width. If you feed the script a low-resolution logo (e.g. 200px wide) and process a high-resolution 24MP or 50MP raw camera photo (which can be 6000px to 8000px wide), the script would have to stretch your logo, making it look blurry and pixelated. High-resolution PNGs scale down beautifully without losing quality.

### 2. Text Logo (Default)
If the tool doesn't find `my_logo.png`, it will prompt you in the console to enter custom text (e.g., `@MyBrand`). Pressing **Enter** without input will default the watermark to `© PROTECTED`.

---

## Compiling Your Own Native App

If you want to bundle the script into a native single-file executable for your specific operating system (e.g., a native macOS `.app` bundle or Mac binary), run the following:

```bash
# Install PyInstaller
pip install pyinstaller

# Build target binary
python -m PyInstaller --onefile watermark_script.py
```
After building, look in the newly created `dist/` directory for your compiled binary.

---

## License

This project is open-source and available under the [MIT License](LICENSE).
