"""
AI service for the SAT/ACT Notes Organizer.
"""

import logging
from typing import Any

from src.ai_processor import AIProcessor
from data.models.note import ClassificationResult

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-related operations."""

    def __init__(self):
        """Initialize the AI service."""
        self.processor: AIProcessor = AIProcessor()
        self.logger: logging.Logger = logging.getLogger(__name__)

    def test_connection(self) -> bool:
        """
        Test connection to the AI service.

        Returns:
            True if connection successful, False otherwise
        """
        return self.processor.test_connection()

    def process_text(self, text: str, image_name: str) -> ClassificationResult:
        """
        Process text with AI to generate classification and notes.

        Args:
            text: Text to process
            image_name: Name of the source image

        Returns:
            ClassificationResult object
        """
        result = self.processor.process_text(text, image_name)

        return ClassificationResult(
            subject=str(result.get('subject', 'general')),
            content_type=str(result.get('content_type', 'notes')),
            confidence=float(result.get('confidence', 0)),
            key_concepts=list(result.get('key_concepts', [])),
            notes=str(result.get('notes', '')),
            summary=str(result.get('summary', '')),
            source_image=str(result.get('source_image', image_name))
        )

    def classify_content(self, text: str) -> dict[str, Any]:
        """
        Legacy method for backward compatibility.

        Args:
            text: Text to classify

        Returns:
            Classification dictionary
        """
        return self.processor.classify_content(text)
