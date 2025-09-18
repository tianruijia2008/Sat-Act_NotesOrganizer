import pytesseract
from PIL import Image
import cv2
import numpy as np
import os
from typing import Optional, Dict, Any, cast
import logging

class OCRProcessor:
    """
    OCR Processor for extracting text from images using pytesseract.
    Designed for SAT/ACT notes and question images.
    """

    config: dict[str, object]
    tesseract_config: str
    logger: logging.Logger

    def __init__(self, config: dict[str, object] | None = None):
        """
        Initialize OCR processor with optional configuration.

        Args:
            config (dict[str, object], optional): Configuration dictionary
        """
        self.config = config or {}
        self.tesseract_config = str(self.config.get('tesseract_config', '--psm 6'))
        self.logger = logging.getLogger(__name__)

    def preprocess_image(self, image_path: str) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.

        Args:
            image_path (str): Path to the image file

        Returns:
            PIL.Image.Image: Preprocessed image

        Raises:
            FileNotFoundError: If image file is not found
            Exception: For other image processing errors
        """
        try:
            # Open image
            image = Image.open(image_path)

            # Convert to grayscale if not already
            if image.mode != 'L':
                image = image.convert('L')

            # Convert PIL image to OpenCV format for preprocessing
            opencv_image = np.array(image)

            # Apply threshold to get image with only black and white
            _, opencv_image = cv2.threshold(opencv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Convert back to PIL Image
            processed_image = Image.fromarray(opencv_image)

            return processed_image

        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error preprocessing image {image_path}: {str(e)}")
            raise

    def extract_text(self, image_path: str, preprocess: bool = True) -> str:
        """
        Extract text from an image using OCR.

        Args:
            image_path (str): Path to the image file
            preprocess (bool): Whether to preprocess the image

        Returns:
            str: Extracted text from the image

        Raises:
            FileNotFoundError: If image file is not found
            Exception: For OCR processing errors
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Preprocess image if requested
            if preprocess:
                image = self.preprocess_image(image_path)
            else:
                image = Image.open(image_path)

            # Perform OCR
            text_result = pytesseract.image_to_string(image, config=self.tesseract_config)  # type: ignore

            # pytesseract.image_to_string should return str, but type checkers may not know this
            if isinstance(text_result, str):
                text = text_result.strip()
            elif isinstance(text_result, bytes):
                text = text_result.decode(errors="replace").strip()
            else:
                # Unexpected type, fallback to str
                text = str(text_result).strip()

            self.logger.info(f"Successfully extracted text from {image_path}")
            return text

        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error extracting text from {image_path}: {str(e)}")
            raise

    def extract_data(self, image_path: str, preprocess: bool = True) -> dict[str, object]:
        """
        Extract detailed data from an image using OCR.

        Args:
            image_path (str): Path to the image file
            preprocess (bool): Whether to preprocess the image

        Returns:
            dict[str, object]: Detailed OCR data including text, boxes, etc.

        Raises:
            FileNotFoundError: If image file is not found
            Exception: For OCR processing errors
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Preprocess image if requested
            if preprocess:
                image = self.preprocess_image(image_path)
            else:
                image = Image.open(image_path)

            # Perform detailed OCR
            data_result = pytesseract.image_to_data(
                image, output_type=pytesseract.Output.DICT, config=self.tesseract_config  # type: ignore
            )

            # pytesseract.image_to_data should return dict, but type checkers may not know this
            if isinstance(data_result, dict):
                data = data_result
            else:
                # Unexpected type, fallback to empty dict
                data = {}

            self.logger.info(f"Successfully extracted data from {image_path}")
            return data

        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error extracting data from {image_path}: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize OCR processor
    ocr_processor = OCRProcessor()

    # Example: Process a sample image (if available)
    # text = ocr_processor.extract_text("path/to/sample/image.jpg")
    # print("Extracted text:", text)
