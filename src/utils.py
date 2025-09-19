import os
import json
from typing import Optional, Any


def load_config(config_path: Optional[str] = None) -> dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path (str): Path to the config file.
                          If None, looks for config.json in the current directory.

    Returns:
        dict[str, Any]: Configuration dictionary

    Raises:
        FileNotFoundError: If config file is not found
        json.JSONDecodeError: If config file is not valid JSON
    """
    if config_path is None:
        # Look for config.json in the current directory
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config

def get_provider_config(config: dict[str, Any], provider_name: str) -> Optional[dict[str, Any]]:
    """
    Get configuration for a specific provider.

    Args:
        config (dict[str, Any]): The full configuration dictionary
        provider_name (str): Name of the provider to look for

    Returns:
        Optional[dict[str, Any]]: Provider configuration or None if not found
    """
    providers = config.get('providers', [])
    for provider in providers:
        if provider.get('name') == provider_name:
            return provider
    return None

def get_model_config(config: dict[str, Any], model_name: str) -> Optional[dict[str, Any]]:
    """
    Get configuration for a specific model.

    Args:
        config (dict[str, Any]): The full configuration dictionary
        model_name (str): Name of the model to look for

    Returns:
        Optional[dict[str, Any]]: Model configuration or None if not found
    """
    providers = config.get('providers', [])
    for provider in providers:
        models = provider.get('models', [])
        if model_name in models:
            return provider
    return None

# Example usage
if __name__ == "__main__":
    try:
        config = load_config()
        print("Configuration loaded successfully:")
        print(json.dumps(config, indent=2))

        # Example: Get ModelScope provider config
        modelscope_config = get_provider_config(config, 'modelscope')
        if modelscope_config:
            print("\nModelScope provider config:")
            print(json.dumps(modelscope_config, indent=2))
    except Exception as e:
        print(f"Error loading configuration: {e}")
