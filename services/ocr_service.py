"""
OCR service for the SAT/ACT Notes Organizer.
"""

import logging
from data.models.image_info import ImageQualityInfo, ImageOrientationInfo

class OCRService:
    """Service for OCR-related operations."""

    def __init__(self):
        """Initialize the OCR service."""
        self.logger: logging.Logger = logging.getLogger(__name__)
        # Import OCR processor dynamically to avoid type issues
        from src.ocr_processor import OCRProcessor
        self._processor: OCRProcessor = OCRProcessor()

    def extract_text(self, image_path: str) -> str:
        """
        Extract text from an image.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text
        """
        try:
            # Use direct method call instead of dynamic calling
            if hasattr(self._processor, 'extract_text'):
                result = self._processor.extract_text(image_path)
                return str(result) if result is not None else ""
            else:
                self.logger.error("OCR processor missing extract_text method")
                return ""
        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            return ""

    def assess_image_quality(self, image_path: str) -> ImageQualityInfo:
        """
        Assess the quality of an image for OCR purposes.

        Args:
            image_path: Path to the image file

        Returns:
            ImageQualityInfo object
        """
        # Default values
        quality_data = {'grade': 'N/A', 'quality_description': 'Error', 'overall_score': 0, 'metrics': {}}

        try:
            # Use direct method call instead of dynamic calling
            if hasattr(self._processor, 'assess_image_quality'):
                result = self._processor.assess_image_quality(image_path)
                if isinstance(result, dict):
                    quality_data = result
            else:
                self.logger.error("OCR processor missing assess_image_quality method")
        except Exception as e:
            self.logger.error(f"Error assessing image quality: {e}")

        # Safe type conversion with fallbacks
        grade = quality_data.get('grade', 'N/A')
        description = quality_data.get('quality_description', '')
        score = quality_data.get('overall_score', 0)
        metrics = quality_data.get('metrics', {})

        return ImageQualityInfo(
            grade=str(grade) if grade is not None else 'N/A',
            quality_description=str(description) if description is not None else '',
            overall_score=float(score) if isinstance(score, (int, float, str)) and str(score).replace('.','').replace('-','').isdigit() else 0.0,
            metrics=dict(metrics) if isinstance(metrics, dict) else {}
        )

    def detect_orientation(self, image_path: str) -> ImageOrientationInfo:
        """
        Detect the orientation of an image.

        Args:
            image_path: Path to the image file

        Returns:
            ImageOrientationInfo object
        """
        # Default values
        orientation_data = {'angle': 0, 'needs_rotation': False, 'recommended_rotation': 0, 'method': None}

        try:
            # Use direct method call instead of dynamic calling
            if hasattr(self._processor, 'detect_orientation'):
                result = self._processor.detect_orientation(image_path)
                if isinstance(result, dict):
                    orientation_data = result
            else:
                self.logger.error("OCR processor missing detect_orientation method")
        except Exception as e:
            self.logger.error(f"Error detecting orientation: {e}")

        # Safe type conversion with fallbacks
        angle = orientation_data.get('angle', 0)
        needs_rotation = orientation_data.get('needs_rotation', False)
        recommended_rotation = orientation_data.get('recommended_rotation', 0)
        method = orientation_data.get('method')

        return ImageOrientationInfo(
            angle=float(angle) if isinstance(angle, (int, float)) else 0.0,
            needs_rotation=bool(needs_rotation),
            recommended_rotation=float(recommended_rotation) if isinstance(recommended_rotation, (int, float)) else 0.0,
            method=str(method) if method is not None else None
        )
