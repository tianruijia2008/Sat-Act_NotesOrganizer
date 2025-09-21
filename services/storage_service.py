"""
Storage service for the SAT/ACT Notes Organizer.
"""

import os
import logging
import time
from typing import Any

from src.utils import get_resource_path, ensure_directory_exists
from data.models.note import ImageInfo

logger = logging.getLogger(__name__)


class StorageService:
    """Service for file storage and retrieval operations."""

    def __init__(self):
        """Initialize storage service."""
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.temp_dir: str = get_resource_path('data/temp')
        self.notes_dir: str = get_resource_path('data/notes')
        self.ensure_directories_exist()

    def ensure_directories_exist(self):
        """Ensure required directories exist."""
        ensure_directory_exists(self.temp_dir)
        ensure_directory_exists(self.notes_dir)

    def save_temp_image(self, uploaded_file: Any, original_name: str) -> ImageInfo:
        """
        Save an uploaded image to the temporary directory.

        Args:
            uploaded_file: Uploaded file object
            original_name: Original filename

        Returns:
            ImageInfo object
        """
        # Create unique filename to prevent overwriting
        filename_base, filename_ext = os.path.splitext(original_name)
        timestamp = int(time.time() * 1000) % 1000000
        unique_filename = f"{filename_base}_{timestamp}{filename_ext}"
        temp_path = os.path.join(self.temp_dir, unique_filename)

        # Reset file pointer and save
        uploaded_file.seek(0)
        with open(temp_path, 'wb') as f:
            _ = f.write(uploaded_file.read())

        return ImageInfo(
            name=unique_filename,
            original_name=original_name,
            path=temp_path
        )

    def get_temp_images(self) -> list[ImageInfo]:
        """
        Get all images in the temporary directory.

        Returns:
            List of ImageInfo objects
        """
        images: list[ImageInfo] = []
        if os.path.exists(self.temp_dir):
            for filename in os.listdir(self.temp_dir):
                if self._is_image_file(filename):
                    file_path = os.path.join(self.temp_dir, filename)
                    images.append(ImageInfo(
                        name=filename,
                        original_name=filename,
                        path=file_path
                    ))
        return images

    def delete_temp_image(self, image_name: str) -> bool:
        """
        Delete a temporary image.

        Args:
            image_name: Name of the image file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = os.path.join(self.temp_dir, image_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting temp image {image_name}: {e}")
            return False

    def clear_temp_directory(self) -> bool:
        """
        Clear all temporary images.

        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.temp_dir):
                for filename in os.listdir(self.temp_dir):
                    if self._is_image_file(filename):
                        file_path = os.path.join(self.temp_dir, filename)
                        os.remove(file_path)
            return True
        except Exception as e:
            self.logger.error(f"Error clearing temp directory: {e}")
            return False

    def get_notes_files(self) -> list[str]:
        """
        Get all note files.

        Returns:
            List of note file paths
        """
        notes = []
        if os.path.exists(self.notes_dir):
            for filename in os.listdir(self.notes_dir):
                if filename.endswith('.md'):
                    notes.append(os.path.join(self.notes_dir, filename))
        return notes

    def _is_image_file(self, filename: str) -> bool:
        """Check if a file is an image."""
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        _, ext = os.path.splitext(filename.lower())
        return ext in supported_extensions
