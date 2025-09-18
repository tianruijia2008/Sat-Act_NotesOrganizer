#!/usr/bin/env python3
"""
Main orchestrator script for SAT/ACT Notes Organizer.
Coordinates all components: file watching, OCR processing, AI classification, and notes saving.
"""

import os
import sys
import time
import logging
import argparse
from typing import Any, Optional

# Add the parent directory to the path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.file_watcher import FileWatcher
from src.ocr_processor import OCRProcessor
from src.ai_processor import AIProcessor
from src.notes_saver import NotesSaver

class SATActNotesOrganizer:
    """
    Main orchestrator for the SAT/ACT Notes Organizer project.
    """

    def __init__(self, config_path: Optional[str] = None, watch_mode: bool = False):
        """
        Initialize the orchestrator.

        Args:
            config_path (str): Path to the configuration file
            watch_mode (bool): Whether to run in continuous watch mode
        """
        self.config_path = config_path
        self.watch_mode = watch_mode
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.file_watcher = FileWatcher("data/raw", self.process_new_image)
        self.ocr_processor = OCRProcessor()
        self.ai_processor = AIProcessor(config_path)
        self.notes_saver = NotesSaver("data/notes")

        # Accumulated content for batch processing
        self.accumulated_content: list[tuple[str, dict[str, Any]]] = []

    def process_new_image(self, image_path: str):
        """
        Process a new image file: OCR -> AI classification -> Save result.

        Args:
            image_path (str): Path to the image file
        """
        try:
            self.logger.info(f"Processing new image: {image_path}")

            # Step 1: Extract text using OCR
            ocr_text = self.ocr_processor.extract_text(image_path)
            self.logger.info(f"Extracted {len(ocr_text)} characters from {image_path}")

            if not ocr_text.strip():
                self.logger.warning(f"No text extracted from {image_path}")
                return

            # Step 2: Classify content using AI
            classification_result = self.ai_processor.classify_content(ocr_text)
            self.logger.info(f"Classification result: {classification_result.get('classification')}")

            # Step 3: Save individual classification result
            image_filename = os.path.basename(image_path)
            self.notes_saver.save_classification_result(ocr_text, classification_result, image_filename)

            # Step 4: Add to accumulated content for batch processing
            self.accumulated_content.append((ocr_text, classification_result))

            self.logger.info(f"Successfully processed {image_path}")

        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")

    def process_batch(self):
        """
        Process accumulated content in batch mode.
        """
        if not self.accumulated_content:
            self.logger.info("No accumulated content to process")
            return

        try:
            self.logger.info(f"Processing batch of {len(self.accumulated_content)} items")

            # Step 1: Organize content using AI
            organized_content = self.ai_processor.organize_content_batch(self.accumulated_content)

            # Step 2: Save organized content
            batch_name = f"batch_{int(time.time())}"
            saved_path = self.notes_saver.save_organized_content(organized_content, batch_name)

            self.logger.info(f"Successfully processed batch and saved to {saved_path}")

            # Clear accumulated content
            self.accumulated_content.clear()

        except Exception as e:
            self.logger.error(f"Error processing batch: {str(e)}")

    def process_existing_images(self):
        """
        Process all existing images in the raw directory.
        """
        self.logger.info("Processing existing images in raw directory")

        # Get list of existing images
        existing_images = self.file_watcher.watch_once()

        if not existing_images:
            self.logger.info("No existing images found in raw directory")
            return

        # Process each image
        for image_path in existing_images:
            self.process_new_image(image_path)

        # Process accumulated content in batch
        if self.accumulated_content:
            self.process_batch()

    def run(self):
        """
        Run the orchestrator in the specified mode.
        """
        try:
            # Test AI connection first
            self.logger.info("Testing AI connection...")
            connection_success = self.ai_processor.test_connection()
            if not connection_success:
                self.logger.error("Failed to connect to AI API. Exiting.")
                return

            self.logger.info("AI connection successful")

            if self.watch_mode:
                # Watch mode: continuously monitor for new images
                self.logger.info("Starting in watch mode")
                self.process_existing_images()  # Process existing images first
                self.logger.info("Watching for new images. Press Ctrl+C to stop.")
                self.file_watcher.start()

                try:
                    while True:
                        time.sleep(1)
                        # Process batch every 10 items or every 5 minutes
                        if len(self.accumulated_content) >= 10:
                            self.process_batch()
                except KeyboardInterrupt:
                    self.logger.info("Stopping watch mode...")
                    self.file_watcher.stop()
                    # Process any remaining accumulated content
                    if self.accumulated_content:
                        self.process_batch()
            else:
                # Batch mode: process existing images and exit
                self.logger.info("Running in batch mode")
                self.process_existing_images()

        except Exception as e:
            self.logger.error(f"Error running orchestrator: {str(e)}")

def main():
    """
    Main function to parse arguments and run the orchestrator.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="SAT/ACT Notes Organizer")
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default="config.json"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run in continuous watch mode"
    )

    args = parser.parse_args()

    # Initialize and run the orchestrator
    orchestrator = SATActNotesOrganizer(args.config, args.watch)
    orchestrator.run()

if __name__ == "__main__":
    main()
