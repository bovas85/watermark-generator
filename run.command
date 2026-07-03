#!/bin/bash
# Move to the directory where this script is located
cd "$(dirname "$0")"

echo "========================================="
echo "  IMAGE WATERMARK & RAW CONVERTER TOOL   "
echo "========================================="
echo "Initializing environment for macOS..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed!"
    echo "Please download and install Python from: https://www.python.org/downloads/"
    echo "Or run 'brew install python' if you use Homebrew."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check and install dependencies
echo "Checking dependencies..."
python3 -c "import PIL, rawpy, numpy" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Missing required libraries. Installing pillow, rawpy, numpy..."
    python3 -m pip install pillow rawpy numpy
    if [ $? -ne 0 ]; then
        echo "Automatic installation failed."
        echo "Please install manually by running: pip3 install pillow rawpy numpy"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "Dependencies installed successfully!"
    echo ""
fi

# Run the watermarking script
echo "Running application..."
python3 watermark_script.py "$@"
