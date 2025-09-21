import pytesseract
from PIL import Image
import cv2
import numpy as np
import os
import logging
import re
from typing import Any

class OCRProcessor:
    """
    Enhanced OCR Processor for extracting text from images using pytesseract.
    Optimized for SAT/ACT study materials with advanced preprocessing.
    """

    def __init__(self):
        """Initialize OCR processor."""
        self.logger: logging.Logger = logging.getLogger(__name__)
        # Start with a more flexible PSM mode
        self.tesseract_config: str = '--psm 6'

    def detect_orientation(self, image_path: str) -> dict[str, Any]:
        """
        Detect the orientation of an image to improve OCR accuracy.
        Handles 90°, 180°, and 270° rotations commonly found in camera photos.

        Args:
            image_path (str): Path to the image file

        Returns:
            dict: Orientation information
        """
        try:
            # Open image
            image = Image.open(image_path)
            opencv_image = np.array(image.convert('L'))

            # Method 1: Try to detect text orientation using HoughLines for small rotations
            edges = cv2.Canny(opencv_image, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

            hough_angle = 0
            if lines is not None and len(lines) > 0:
                angles = []
                for rho, theta in lines[:, 0]:
                    # Convert to degrees
                    angle_deg = np.degrees(theta)
                    # Normalize to -45 to 45 range
                    if angle_deg > 45 and angle_deg < 135:
                        angles.append(angle_deg - 90)
                    elif angle_deg > 135:
                        angles.append(angle_deg - 180)
                    else:
                        angles.append(angle_deg)

                if angles:
                    hough_angle = np.median(angles)

            # Method 2: Use pytesseract's built-in OSD (Orientation and Script Detection)
            osd_angle = 0
            try:
                osd = pytesseract.image_to_osd(image)
                osd_str = str(osd) if isinstance(osd, (bytes, dict)) else osd
                for line in osd_str.split('\n'):
                    if line.strip().startswith('Rotate:'):
                        osd_angle = int(line.split(':')[1].strip())
                        break
            except Exception as e:
                self.logger.debug(f"OSD detection failed: {e}")

            # Choose the most reliable angle
            final_angle = osd_angle if abs(osd_angle) > 5 else hough_angle

            # Determine if rotation is needed (threshold of 5 degrees)
            needs_rotation = abs(final_angle) > 5

            # Recommend rotation angle (round to nearest 90 degrees for major rotations)
            if abs(final_angle) > 45:
                if final_angle > 0:
                    recommended_rotation = 90
                else:
                    recommended_rotation = -90
            elif abs(final_angle) > 5:
                recommended_rotation = -final_angle  # Counter-rotate
            else:
                recommended_rotation = 0

            return {
                'angle': final_angle,
                'needs_rotation': needs_rotation,
                'recommended_rotation': recommended_rotation,
                'method': 'osd' if abs(osd_angle) > 5 else 'hough'
            }

        except Exception as e:
            self.logger.error(f"Error detecting orientation: {e}")
            return {
                'angle': 0,
                'needs_rotation': False,
                'recommended_rotation': 0,
                'method': 'error'
            }

    def assess_image_quality(self, image_path: str) -> dict[str, Any]:
        """
        Assess the quality of an image for OCR purposes.

        Args:
            image_path (str): Path to the image file

        Returns:
            dict: Quality assessment information
        """
        try:
            # Open image
            image = Image.open(image_path)
            opencv_image = np.array(image.convert('L'))

            # Calculate various quality metrics

            # 1. Sharpness (Laplacian variance)
            laplacian = cv2.Laplacian(opencv_image, cv2.CV_64F)
            sharpness = laplacian.var()

            # 2. Contrast (standard deviation)
            contrast = opencv_image.std()

            # 3. Brightness (mean pixel value)
            brightness = opencv_image.mean()

            # 4. Noise estimation (using Gaussian blur difference)
            blurred = cv2.GaussianBlur(opencv_image, (5, 5), 0)
            noise_level = np.sum((opencv_image.astype("float") - blurred.astype("float")) ** 2)
            noise_level /= float(opencv_image.shape[0] * opencv_image.shape[1])

            # 5. Text region detection
            edges = cv2.Canny(opencv_image, 50, 150, apertureSize=3)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            text_regions = len(contours)

            # 6. Horizontal line detection (common in text)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            detect_horizontal = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            horizontal_lines = cv2.countNonZero(detect_horizontal)

            # 7. Resolution score
            height, width = opencv_image.shape
            resolution_score = min(100, (width * height) / 10000)  # Normalize to 100

            # Calculate overall quality score (0-100)
            quality_score = 0

            # Sharpness contribution (30%)
            if sharpness > 100:
                quality_score += 30
            elif sharpness > 50:
                quality_score += 20
            elif sharpness > 10:
                quality_score += 10

            # Contrast contribution (25%)
            if contrast > 50:
                quality_score += 25
            elif contrast > 30:
                quality_score += 15
            elif contrast > 10:
                quality_score += 8

            # Brightness contribution (20%) - prefer moderate brightness
            if 50 <= brightness <= 200:
                quality_score += 20
            elif 30 <= brightness <= 220:
                quality_score += 15
            elif 10 <= brightness <= 240:
                quality_score += 10

            # Low noise contribution (15%)
            if noise_level < 50:
                quality_score += 15
            elif noise_level < 100:
                quality_score += 10
            elif noise_level < 200:
                quality_score += 5

            # Text regions contribution (10%)
            if text_regions > 10:
                quality_score += 10
            elif text_regions > 5:
                quality_score += 7
            elif text_regions > 0:
                quality_score += 3

            # Determine quality grade
            if quality_score >= 80:
                grade = 'A'
                quality_description = 'Excellent - Optimal for OCR'
            elif quality_score >= 65:
                grade = 'B'
                quality_description = 'Good - Should work well for OCR'
            elif quality_score >= 50:
                grade = 'C'
                quality_description = 'Fair - May need preprocessing'
            elif quality_score >= 35:
                grade = 'D'
                quality_description = 'Poor - Significant OCR challenges expected'
            else:
                grade = 'F'
                quality_description = 'Very Poor - OCR likely to fail'

            return {
                'overall_score': quality_score,
                'grade': grade,
                'quality_description': quality_description,
                'metrics': {
                    'sharpness': sharpness,
                    'contrast': contrast,
                    'brightness': brightness,
                    'noise_level': noise_level,
                    'text_regions': text_regions,
                    'horizontal_lines': horizontal_lines,
                    'resolution_score': resolution_score,
                    'edges': cv2.countNonZero(edges)
                }
            }

        except Exception as e:
            self.logger.error(f"Error assessing image quality: {e}")
            return {
                'overall_score': 0,
                'grade': 'F',
                'quality_description': 'Error assessing quality',
                'metrics': {}
            }

    def preprocess_image(self, image_path: str) -> list[Image.Image]:
        """
        Preprocess image with essential techniques to improve OCR accuracy.

        Args:
            image_path (str): Path to the image file

        Returns:
            list: List of processed PIL Images to try OCR on
        """
        try:
            # Load image
            image = Image.open(image_path)
            opencv_image = np.array(image.convert('L'))

            processed_images: list[Image.Image] = []

            # 1. Original grayscale (baseline)
            processed_images.append(Image.fromarray(opencv_image))

            # 2. Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(opencv_image, (3, 3), 0)
            processed_images.append(Image.fromarray(blurred))

            # 3. Adaptive threshold (good for uneven lighting)
            adaptive_thresh = cv2.adaptiveThreshold(
                opencv_image, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            processed_images.append(Image.fromarray(adaptive_thresh))

            # 4. Morphological operations to clean up text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morphed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            processed_images.append(Image.fromarray(morphed))

            return processed_images

        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            # Return original image as fallback
            return [Image.open(image_path).convert('L')]

    def _clean_text(self, text: str) -> str:
        """
        Clean and correct common OCR errors in extracted text.

        Args:
            text (str): Raw OCR text

        Returns:
            str: Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Fix common OCR character mistakes
        replacements = {
            '|': 'I',
            '0': 'O',  # Only in specific contexts
            '5': 'S',  # Only in specific contexts
            '1': 'l',  # Only in specific contexts
        }

        # Apply replacements carefully (only for obvious mistakes)
        for old, new in replacements.items():
            # Only replace standalone characters that are clearly mistakes
            text = re.sub(f'\\b{re.escape(old)}\\b', new, text)

        # Remove special characters that are clearly OCR noise
        text = re.sub(r'[^\w\s.,!?()[\]{}:;"\'-+=<>/\\]', '', text)

        return text.strip()

    def extract_text(self, image_path: str, preprocess: bool = True) -> str:
        """
        Extract text from an image using OCR with multiple advanced approaches.

        Args:
            image_path (str): Path to the image file
            preprocess (bool): Whether to preprocess the image

        Returns:
            str: Extracted text
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            best_text = ""
            best_confidence = 0

            # Get list of images to try (preprocessed versions if enabled)
            if preprocess:
                images_to_try = self.preprocess_image(image_path)
            else:
                images_to_try = [Image.open(image_path).convert('L')]

            # Try different PSM (Page Segmentation Mode) configurations
            psm_configs = [
                '--psm 6',  # Uniform block of text
                '--psm 4',  # Single column of text
                '--psm 3',  # Fully automatic page segmentation
                '--psm 1',  # Automatic page segmentation with OSD
            ]

            for img in images_to_try:
                for config in psm_configs:
                    try:
                        # Try to get confidence data
                        try:
                            data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
                            if isinstance(data, dict) and 'conf' in data and 'text' in data:
                                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                                text = ' '.join([data['text'][i] for i, conf in enumerate(data['conf']) if int(conf) > 30])
                            else:
                                raise ValueError("Invalid data format from pytesseract")
                        except:
                            # Fallback to simple OCR if no confidence data
                            raw_text = pytesseract.image_to_string(img, config=config)
                            text = str(raw_text) if isinstance(raw_text, (bytes, dict)) else raw_text
                            avg_confidence = 50  # Default confidence

                        # Clean up extracted text
                        cleaned_text = self._clean_text(text)

                        # Score this attempt
                        text_score = self._score_text_quality(cleaned_text)
                        combined_score = (avg_confidence + text_score) / 2

                        if combined_score > best_confidence and len(cleaned_text.strip()) > 0:
                            best_text = cleaned_text
                            best_confidence = combined_score

                    except Exception as e:
                        self.logger.debug(f"OCR attempt failed with config {config}: {e}")
                        continue

            # If we still don't have good text, try one more aggressive approach
            if not best_text.strip() or best_confidence < 30:
                try:
                    # Last resort: try with no preprocessing and minimal config
                    simple_image = Image.open(image_path).convert('L')
                    raw_fallback = pytesseract.image_to_string(simple_image, config='--psm 8')
                    fallback_text = str(raw_fallback) if isinstance(raw_fallback, (bytes, dict)) else raw_fallback
                    if len(fallback_text.strip()) > len(best_text.strip()):
                        best_text = self._clean_text(fallback_text)
                except Exception as e:
                    self.logger.debug(f"Fallback OCR failed: {e}")

            return best_text if best_text else ""

        except Exception as e:
            self.logger.error(f"Error extracting text from {image_path}: {e}")
            return ""

    def _score_text_quality(self, text: str) -> int:
        """
        Score text quality based on readability heuristics.

        Args:
            text (str): Text to score

        Returns:
            int: Quality score (0-100)
        """
        if not text:
            return 0

        score = 0

        # Base score for having text
        score += 10

        # Length bonus (but with diminishing returns)
        length_score = min(30, len(text) // 5)
        score += length_score

        # Bonus for proper word-like structures
        word_count = len(re.findall(r'\b[a-zA-Z]{3,}\b', text))  # 3+ letter words
        score += min(25, word_count * 2)

        # Bonus for numbers (common in academic content)
        number_count = len(re.findall(r'\b\d+\b', text))
        score += min(15, number_count * 3)

        # Penalty for excessive special characters
        special_char_count = len(re.findall(r'[^\w\s.,!?()[\]{}:;"\'-]', text))
        if special_char_count > len(text) * 0.3:  # More than 30% special chars
            score -= 20

        # Bonus for sentence-like structures
        sentence_count = len(re.findall(r'[.!?]+', text))
        score += min(10, sentence_count * 2)

        return max(0, min(100, score))
