"""
Configuration management for the SAT/ACT Notes Organizer.
Handles loading and validation of application settings.
"""

import os
import json
from typing import Optional, Any


class Settings:
    """Application settings manager."""

    def __init__(self):
        """Initialize settings from config file or environment variables."""
        self._config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from config file or environment variables."""
        # Try to load from config.json first
        config_path = self._get_config_path()

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load config.json: {e}")

        # Fallback to environment variables
        return self._get_default_config()

    def _get_config_path(self) -> str:
        """Get path to configuration file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        return os.path.join(project_root, 'config.json')

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
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
                "enabled": False,
                "similarity_threshold": 0.8
            }
        }

    @property
    def providers(self) -> list[dict[str, Any]]:
        """Get AI providers configuration."""
        return self._config.get('providers', [])

    @property
    def ocr_settings(self) -> dict[str, Any]:
        """Get OCR settings."""
        return self._config.get('ocr', {})

    @property
    def vector_db_settings(self) -> dict[str, Any]:
        """Get vector database settings."""
        return self._config.get('vector_db', {})

    def get_provider_config(self, provider_name: str = 'modelscope') -> Optional[dict[str, Any]]:
        """Get configuration for a specific provider."""
        providers = self.providers
        for provider in providers:
            if provider.get('name') == provider_name:
                return provider
        return None


# Global settings instance
settings = Settings()
