"""
Data models for the SAT/ACT Notes Organizer.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ImageInfo:
    """Information about an uploaded image."""
    name: str
    original_name: str
    path: str
    upload_time: datetime = field(default_factory=datetime.now)


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    quality_score: float
    quality_grade: str
    confidence: float
    processing_time: float


@dataclass
class ClassificationResult:
    """Result from AI classification."""
    subject: str
    content_type: str
    confidence: float
    key_concepts: list[str]
    notes: str
    summary: str
    source_image: str


@dataclass
class ProcessingResult:
    """Complete result from processing an image."""
    image_info: ImageInfo
    ocr_result: Optional[OCRResult]
    classification_result: Optional[ClassificationResult]
    notes_path: Optional[str]
    processing_time: float
    success: bool
    error_message: Optional[str] = None
