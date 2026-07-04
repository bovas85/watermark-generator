import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from PIL import Image

# Ensure the root directory is in sys.path so we can import watermark_script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import watermark_script

class TestWatermarkGenerator(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for sandboxed file operations
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_dir = self.test_dir.name
        
        # Paths to resource files
        self.resource_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))
        self.test_image_src = os.path.join(self.resource_dir, "test-image.png")
        self.test_raw_src = os.path.join(self.resource_dir, "test-raw.ARW")

        # Set up a sandbox directory structure mimicking the project structure
        self.sandbox_raw_dir = os.path.join(self.base_dir, "raw_photos")
        self.sandbox_output_dir = os.path.join(self.base_dir, "watermarked_photos")
        os.makedirs(self.sandbox_raw_dir, exist_ok=True)
        
        # Patch get_base_dir to return our temporary base directory
        self.get_base_dir_patcher = patch("watermark_script.get_base_dir", return_value=self.base_dir)
        self.mock_get_base_dir = self.get_base_dir_patcher.start()

    def tearDown(self):
        # Stop base dir patcher and clean up temp files
        self.get_base_dir_patcher.stop()
        self.test_dir.cleanup()

    def test_apply_watermark_text(self):
        """Test the core apply_watermark function with a text watermark."""
        img = Image.new("RGB", (400, 300), color="blue")
        watermarked = watermark_script.apply_watermark(img, text="Hello World")
        self.assertEqual(watermarked.mode, "RGBA")
        self.assertEqual(watermarked.size, (400, 300))

    def test_apply_watermark_logo(self):
        """Test apply_watermark function with a logo image (checks aspect ratio safety)."""
        img = Image.new("RGB", (1000, 500), color="green")
        logo = Image.new("RGBA", (200, 100), color="white")  # 2:1 aspect ratio
        watermarked = watermark_script.apply_watermark(img, logo=logo)
        self.assertEqual(watermarked.mode, "RGBA")

    @patch("sys.argv", ["watermark_script.py", "--no-interactive", "--text", "@test watermark"])
    def test_cli_non_interactive(self):
        """Test running the CLI non-interactively with a text watermark on test-image.png."""
        # Copy test-image.png to sandbox raw_photos
        shutil.copy2(self.test_image_src, self.sandbox_raw_dir)
        
        config = watermark_script.build_config()
        self.assertFalse(config.interactive)
        self.assertEqual(config.text, "@test watermark")
        
        watermark_script.process_images(config)
        
        # Verify output exists
        output_file = os.path.join(self.sandbox_output_dir, "test-image.png")
        self.assertTrue(os.path.exists(output_file))
        
        # Verify it has correct dimensions matching the source and can be opened
        with Image.open(self.test_image_src) as src_img:
            expected_size = src_img.size
            
        with Image.open(output_file) as out_img:
            self.assertEqual(out_img.size, expected_size)

    @patch("sys.argv", ["watermark_script.py"])
    @patch("builtins.input")
    def test_cli_interactive_text_no_logo(self, mock_input):
        """Test interactive mode without a logo, entering custom text and stripping EXIF."""
        # Setup inputs: 
        # 1. Text watermark: "@test watermark"
        # 2. Preserve EXIF: "n"
        mock_input.side_effect = ["@test watermark", "n"]
        
        # Copy test-image.png to sandbox raw_photos
        shutil.copy2(self.test_image_src, self.sandbox_raw_dir)
        
        config = watermark_script.build_config()
        self.assertTrue(config.interactive)
        
        watermark_script.process_images(config)
        
        output_file = os.path.join(self.sandbox_output_dir, "test-image.png")
        self.assertTrue(os.path.exists(output_file))
        
        with Image.open(self.test_image_src) as src_img:
            expected_size = src_img.size
            
        with Image.open(output_file) as out_img:
            self.assertEqual(out_img.size, expected_size)
        
        mock_input.assert_any_call("Enter text watermark (or Enter for '© PROTECTED'): ")
        mock_input.assert_any_call("\nPreserve EXIF metadata (GPS location, camera details, settings) in output JPEGs? (y/N): ")

    @patch("sys.argv", ["watermark_script.py"])
    @patch("builtins.input")
    def test_cli_interactive_raw(self, mock_input):
        """Test interactive mode with a RAW file (test-raw.ARW), checking raw development and text watermark."""
        if watermark_script.rawpy is None:
            self.skipTest("rawpy library is not available, skipping RAW processing test.")

        # Setup inputs:
        # 1. Text watermark: "@test watermark"
        # 2. Preserve EXIF: "y"
        mock_input.side_effect = ["@test watermark", "y"]
        
        # Copy test-raw.ARW to sandbox raw_photos
        shutil.copy2(self.test_raw_src, self.sandbox_raw_dir)
        
        config = watermark_script.build_config()
        watermark_script.process_images(config)
        
        # The output format for raw images is converted to .jpg
        output_file = os.path.join(self.sandbox_output_dir, "test-raw.jpg")
        self.assertTrue(os.path.exists(output_file))
        
        # Verify it can be opened
        with Image.open(output_file) as out_img:
            self.assertIsNotNone(out_img)

    @patch("sys.argv", ["watermark_script.py", "--no-interactive", "--strip-exif"])
    def test_exif_stripping(self):
        """Test that EXIF metadata is completely stripped for privacy."""
        shutil.copy2(self.test_image_src, self.sandbox_raw_dir)
        
        config = watermark_script.build_config()
        watermark_script.process_images(config)
        
        output_file = os.path.join(self.sandbox_output_dir, "test-image.png")
        self.assertTrue(os.path.exists(output_file))
        with Image.open(output_file) as out_img:
            # PNG/JPEG info dict should not contain EXIF data
            self.assertIsNone(out_img.info.get("exif"))

    def test_custom_output_directory(self):
        """Test that passing a custom output directory via --output is respected."""
        shutil.copy2(self.test_image_src, self.sandbox_raw_dir)
        
        custom_out_path = os.path.join(self.base_dir, "custom_out")
        
        with patch("sys.argv", ["watermark_script.py", "--no-interactive", "--output", custom_out_path]):
            config = watermark_script.build_config()
            self.assertEqual(config.output, custom_out_path)
            watermark_script.process_images(config)
            
        self.assertTrue(os.path.exists(custom_out_path))
        
        output_file = os.path.join(custom_out_path, "test-image.png")
        self.assertTrue(os.path.exists(output_file))

    @patch("sys.argv", ["watermark_script.py", "--no-interactive", "--workers", "2"])
    def test_parallel_workers_execution(self):
        """Test running with parallel workers configuration."""
        shutil.copy2(self.test_image_src, self.sandbox_raw_dir)
        
        config = watermark_script.build_config()
        self.assertEqual(config.workers, 2)
        
        # Should execute successfully without throwing errors
        watermark_script.process_images(config)
        
        output_file = os.path.join(self.sandbox_output_dir, "test-image.png")
        self.assertTrue(os.path.exists(output_file))

    @patch("sys.argv", ["watermark_script.py", "--no-interactive"])
    def test_invalid_file_skips_gracefully(self):
        """Test that invalid files are skipped gracefully and don't stop the overall run."""
        # Put a valid file and an invalid/corrupt text file in raw_photos
        shutil.copy2(self.test_image_src, self.sandbox_raw_dir)
        
        corrupt_file_path = os.path.join(self.sandbox_raw_dir, "corrupt_photo.jpg")
        with open(corrupt_file_path, "w") as f:
            f.write("This is not an image file.")
            
        config = watermark_script.build_config()
        # Should process the valid file and skip/log error for the invalid one without crashing
        watermark_script.process_images(config)
        
        # test-image should be successfully processed
        self.assertTrue(os.path.exists(os.path.join(self.sandbox_output_dir, "test-image.png")))
        # corrupt_photo should fail and not be in the output
        self.assertFalse(os.path.exists(os.path.join(self.sandbox_output_dir, "corrupt_photo.jpg")))

if __name__ == "__main__":
    unittest.main()
