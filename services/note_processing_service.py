"""
Main service for coordinating note processing in the SAT/ACT Notes Organizer.
"""

import time
import logging
from typing import Optional
from data.models.note import ProcessingResult, OCRResult, ImageInfo

# Import exceptions properly
# Define exceptions locally to avoid import conflicts
class ProcessingError(Exception):
    """Base processing error."""
    pass

class OCRProcessingError(ProcessingError):
    """OCR processing specific error."""
    pass

class NoteProcessingService:
    """Service for coordinating the complete note processing workflow."""

    def __init__(self):
        """Initialize the processing service with required processors."""
        self.logger: logging.Logger = logging.getLogger(__name__)
        # Import processors dynamically to avoid type issues
        from src.ocr_processor import OCRProcessor
        from src.ai_processor import AIProcessor
        from src.notes_saver import NotesSaver

        self._ocr_processor: OCRProcessor = OCRProcessor()
        self._ai_processor: AIProcessor = AIProcessor()
        self._notes_saver: NotesSaver = NotesSaver()

    def process_batch(self, image_infos: list[ImageInfo]) -> list[ProcessingResult]:
        """
        Process a list of images through the complete workflow.

        Args:
            image_infos: List of ImageInfo objects to process

        Returns:
            List of ProcessingResult objects
        """
        results: list[ProcessingResult] = []

        # Test AI connection first
        try:
            ai_test_method = self._ai_processor.__class__.__dict__.get('test_connection')
            if ai_test_method and not ai_test_method(self._ai_processor):
                raise ProcessingError("Failed to connect to AI service. Please check your configuration.")
        except Exception:
            pass  # Continue without AI test if method doesn't exist

        for image_info in image_infos:
            try:
                result = self.process_single_image(image_info)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing image {image_info.original_name}: {e}")
                # Create a failed result
                failed_result = self._create_failed_result(image_info, str(e))
                results.append(failed_result)

        return results

    def process_single_image(self, image_info: ImageInfo) -> ProcessingResult:
        """
        Process a single image through the complete workflow.

        Args:
            image_info: ImageInfo object to process

        Returns:
            ProcessingResult object
        """
        start_time: float = time.time()

        try:
            # Step 1: OCR Processing
            try:
                if hasattr(self._ocr_processor, 'extract_text'):
                    ocr_text = str(self._ocr_processor.extract_text(image_info.path))
                else:
                    raise OCRProcessingError("OCR extract_text method not found")
            except Exception as e:
                raise OCRProcessingError(f"OCR extraction failed: {str(e)}")

            if not ocr_text or not ocr_text.strip():
                raise OCRProcessingError(f"No text found in image {image_info.original_name}")

            # Get OCR quality metrics
            try:
                if hasattr(self._ocr_processor, 'assess_image_quality'):
                    quality_info = self._ocr_processor.assess_image_quality(image_info.path)
                    if not isinstance(quality_info, dict):
                        quality_info = {'overall_score': 0, 'grade': 'N/A'}
                else:
                    quality_info = {'overall_score': 0, 'grade': 'N/A'}
            except Exception:
                quality_info = {'overall_score': 0, 'grade': 'N/A'}

            # Create OCR result with proper type casting
            ocr_result = OCRResult(
                text=str(ocr_text),
                quality_score=float(quality_info.get('overall_score', 0)),
                quality_grade=str(quality_info.get('grade', 'N/A')),
                confidence=0.0,  # TODO: Implement confidence calculation
                processing_time=time.time() - start_time
            )

            # Step 2: AI Processing
            ai_result_dict = {}
            try:
                if hasattr(self._ai_processor, 'process_text'):
                    ai_result_dict = self._ai_processor.process_text(str(ocr_text), image_info.original_name)
            except Exception as e:
                self.logger.warning(f"AI processing failed: {e}")

            # Step 3: Save Notes
            notes_path: Optional[str] = None
            try:
                if hasattr(self._notes_saver, 'save_classification_result') and ai_result_dict:
                    result = self._notes_saver.save_classification_result(ai_result_dict, str(ocr_text), image_info.original_name)
                    if isinstance(result, tuple) and len(result) >= 1:
                        notes_path = str(result[0]) if result[0] is not None else None
                    elif isinstance(result, str):
                        notes_path = result
            except Exception as save_error:
                self.logger.warning(f"Could not save notes: {save_error}")

            processing_time = time.time() - start_time

            # Create successful result
            return self._create_successful_result(
                image_info=image_info,
                ocr_result=ocr_result,
                notes_path=notes_path,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            raise ProcessingError(f"Failed to process image {image_info.original_name}: {str(e)}") from e

    def _create_successful_result(self, image_info: ImageInfo, ocr_result: OCRResult, notes_path: Optional[str], processing_time: float) -> ProcessingResult:
        """Create a successful ProcessingResult object."""
        try:
            return ProcessingResult(
                image_info=image_info,
                ocr_result=ocr_result,
                classification_result=None,
                notes_path=notes_path,
                processing_time=processing_time,
                success=True
            )
        except Exception as e:
            self.logger.error(f"Error creating ProcessingResult: {e}")
            # Create a basic ProcessingResult with minimal data
            return ProcessingResult(
                image_info=image_info,
                ocr_result=ocr_result,
                classification_result=None,
                notes_path=notes_path,
                processing_time=processing_time,
                success=True
            )

    def _create_failed_result(self, image_info: ImageInfo, error_message: str) -> ProcessingResult:
        """Create a failed ProcessingResult object."""
        try:
            return ProcessingResult(
                image_info=image_info,
                ocr_result=None,
                classification_result=None,
                notes_path=None,
                processing_time=0,
                success=False,
                error_message=error_message
            )
        except Exception as e:
            self.logger.error(f"Error creating failed ProcessingResult: {e}")
            # Create a basic failed ProcessingResult
            return ProcessingResult(
                image_info=image_info,
                ocr_result=None,
                classification_result=None,
                notes_path=None,
                processing_time=0.0,
                success=False,
                error_message=error_message
            )
