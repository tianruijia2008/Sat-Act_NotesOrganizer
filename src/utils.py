import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to a resource relative to the project root.

    Args:
        relative_path: Path relative to project root (e.g., 'data/temp')

    Returns:
        Absolute path to the resource
    """
    # Get the project root directory (parent of src)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    # Join with the relative path
    resource_path = os.path.join(project_root, relative_path)

    # Create directory if it doesn't exist and it's a directory path
    if not os.path.exists(resource_path):
        # Check if this looks like a directory path (no extension or ends with /)
        if not os.path.splitext(relative_path)[1] or relative_path.endswith('/'):
            os.makedirs(resource_path, exist_ok=True)
        else:
            # Create parent directory for files
            parent_dir = os.path.dirname(resource_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

    return resource_path

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config file or environment variables.

    Returns:
        Configuration dictionary
    """
    logger = logging.getLogger(__name__)

    # Try to load from config.json first
    config_path = get_resource_path('config.json')

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("Configuration loaded from config.json")
            return config
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config.json: {e}")

    # Fallback to environment variables
    logger.info("Using environment variables for configuration")

    # Default configuration structure
    config = {
        "providers": [
            {
                "name": "modelscope",
                "base_url": os.getenv('AI_BASE_URL', 'https://api.modelscope.cn/v1/chat/completions'),
                "api_key": os.getenv('AI_API_KEY', ''),
                "models": [
                    os.getenv('AI_MODEL', 'qwen-turbo')
                ]
            }
        ],
        "ocr": {
            "provider": "tesseract",
            "confidence_threshold": 60
        },
        "vector_db": {
            "enabled": False,  # Disabled by default to avoid dependency issues
            "similarity_threshold": 0.8
        }
    }

    return config

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to directory
    """
    os.makedirs(directory_path, exist_ok=True)

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        File size in MB
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)
    return 0.0

def get_folder_size(folder_path: str) -> int:
    """
    Get total size of all files in a folder.

    Args:
        folder_path: Path to folder

    Returns:
        Total size in bytes
    """
    total_size = 0
    if os.path.exists(folder_path):
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    continue
    return total_size

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def validate_image_file(file_path: str) -> bool:
    """
    Validate if a file is a supported image format.

    Args:
        file_path: Path to image file

    Returns:
        True if valid image format
    """
    if not os.path.exists(file_path):
        return False

    supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    _, ext = os.path.splitext(file_path.lower())
    return ext in supported_extensions

def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing problematic characters.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    import re
    # Remove or replace problematic characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove any remaining non-printable characters
    safe_name = ''.join(char for char in safe_name if char.isprintable())
    # Limit length
    if len(safe_name) > 255:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:255-len(ext)] + ext

    return safe_name
