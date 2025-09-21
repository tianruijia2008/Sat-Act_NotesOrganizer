import json
import requests
import logging
import re
from typing import Any
import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils import load_config

class AIProcessor:
    """
    Simplified AI Processor for analyzing SAT/ACT study content.
    """

    def __init__(self):
        """Initialize AI processor with configuration."""
        self.logger = logging.getLogger(__name__)

        try:
            self.config = load_config()
            provider_config = self._get_provider_config()

            self.base_url = provider_config['base_url']
            self.api_key = provider_config['api_key']
            self.model = provider_config['models'][0]

        except Exception as e:
            self.logger.warning(f"Using fallback config due to error: {e}")
            # Fallback to environment variables
            self.base_url = os.getenv('AI_BASE_URL', 'https://api-inference.modelscope.cn/v1/chat/completions')
            self.api_key = os.getenv('AI_API_KEY', '')
            self.model = os.getenv('AI_MODEL', 'Qwen/Qwen3-235B-A22B-Thinking-2507')

        # Always set headers after config is determined
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _get_provider_config(self) -> Dict[str, Any]:
        """Get ModelScope provider configuration."""
        providers = self.config.get('providers', [])
        for provider in providers:
            if provider.get('name') == 'modelscope':
                return provider
        raise ValueError("ModelScope provider not found in configuration")

    def test_connection(self) -> bool:
        """Test connection to the AI API."""
        if not self.api_key or not self.base_url:
            self.logger.error("Missing API key or base URL")
            return False

        try:
            # Send a simple test request
            test_data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "max_tokens": 10
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=test_data,
                timeout=10
            )

            if response.status_code == 200:
                self.logger.info("AI API connection successful")
                return True
            else:
                self.logger.error(f"AI API test failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Error testing AI connection: {e}")
            return False

    def process_text(self, text: str, image_name: str) -> Dict[str, Any]:
        """
        Process extracted text and generate structured notes.

        Args:
            text: Extracted text from OCR
            image_name: Name of the source image

        Returns:
            Dict containing processed information
        """
        try:
            # Create prompt for content analysis
            prompt = self._create_analysis_prompt(text)

            # Send request to AI API
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert tutor analyzing SAT/ACT study materials. Provide structured, helpful analysis."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code}")

            result = response.json()
            content = result['choices'][0]['message']['content']

            # Parse the structured response
            return self._parse_ai_response(content, image_name)

        except Exception as e:
            self.logger.error(f"Error processing text: {e}")
            return self._create_fallback_response(text, image_name)

    def _create_analysis_prompt(self, text: str) -> str:
        """Create analysis prompt for the AI."""
        # Check if text appears corrupted or has OCR issues
        text_quality = self._assess_text_quality(text)

        if text_quality == "corrupted":
            return f"""
The following text appears to be corrupted OCR output from SAT/ACT study materials. Please analyze what you can extract:

CORRUPTED TEXT:
{text}

Please provide your analysis in the following JSON format, noting the OCR corruption:
{{
    "subject": "unknown|math|english|science|social_studies",
    "content_type": "corrupted_ocr|notes|practice_problem|wrong_answer_explanation|concept_summary",
    "confidence": 25,
    "key_concepts": ["any identifiable concepts"],
    "notes": "Based on the corrupted text, this appears to be [description]. Key readable elements include: [list any readable parts]. Recommend re-scanning with higher quality settings.",
    "summary": "OCR text is heavily corrupted but may contain [subject] content. Needs better image quality for proper analysis."
}}

Focus on extracting any meaningful content despite OCR errors and provide guidance for improvement.
"""
        else:
            return f"""
Analyze the following SAT/ACT study material text and provide a structured response:

TEXT TO ANALYZE:
{text}

Please provide your analysis in the following JSON format:
{{
    "subject": "math|english|science|social_studies",
    "content_type": "notes|practice_problem|wrong_answer_explanation|concept_summary",
    "confidence": 85,
    "key_concepts": ["concept1", "concept2"],
    "notes": "Well-organized study notes based on the content...",
    "summary": "Brief summary of the main points..."
}}

Focus on creating helpful, organized study notes that would be useful for SAT/ACT preparation.
"""

    def _parse_ai_response(self, response_content: str, image_name: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data."""
        try:
            # Try to extract JSON from the response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                parsed_data = json.loads(json_str)

                # Ensure required fields exist
                result = {
                    'subject': parsed_data.get('subject', 'general'),
                    'content_type': parsed_data.get('content_type', 'notes'),
                    'confidence': parsed_data.get('confidence', 75),
                    'key_concepts': parsed_data.get('key_concepts', []),
                    'notes': parsed_data.get('notes', ''),
                    'summary': parsed_data.get('summary', ''),
                    'source_image': image_name
                }

                return result
            else:
                # If no JSON found, treat entire response as notes
                return self._create_fallback_response(response_content, image_name)

        except json.JSONDecodeError:
            # If JSON parsing fails, use the response as notes
            return self._create_fallback_response(response_content, image_name)

    def _create_fallback_response(self, content: str, image_name: str) -> Dict[str, Any]:
        """Create a fallback response when AI processing fails."""
        return {
            'subject': 'general',
            'content_type': 'notes',
            'confidence': 50,
            'key_concepts': [],
            'notes': content if content else "No content could be processed from this image.",
            'summary': "Content extracted from image but could not be fully analyzed.",
            'source_image': image_name
        }

    def classify_content(self, text: str) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        return self.process_text(text, "unknown_image")

    def _assess_text_quality(self, text: str) -> str:
        """
        Assess the quality of OCR text to determine processing approach.

        Args:
            text: The text to assess

        Returns:
            str: Quality assessment ('good', 'poor', 'corrupted')
        """
        if not text or len(text) < 10:
            return "poor"

        # Count readable vs unreadable characters
        words = text.split()
        if len(words) == 0:
            return "corrupted"

        # Check for signs of severe OCR corruption
        corruption_score = 0

        # 1. Too many single characters scattered around
        single_chars = len([w for w in words if len(w) == 1 and not w.isalnum()])
        if single_chars > len(words) * 0.25:  # Lower threshold
            corruption_score += 1

        # 2. Too many special characters relative to letters
        special_chars = len([c for c in text if not c.isalnum() and not c.isspace() and c not in '.,!?()-'])
        total_chars = len(text)
        if total_chars > 0 and special_chars / total_chars > 0.3:  # Lower threshold
            corruption_score += 1

        # 3. Very low ratio of recognizable words
        recognizable_words = len([w for w in words if len(w) >= 3 and sum(c.isalpha() for c in w) / len(w) > 0.7])
        if len(words) > 0 and recognizable_words / len(words) < 0.4:  # Lower threshold
            corruption_score += 1

        # 4. Excessive repetition of noise patterns (scattered letters)
        if len(re.findall(r'[a-zA-Z]\s+[a-zA-Z]\s+[a-zA-Z]', text)) > 5:  # Lower threshold
            corruption_score += 1

        # 5. Common OCR artifacts
        ocr_artifacts = len(re.findall(r'\b(ee|oe|ae|ce|Se|Le|Ae|Ve|We|He)\b', text))
        if ocr_artifacts > 10:
            corruption_score += 1

        # 6. Excessive punctuation noise
        noise_punct = len(re.findall(r'[—–@#$%^&*_+={}[\]|\\:";\'<>?,./`~]', text))
        if noise_punct > len(text) * 0.1:
            corruption_score += 1

        # 7. Pattern of meaningless character combinations
        meaningless_combos = len(re.findall(r'\b[a-zA-Z]{1,2}\s+[a-zA-Z]{1,2}\s', text))
        if meaningless_combos > 15:
            corruption_score += 1

        if corruption_score >= 3:
            return "corrupted"
        elif corruption_score >= 1:
            return "poor"
        else:
            return "good"
