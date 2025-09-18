#!/usr/bin/env python3
"""
Test script for OCR processor functionality.
"""

import os
import sys
import logging

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ocr_processor import OCRProcessor

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize OCR processor
    ocr_processor = OCRProcessor()

    print("OCR Processor Test")
    print("==================")

    # Test with a sample image if available
    # You can add your test images to the data/raw directory
    raw_data_dir = os.path.join("data", "raw")

    if os.path.exists(raw_data_dir):
        image_files = [f for f in os.listdir(raw_data_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))]

        if image_files:
            print(f"Found {len(image_files)} image(s) in {raw_data_dir}:")
            for image_file in image_files:
                image_path = os.path.join(raw_data_dir, image_file)
                print(f"\nProcessing: {image_file}")

                try:
                    # Extract text from image
                    text = ocr_processor.extract_text(image_path)
                    print(f"Extracted text:\n{text}\n")

                    # Extract detailed data
                    data = ocr_processor.extract_data(image_path)
                    text_elements = data.get('text', [])
                    if not isinstance(text_elements, (list, tuple)):
                        text_elements = []
                    print(f"Extracted {len(text_elements)} text elements")

                except Exception as e:
                    print(f"Error processing {image_file}: {str(e)}")
        else:
            print(f"No image files found in {raw_data_dir}")
            print("Add some images to test the OCR functionality.")
    else:
        print(f"Directory {raw_data_dir} does not exist")
        print("Please create the directory and add some images to test.")

if __name__ == "__main__":
    main()
