import json
import requests
import logging
from typing import Any, cast, Optional
import logging

from src.utils import load_config, get_provider_config
from src.vector_db import VectorDB

class AIProcessor:
    """
    AI Processor for interacting with ModelScope API to analyze SAT/ACT content.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize AI processor with configuration.

        Args:
            config_path (str | None): Path to the config file
        """
        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        # Ensure config_path is a string for load_config
        config_path_str = config_path if config_path is not None else ""
        self.config: dict[str, Any] = load_config(config_path_str)
        provider_config = get_provider_config(self.config, 'modelscope')
        if provider_config is None:
            raise ValueError("ModelScope provider configuration not found in config file")
        self.provider_config: dict[str, Any] = cast(dict[str, Any], provider_config)

        base_url = self.provider_config.get('base_url')
        api_key = self.provider_config.get('api_key')
        models = self.provider_config.get('models', [])

        if not isinstance(base_url, str) or not base_url:
            raise ValueError("base_url must be provided in ModelScope provider configuration")
        if not isinstance(api_key, str) or not api_key:
            raise ValueError("api_key must be provided in ModelScope provider configuration")
        if not isinstance(models, list) or not models or not isinstance(models[0], str):
            raise ValueError("At least one model must be specified in ModelScope provider configuration")

        self.base_url: str = base_url
        self.api_key: str = api_key
        self.model: str = models[0]

        # Initialize headers
        self.headers: dict[str, str] = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Initialize vector database with config
        self.vector_db = VectorDB(config=self.config)

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

    def send_test_request(self) -> Optional[dict[str, Any]]:
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

    def classify_content(self, ocr_text: str) -> dict[str, Any]:
        """
        Classify OCR extracted text as either a note or a wrong question.

        Args:
            ocr_text (str): Text extracted from an image using OCR

        Returns:
            Dict[str, Any]: Classification result with type and confidence
        """
        try:
            # Get similar documents from vector database for context
            similar_docs = self.vector_db.query_similar(ocr_text, top_k=3)

            # Prepare context from similar documents, distinguishing sources
            context_sections = []
            for i, doc in enumerate(similar_docs):
                # Determine source of the document
                source = doc["metadata"].get("source", "unknown")
                if source == "obsidian":
                    source_label = "Obsidian Note"
                    title = doc["metadata"].get("title", "Untitled")
                    context_sections.append(f"Context {i+1} (Source: {source_label}, Title: {title}): {doc['text'][:200]}...")
                else:
                    doc_type = doc["metadata"].get("type", "unknown")
                    doc_topic = doc["metadata"].get("topic", "unknown")
                    context_sections.append(f"Context {i+1} (Source: OCR, Type: {doc_type}, Topic: {doc_topic}): {doc['text'][:200]}...")

            context_str = "\n\n".join(context_sections) if context_sections else "No relevant context found."

            # Prepare the prompt for the AI model
            prompt = f"""
            Analyze the following text extracted from an image and classify it as either a \"note\" or a \"wrong question\".

            A \"note\" is educational content such as formulas, concepts, explanations, or study materials.
            A \"wrong question\" is a practice problem or test question that was answered incorrectly,
            typically with an explanation of the mistake and the correct approach.

            Relevant context from previous materials:
            {context_str}

            Text to analyze:
            {ocr_text}

            Respond in JSON format with the following structure:
            {{
                \"classification\": \"note\" or \"wrong_question\",
                \"confidence\": a number between 0 and 1,
                \"reasoning\": \"brief explanation of why this classification was chosen\",
                \"related_to_context\": \"brief explanation of how this content relates to the provided context (if applicable)\"
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

    def recommend_organization_strategy(self, content_items: list[tuple[str, dict[str, Any], str]]) -> dict[str, Any]:
        """
        First-stage AI analysis to recommend content organization strategy.

        Args:
            content_items (List[Tuple[str, Dict[str, Any], str]]): List of tuples containing
                (ocr_text, classification_result, image_filename)

        Returns:
            Dict[str, Any]: Organization strategy recommendation
        """
        try:
            # Get context from vector database about similar content
            all_ocr_texts = [item[0] for item in content_items]
            combined_text = " ".join(all_ocr_texts)
            similar_docs = self.vector_db.query_similar(combined_text, top_k=5)

            # Prepare context from similar documents, distinguishing sources
            context_sections = []
            for i, doc in enumerate(similar_docs):
                # Determine source of the document
                source = doc["metadata"].get("source", "unknown")
                if source == "obsidian":
                    source_label = "Obsidian Note"
                    title = doc["metadata"].get("title", "Untitled")
                    context_sections.append(f"Previous content {i+1} (Source: {source_label}, Title: {title}): {doc['text'][:200]}...")
                else:
                    doc_type = doc["metadata"].get("type", "unknown")
                    doc_topic = doc["metadata"].get("topic", "unknown")
                    context_sections.append(f"Previous content {i+1} (Source: OCR, Type: {doc_type}, Topic: {doc_topic}): {doc['text'][:200]}...")

            context_str = "\n\n".join(context_sections) if context_sections else "No relevant previous content found."

            # Prepare the prompt for the AI model
            content_descriptions = []
            for i, (ocr_text, classification, image_filename) in enumerate(content_items):
                char_count = len(ocr_text)
                content_type = classification.get('classification', 'unknown')
                confidence = classification.get('confidence', 0.0)

                content_descriptions.append(
                    f"Item {i+1} (File: {image_filename}, Type: {content_type}, "
                    f"Confidence: {confidence:.2f}, Characters: {char_count}): {ocr_text[:200]}..."
                )

            prompt = f"""
            Analyze the following SAT/ACT study materials and recommend the best organization strategy.
            You must decide whether to:
            1. Combine all items into a single comprehensive Markdown file
            2. Create separate files for each item
            3. Group related items into multiple files

            Consider these factors:
            - Content similarity and relationships
            - Character count (longer content may need separate files)
            - Content type (notes vs wrong questions)
            - Educational value of grouping vs separation
            - Relationship to previously processed content (provided below)

            Previously processed similar content:
            {context_str}

            Content items:
            {chr(10).join(content_descriptions)}

            Respond in JSON format with the following structure:
            {{
                "strategy": "combine_all" or "separate_all" or "group_related",
                "reasoning": "explanation of why this strategy was chosen",
                "groups": [
                    {{
                        "name": "descriptive name for this group",
                        "items": [list of item indices that belong together],
                        "rationale": "why these items should be grouped"
                    }}
                ],
                "recommendations": {{
                    "file_naming": "suggestion for file naming convention",
                    "content_structure": "suggestion for how to structure the content"
                }},
                "relationship_to_previous_content": "how the new content relates to previously processed content"
            }}

            Important rules:
            - If strategy is "combine_all", groups should contain all items in one group
            - If strategy is "separate_all", groups should contain one item each
            - If strategy is "group_related", groups should logically cluster related items
            - Always provide exactly one group if strategy is "combine_all"
            - Consider how the new content relates to previously processed content when making recommendations
            """

            # Prepare the payload for the API request
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 1500
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
                        recommendation = json.loads(content)
                        self.logger.info(f"Successfully generated organization strategy: {recommendation.get('strategy')}")
                        return recommendation
                    except json.JSONDecodeError:
                        # If JSON parsing fails, return a default response
                        self.logger.warning("Failed to parse JSON response from AI model for organization strategy")
                        return {
                            "strategy": "separate_all",
                            "reasoning": "Could not parse AI response, defaulting to separate files",
                            "groups": [{"name": f"Item {i+1}", "items": [i], "rationale": "Default separation"}
                                      for i in range(len(content_items))],
                            "recommendations": {
                                "file_naming": "individual_item_{index}",
                                "content_structure": "Separate files for each item"
                            }
                        }
                else:
                    self.logger.error("Unexpected response format from AI model for organization strategy")
                    return {
                        "strategy": "separate_all",
                        "reasoning": "Unexpected response format, defaulting to separate files",
                        "groups": [{"name": f"Item {i+1}", "items": [i], "rationale": "Default separation"}
                                  for i in range(len(content_items))],
                        "recommendations": {
                            "file_naming": "individual_item_{index}",
                            "content_structure": "Separate files for each item"
                        }
                    }
            else:
                self.logger.error(f"Failed to generate organization strategy. Status code: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return {
                    "strategy": "separate_all",
                    "reasoning": f"API request failed with status {response.status_code}, defaulting to separate files",
                    "groups": [{"name": f"Item {i+1}", "items": [i], "rationale": "Default separation"}
                              for i in range(len(content_items))],
                    "recommendations": {
                        "file_naming": "individual_item_{index}",
                        "content_structure": "Separate files for each item"
                    }
                }

        except Exception as e:
            self.logger.error(f"Error generating organization strategy: {str(e)}")
            return {
                "strategy": "separate_all",
                "reasoning": f"Exception occurred: {str(e)}, defaulting to separate files",
                "groups": [{"name": f"Item {i+1}", "items": [i], "rationale": "Default separation"}
                          for i in range(len(content_items))],
                "recommendations": {
                    "file_naming": "individual_item_{index}",
                    "content_structure": "Separate files for each item"
                }
            }

    def organize_content_batch(self, content_items: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
        """
        Organize a batch of content items (notes and wrong questions) into structured format.

        Args:
            content_items (List[Tuple[str, Dict[str, Any]]]): List of tuples containing (ocr_text, classification_result)

        Returns:
            Dict[str, Any]: Organized content with relationships identified
        """
        try:
            # Get context from vector database about similar content
            all_ocr_texts = [item[0] for item in content_items]
            combined_text = " ".join(all_ocr_texts)
            similar_docs = self.vector_db.query_similar(combined_text, top_k=5)

            # Prepare context from similar documents, distinguishing sources
            context_sections = []
            for i, doc in enumerate(similar_docs):
                # Determine source of the document
                source = doc["metadata"].get("source", "unknown")
                if source == "obsidian":
                    source_label = "Obsidian Note"
                    title = doc["metadata"].get("title", "Untitled")
                    context_sections.append(f"Previous content {i+1} (Source: {source_label}, Title: {title}): {doc['text'][:200]}...")
                else:
                    doc_type = doc["metadata"].get("type", "unknown")
                    doc_topic = doc["metadata"].get("topic", "unknown")
                    context_sections.append(f"Previous content {i+1} (Source: OCR, Type: {doc_type}, Topic: {doc_topic}): {doc['text'][:200]}...")

            context_str = "\n\n".join(context_sections) if context_sections else "No relevant previous content found."

            # Prepare the prompt for the AI model
            content_descriptions = []
            for i, (ocr_text, classification) in enumerate(content_items):
                content_descriptions.append(
                    f"Item {i+1} (Type: {classification.get('classification', 'unknown')}): {ocr_text[:200]}..."
                )

            prompt = f"""
            Organize the following SAT/ACT study materials into a structured format suitable for Obsidian notes.
            Identify relationships between notes and wrong questions, such as which notes relate to which wrong questions.
            Also consider how this content relates to previously processed content provided below.

            Previously processed similar content:
            {context_str}

            Content items:
            {chr(10).join(content_descriptions)}

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
                "relationships": "description of how the items relate to each other",
                "relationship_to_previous_content": "how this content relates to previously processed content"
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

    def organize_content_by_groups(self, content_items: list[tuple[str, dict[str, Any], str]],
                                 groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Second-stage AI processing to organize content according to recommended groups.

        Args:
            content_items (List[Tuple[str, Dict[str, Any], str]]): List of tuples containing
                (ocr_text, classification_result, image_filename)
            groups (List[Dict[str, Any]]): Group definitions from recommendation

        Returns:
            List[Dict[str, Any]]: List of organized content for each group
        """
        organized_groups = []

        try:
            for group in groups:
                group_name = group.get('name', 'Unnamed Group')
                item_indices = group.get('items', [])

                # Extract content items for this group
                group_content_items = [content_items[i] for i in item_indices if i < len(content_items)]

                # Convert to the format expected by organize_content_batch
                batch_items = [(item[0], item[1]) for item in group_content_items]

                # Organize the content in this group
                organized_content = self.organize_content_batch(batch_items)
                organized_content['group_name'] = group_name
                organized_content['group_rationale'] = group.get('rationale', '')
                organized_content['item_indices'] = item_indices
                organized_content['source_files'] = [content_items[i][2] for i in item_indices if i < len(content_items)]

                organized_groups.append(organized_content)

            self.logger.info(f"Successfully organized content into {len(organized_groups)} groups")
            return organized_groups

        except Exception as e:
            self.logger.error(f"Error organizing content by groups: {str(e)}")
            # Fallback: organize each item separately
            fallback_groups = []
            for i, (ocr_text, classification, image_filename) in enumerate(content_items):
                batch_items = [(ocr_text, classification)]
                organized_content = self.organize_content_batch(batch_items)
                organized_content['group_name'] = f"Item {i+1}: {image_filename}"
                organized_content['group_rationale'] = "Fallback organization - individual item"
                organized_content['item_indices'] = [i]
                organized_content['source_files'] = [image_filename]
                fallback_groups.append(organized_content)

            return fallback_groups
