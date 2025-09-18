import json
import requests
import logging
from typing import Any, cast, Dict, List, Optional, Tuple

from src.utils import load_config, get_provider_config

class AIProcessor:
    """
    AI Processor for interacting with ModelScope API to analyze SAT/ACT content.
    """

    config: dict[str, Any]
    provider_config: dict[str, Any]
    base_url: str
    api_key: str
    model: str
    logger: logging.Logger
    headers: dict[str, str]

    def __init__(self, config_path: str | None = None):
        """
        Initialize AI processor with configuration.

        Args:
            config_path (str | None): Path to the config file
        """
        # Ensure config_path is a string for load_config
        config_path_str = config_path if config_path is not None else ""
        self.config = load_config(config_path_str)
        provider_config = get_provider_config(self.config, 'modelscope')
        if provider_config is None:
            raise ValueError("ModelScope provider configuration not found in config file")
        self.provider_config = cast(dict[str, Any], provider_config)

        base_url = self.provider_config.get('base_url')
        api_key = self.provider_config.get('api_key')
        models = self.provider_config.get('models', [])

        if not isinstance(base_url, str) or not base_url:
            raise ValueError("base_url must be provided in ModelScope provider configuration")
        if not isinstance(api_key, str) or not api_key:
            raise ValueError("api_key must be provided in ModelScope provider configuration")
        if not isinstance(models, list) or not models or not isinstance(models[0], str):
            raise ValueError("At least one model must be specified in ModelScope provider configuration")

        self.base_url = base_url
        self.api_key = api_key
        self.model = models[0]

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Set up headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def test_connection(self) -> bool:
        """
        Test connection to the ModelScope API.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Simple health check or model info request
            test_url = self.base_url.replace('/chat/completions', '/models') if '/chat/completions' in self.base_url else self.base_url

            response = requests.get(test_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                self.logger.info("Successfully connected to ModelScope API")
                return True
            else:
                self.logger.error(f"Failed to connect to ModelScope API. Status code: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Error testing connection to ModelScope API: {str(e)}")
            return False

    def verify_model_access(self) -> bool:
        """
        Verify that the configured model is accessible.

        Returns:
            bool: True if model is accessible, False otherwise
        """
        if not self.model:
            self.logger.error("No model specified in configuration")
            return False

        try:
            # For ModelScope, we can try to get model info
            model_url = f"{self.base_url.replace('/chat/completions', '')}/models/{self.model}"

            response = requests.get(model_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                self.logger.info(f"Successfully verified access to model: {self.model}")
                return True
            else:
                self.logger.error(f"Failed to verify model access. Status code: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Error verifying model access: {str(e)}")
            return False

    def send_test_request(self) -> dict[str, Any] | None:
        """
        Send a test request to the ModelScope API.

        Returns:
            dict[str, Any] | None: API response or None if failed
        """
        if not self.model:
            self.logger.error("No model specified in configuration")
            return None

        try:
            # Prepare a simple test message
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                "max_tokens": 50
            }

            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                self.logger.info("Successfully sent test request to ModelScope API")
                return result
            else:
                self.logger.error(f"Failed to send test request. Status code: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Error sending test request to ModelScope API: {str(e)}")
            return None

    def classify_content(self, ocr_text: str) -> Dict[str, Any]:
        """
        Classify OCR extracted text as either a note or a wrong question.

        Args:
            ocr_text (str): Text extracted from an image using OCR

        Returns:
            Dict[str, Any]: Classification result with type and confidence
        """
        try:
            # Prepare the prompt for the AI model
            prompt = f"""
            Analyze the following text extracted from an image and classify it as either a "note" or a "wrong question".

            A "note" is educational content such as formulas, concepts, explanations, or study materials.
            A "wrong question" is a practice problem or test question that was answered incorrectly,
            typically with an explanation of the mistake and the correct approach.

            Text to analyze:
            {ocr_text}

            Respond in JSON format with the following structure:
            {{
                "classification": "note" or "wrong_question",
                "confidence": a number between 0 and 1,
                "reasoning": "brief explanation of why this classification was chosen"
            }}
            """

            # Prepare the payload for the API request
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }

            # Send the request to the ModelScope API
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()

                # Extract the content from the response
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')

                    # Try to parse the JSON response
                    try:
                        classification_result = json.loads(content)
                        self.logger.info(f"Successfully classified content: {classification_result.get('classification')}")
                        return classification_result
                    except json.JSONDecodeError:
                        # If JSON parsing fails, return a default response
                        self.logger.warning("Failed to parse JSON response from AI model")
                        return {
                            "classification": "unknown",
                            "confidence": 0.0,
                            "reasoning": "Could not parse AI response"
                        }
                else:
                    self.logger.error("Unexpected response format from AI model")
                    return {
                        "classification": "unknown",
                        "confidence": 0.0,
                        "reasoning": "Unexpected response format"
                    }
            else:
                self.logger.error(f"Failed to classify content. Status code: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return {
                    "classification": "unknown",
                    "confidence": 0.0,
                    "reasoning": f"API request failed with status {response.status_code}"
                }

        except Exception as e:
            self.logger.error(f"Error classifying content: {str(e)}")
            return {
                "classification": "unknown",
                "confidence": 0.0,
                "reasoning": f"Exception occurred: {str(e)}"
            }

    def organize_content_batch(self, content_items: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Organize a batch of content items (notes and wrong questions) into structured format.

        Args:
            content_items (List[Tuple[str, Dict[str, Any]]]): List of tuples containing (ocr_text, classification_result)

        Returns:
            Dict[str, Any]: Organized content with relationships identified
        """
        try:
            # Prepare the prompt for the AI model
            content_descriptions = []
            for i, (ocr_text, classification) in enumerate(content_items):
                content_descriptions.append(
                    f"Item {i+1} (Type: {classification.get('classification', 'unknown')}): {ocr_text[:200]}..."
                )

            prompt = f"""
            Organize the following SAT/ACT study materials into a structured format suitable for Obsidian notes.
            Identify relationships between notes and wrong questions, such as which notes relate to which wrong questions.

            Content items:
            {'\n'.join(content_descriptions)}

            Respond in JSON format with the following structure:
            {{
                "summary": "overall summary of the content",
                "notes": [
                    {{
                        "content": "the note content",
                        "related_wrong_questions": [list of indices of related wrong questions]
                    }}
                ],
                "wrong_questions": [
                    {{
                        "content": "the wrong question content",
                        "related_notes": [list of indices of related notes],
                        "mistake_explanation": "explanation of the mistake",
                        "correct_approach": "correct approach to solve the problem"
                    }}
                ],
                "relationships": "description of how the items relate to each other"
            }}
            """

            # Prepare the payload for the API request
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 2000
            }

            # Send the request to the ModelScope API
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=120)

            if response.status_code == 200:
                result = response.json()

                # Extract the content from the response
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0].get('message', {}).get('content', '')

                    # Try to parse the JSON response
                    try:
                        organized_content = json.loads(content)
                        self.logger.info("Successfully organized content batch")
                        return organized_content
                    except json.JSONDecodeError:
                        # If JSON parsing fails, return a default response
                        self.logger.warning("Failed to parse JSON response from AI model for batch organization")
                        return {
                            "summary": "Failed to organize content",
                            "notes": [],
                            "wrong_questions": [],
                            "relationships": "Could not parse AI response"
                        }
                else:
                    self.logger.error("Unexpected response format from AI model for batch organization")
                    return {
                        "summary": "Failed to organize content",
                        "notes": [],
                        "wrong_questions": [],
                        "relationships": "Unexpected response format"
                    }
            else:
                self.logger.error(f"Failed to organize content batch. Status code: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return {
                    "summary": "Failed to organize content",
                    "notes": [],
                    "wrong_questions": [],
                    "relationships": f"API request failed with status {response.status_code}"
                }

        except Exception as e:
            self.logger.error(f"Error organizing content batch: {str(e)}")
            return {
                "summary": "Failed to organize content",
                "notes": [],
                "wrong_questions": [],
                "relationships": f"Exception occurred: {str(e)}"
            }

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Initialize AI processor
        ai_processor = AIProcessor()

        print("AI Processor Test")
        print("=================")
        print(f"Base URL: {ai_processor.base_url}")
        print(f"Model: {ai_processor.model}")

        # Test connection
        print("\n1. Testing connection...")
        connection_success = ai_processor.test_connection()
        print(f"Connection test: {'PASSED' if connection_success else 'FAILED'}")

        if connection_success:
            # Verify model access
            print("\n2. Verifying model access...")
            model_access = ai_processor.verify_model_access()
            print(f"Model access: {'PASSED' if model_access else 'FAILED'}")

            if model_access:
                # Send test request
                print("\n3. Sending test request...")
                test_result = ai_processor.send_test_request()
                if test_result:
                    print("Test request: PASSED")
                    print(f"Response: {json.dumps(test_result, indent=2)[:200]}...")
                else:
                    print("Test request: FAILED")

    except Exception as e:
        print(f"Error initializing AI processor: {str(e)}")