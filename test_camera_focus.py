#!/usr/bin/env python3
"""
Test script for camera focus detection and image enhancement.
This script helps verify that the camera utilities work correctly.
"""

import os
import sys
from PIL import Image
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from camera_utils import detect_text_focus_quality, enhance_image_for_text, auto_orient_image

def create_test_images():
    """Create test images with different focus levels"""
    # Create a sharp text image
    sharp_img = np.zeros((400, 600, 3), dtype=np.uint8)
    sharp_img.fill(255)  # White background

    # Add some text-like patterns (black rectangles)
    sharp_img[100:120, 50:550] = 0  # Horizontal line
    sharp_img[150:170, 50:550] = 0
    sharp_img[200:220, 50:550] = 0

    # Create a blurry version using simple averaging (without scipy)
    # Simple blur by averaging neighboring pixels
    blurry_img = np.copy(sharp_img)
    for i in range(1, sharp_img.shape[0]-1):
        for j in range(1, sharp_img.shape[1]-1):
            for k in range(3):  # RGB channels
                blurry_img[i, j, k] = np.mean(sharp_img[i-1:i+2, j-1:j+2, k])

    return Image.fromarray(sharp_img), Image.fromarray(blurry_img.astype(np.uint8))

def test_focus_detection():
    """Test the focus detection functionality"""
    print("Testing focus detection...")

    try:
        sharp_img, blurry_img = create_test_images()

        # Test sharp image
        sharp_result = detect_text_focus_quality(sharp_img)
        print(f"Sharp image - Quality: {sharp_result['quality']}, Score: {sharp_result['score']}, Variance: {sharp_result['variance']:.2f}")

        # Test blurry image
        blurry_result = detect_text_focus_quality(blurry_img)
        print(f"Blurry image - Quality: {blurry_result['quality']}, Score: {blurry_result['score']}, Variance: {blurry_result['variance']:.2f}")

        # Verify results
        if sharp_result['score'] > blurry_result['score']:
            print("✅ Focus detection working correctly!")
        else:
            print("❌ Focus detection may have issues")

    except Exception as e:
        print(f"❌ Focus detection test failed: {e}")

def test_image_enhancement():
    """Test image enhancement functionality"""
    print("\nTesting image enhancement...")

    try:
        # Create a test image
        test_img = np.random.randint(100, 200, (300, 400, 3), dtype=np.uint8)
        pil_img = Image.fromarray(test_img)

        # Enhance the image
        enhanced = enhance_image_for_text(pil_img)

        if enhanced and isinstance(enhanced, Image.Image):
            print("✅ Image enhancement working correctly!")
            print(f"Original size: {pil_img.size}, Enhanced size: {enhanced.size}")
        else:
            print("❌ Image enhancement failed")

    except Exception as e:
        print(f"❌ Image enhancement test failed: {e}")

def test_with_sample_image():
    """Test with a sample image if available"""
    print("\nTesting with sample images...")

    # Look for sample images in the data/raw directory
    raw_dir = os.path.join(os.path.dirname(__file__), 'data', 'raw')

    if os.path.exists(raw_dir):
        image_files = [f for f in os.listdir(raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if image_files:
            sample_file = os.path.join(raw_dir, image_files[0])
            try:
                sample_img = Image.open(sample_file)

                # Test focus detection
                focus_result = detect_text_focus_quality(sample_img)
                print(f"Sample image ({image_files[0]}):")
                print(f"  Quality: {focus_result['quality']}")
                print(f"  Score: {focus_result['score']}/4")
                print(f"  Variance: {focus_result['variance']:.2f}")

                # Test enhancement
                enhanced = enhance_image_for_text(sample_img)
                if enhanced:
                    print("  ✅ Successfully enhanced sample image")

            except Exception as e:
                print(f"  ❌ Error processing sample image: {e}")
        else:
            print("  No sample images found in data/raw/")
    else:
        print("  data/raw/ directory not found")

def main():
    print("Camera Focus Detection Test")
    print("=" * 30)

    # Check dependencies
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV not available")
        return

    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
    except ImportError:
        print("❌ NumPy not available")
        return

    print()

    # Run tests
    test_focus_detection()
    test_image_enhancement()
    test_with_sample_image()

    print("\n" + "=" * 30)
    print("Test completed!")

if __name__ == "__main__":
    main()
