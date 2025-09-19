import pytesseract
from PIL import Image
import cv2
import numpy as np
import os
from typing import Optional, Dict, Any
import logging

# Import VectorDB
from src.vector_db import VectorDB

class OCRProcessor:
    """
    OCR Processor for extracting text from images using pytesseract.
    Designed for SAT/ACT notes and question images.
    """

    def __init__(self, config: Optional[dict[str, object]] = None):
        """
        Initialize OCR processor with optional configuration.

        Args:
            config (dict[str, object], optional): Configuration dictionary
        """
        self.config: dict[str, object] = config or {}

        # Initialize VectorDB
        vector_db_path_obj = self.config.get('vector_db_path', 'data/vector_db')
        vector_db_path = str(vector_db_path_obj) if vector_db_path_obj is not None else 'data/vector_db'
        self.vector_db: VectorDB = VectorDB(storage_path=vector_db_path, config=config)
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.tesseract_config: str = str(self.config.get('tesseract_config', '--psm 6'))

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

    def extract_text(self, image_path: str, preprocess: bool = True) -> tuple[str, str]:
        """
        Extract text from an image using OCR.

        Args:
            image_path (str): Path to the image file
            preprocess (bool): Whether to preprocess the image

        Returns:
            tuple[str, str]: Extracted text and document ID from the vector database

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
            custom_config = self.tesseract_config
            text = pytesseract.image_to_string(image, config=custom_config)

            # Clean up extracted text
            text = text.strip()

            # Store extracted text in vector database
            image_filename = os.path.basename(image_path)
            metadata = {
                "source": "ocr",
                "source_image": image_filename,
                "image_path": image_path,
                "processed": True,
                "extraction_method": "tesseract"
            }

            doc_id = self.vector_db.add_document(text, metadata)
            self.logger.info(f"Stored extracted text in vector database with doc_id: {doc_id}")

            self.logger.info(f"Successfully extracted text from {image_path}")
            return text, doc_id

        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error extracting text from {image_path}: {str(e)}")
            raise

    def update_document_metadata(self, doc_id: str, classification_result: Dict[str, Any]) -> bool:
        """
        Update document metadata with classification results.

        Args:
            doc_id (str): Document ID to update
            classification_result (Dict[str, Any]): Classification result from AI processor

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Prepare updated metadata
            metadata = {
                "type": classification_result.get("classification", "unknown"),
                "confidence": classification_result.get("confidence", 0.0),
                "topic": "math"  # Default topic, could be enhanced with more AI processing
            }

            # Update document in vector database
            success = self.vector_db.update_document(doc_id, "", metadata)
            if success:
                self.logger.info(f"Updated document {doc_id} with classification metadata")
            else:
                self.logger.warning(f"Failed to update document {doc_id} with classification metadata")
            return success

        except Exception as e:
            self.logger.error(f"Error updating document {doc_id} metadata: {str(e)}")
            return False

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
                data: dict[str, object] = data_result
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
