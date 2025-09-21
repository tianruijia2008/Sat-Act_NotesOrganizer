"""
Image information models for the SAT/Act Notes Organizer.
"""

from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime


@dataclass
class ImageQualityInfo:
    """Information about image quality for OCR."""
    grade: str
    quality_description: str
    overall_score: float
    metrics: dict[str, Any]


@dataclass
class ImageOrientationInfo:
    """Information about image orientation."""
    angle: float
    needs_rotation: bool
    recommended_rotation: float
    method: Optional[str] = None
