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
import json
from typing import Any, Optional, List, Tuple, Dict

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
        config_dict = {}
        if config_path:
            from src.utils import load_config
            config_dict = load_config(config_path)
        self.file_watcher = FileWatcher("data/raw", self.process_new_image)
        self.ocr_processor = OCRProcessor(config_dict)
        self.ai_processor = AIProcessor(config_path)
        self.notes_saver = NotesSaver("data/notes")

        # Accumulated content for batch processing
        # Now includes image filename: (ocr_text, classification_result, image_filename)
        self.accumulated_content: list[tuple[str, dict[str, Any], str]] = []

    def process_new_image(self, image_path: str):
        """
        Process a new image file: OCR -> AI classification -> Save result.

        Args:
            image_path (str): Path to the image file
        """
        try:
            self.logger.info(f"Processing new image: {image_path}")

            # Step 1: Extract text using OCR
            ocr_text, doc_id = self.ocr_processor.extract_text(image_path)
            self.logger.info(f"Extracted {len(ocr_text)} characters from {image_path}")

            if not ocr_text.strip():
                self.logger.warning(f"No text extracted from {image_path}")
                return

            # Step 2: Classify content using AI
            classification_result = self.ai_processor.classify_content(ocr_text)
            self.logger.info(f"Classification result: {classification_result.get('classification')}")

            # Step 3: Update document metadata in vector database with classification results
            update_success = self.ocr_processor.update_document_metadata(doc_id, classification_result)
            if update_success:
                self.logger.info(f"Updated document {doc_id} with classification metadata")
            else:
                self.logger.warning(f"Failed to update document {doc_id} with classification metadata")

            # Step 3: Update document metadata in vector database with classification results
            # Note: We don't have the doc_id here, so we'll need to modify the OCR processor
            # to return it or find another way to update the metadata

            # Step 4: Save individual classification result
            image_filename = os.path.basename(image_path)
            self.notes_saver.save_classification_result(ocr_text, classification_result, image_filename)

            # Step 5: Add to accumulated content for batch processing (with filename)
            self.accumulated_content.append((ocr_text, classification_result, image_filename))

            self.logger.info(f"Successfully processed {image_path}")

        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")

    def process_with_two_stage_ai(self):
        """
        Process accumulated content using two-stage AI approach.
        """
        if not self.accumulated_content:
            self.logger.info("No accumulated content to process")
            return

        try:
            self.logger.info(f"Processing batch of {len(self.accumulated_content)} items with two-stage AI")

            # Stage 1: Get organization strategy recommendation from AI
            self.logger.info("Stage 1: Getting organization strategy recommendation from AI")
            recommendation = self.ai_processor.recommend_organization_strategy(self.accumulated_content)

            strategy = recommendation.get('strategy', 'separate_all')
            reasoning = recommendation.get('reasoning', 'No reasoning provided')
            groups = recommendation.get('groups', [])
            recommendations = recommendation.get('recommendations', {})

            # Print the first-stage AI output
            print("\n" + "="*60)
            print("FIRST-STAGE AI ANALYSIS - ORGANIZATION STRATEGY")
            print("="*60)
            print(f"Strategy: {strategy}")
            print(f"Reasoning: {reasoning}")
            print(f"Number of groups: {len(groups)}")
            if recommendations:
                print(f"File naming recommendation: {recommendations.get('file_naming', 'N/A')}")
                print(f"Content structure recommendation: {recommendations.get('content_structure', 'N/A')}")
            print("\nGroups:")
            for i, group in enumerate(groups):
                print(f"  Group {i+1}: {group.get('name', 'Unnamed Group')}")
                print(f"    Items: {group.get('items', [])}")
                print(f"    Rationale: {group.get('rationale', 'No rationale provided')}")
            print("="*60 + "\n")

            self.logger.info(f"AI recommended strategy: {strategy}")
            self.logger.info(f"Reasoning: {reasoning}")
            self.logger.info(f"Number of groups: {len(groups)}")

            # Stage 2: Process content according to recommended strategy
            if strategy == 'combine_all' and len(groups) > 0:
                # Combine all items into a single comprehensive file
                self.logger.info("Combining all items into a single file")
                group = groups[0]  # There should be only one group for combine_all strategy
                item_indices = group.get('items', [])

                # Extract content items for this group
                group_content_items = [self.accumulated_content[i] for i in item_indices if i < len(self.accumulated_content)]

                # Convert to the format expected by organize_content_batch
                batch_items = [(item[0], item[1]) for item in group_content_items]

                # Organize the content
                organized_content = self.ai_processor.organize_content_batch(batch_items)
                organized_content['group_name'] = group.get('name', 'Combined Content')
                organized_content['group_rationale'] = group.get('rationale', 'Combined all items')
                organized_content['item_indices'] = item_indices
                organized_content['source_files'] = [self.accumulated_content[i][2] for i in item_indices if i < len(self.accumulated_content)]

                # Save organized content
                batch_name = f"combined_{int(time.time())}"
                saved_path = self.notes_saver.save_organized_content(organized_content, batch_name)
                self.logger.info(f"Successfully saved combined content to {saved_path}")

            elif strategy == 'separate_all':
                # Create separate files for each item
                self.logger.info("Creating separate files for each item")
                for i, (ocr_text, classification_result, image_filename) in enumerate(self.accumulated_content):
                    batch_items = [(ocr_text, classification_result)]
                    organized_content = self.ai_processor.organize_content_batch(batch_items)
                    organized_content['group_name'] = f"Item {i+1}: {image_filename}"
                    organized_content['group_rationale'] = "Individual item processing"
                    organized_content['item_indices'] = [i]
                    organized_content['source_files'] = [image_filename]

                    # Save organized content
                    batch_name = f"individual_{i+1}_{int(time.time())}"
                    saved_path = self.notes_saver.save_organized_content(organized_content, batch_name)
                    self.logger.info(f"Successfully saved individual content to {saved_path}")

            elif strategy == 'group_related' and len(groups) > 0:
                # Group related items into multiple files
                self.logger.info("Grouping related items into multiple files")
                organized_groups = self.ai_processor.organize_content_by_groups(self.accumulated_content, groups)

                for i, organized_content in enumerate(organized_groups):
                    group_name = organized_content.get('group_name', f'Group {i+1}')
                    # Save organized content
                    batch_name = f"group_{i+1}_{group_name.replace(' ', '_').replace('/', '_')}_{int(time.time())}"
                    saved_path = self.notes_saver.save_organized_content(organized_content, batch_name)
                    self.logger.info(f"Successfully saved group content to {saved_path}")

            else:
                # Fallback: process each item separately
                self.logger.warning("Unknown strategy or no groups defined, falling back to individual processing")
                for i, (ocr_text, classification_result, image_filename) in enumerate(self.accumulated_content):
                    batch_items = [(ocr_text, classification_result)]
                    organized_content = self.ai_processor.organize_content_batch(batch_items)
                    organized_content['group_name'] = f"Fallback Item {i+1}: {image_filename}"
                    organized_content['group_rationale'] = "Fallback processing"
                    organized_content['item_indices'] = [i]
                    organized_content['source_files'] = [image_filename]

                    # Save organized content
                    batch_name = f"fallback_{i+1}_{int(time.time())}"
                    saved_path = self.notes_saver.save_organized_content(organized_content, batch_name)
                    self.logger.info(f"Successfully saved fallback content to {saved_path}")

            # Clear accumulated content
            self.accumulated_content.clear()

        except Exception as e:
            self.logger.error(f"Error processing with two-stage AI: {str(e)}")
            # Fallback to simple batch processing if two-stage AI fails
            self.logger.info("Falling back to simple batch processing")
            self.process_simple_batch()

    def process_simple_batch(self):
        """
        Fallback method: process accumulated content in simple batch mode.
        """
        if not self.accumulated_content:
            self.logger.info("No accumulated content to process")
            return

        try:
            self.logger.info(f"Processing batch of {len(self.accumulated_content)} items (simple mode)")

            # Convert to the format expected by organize_content_batch
            batch_items = [(item[0], item[1]) for item in self.accumulated_content]

            # Step 1: Organize content using AI
            organized_content = self.ai_processor.organize_content_batch(batch_items)

            # Step 2: Save organized content
            batch_name = f"batch_{int(time.time())}"
            saved_path = self.notes_saver.save_organized_content(organized_content, batch_name)

            self.logger.info(f"Successfully processed batch and saved to {saved_path}")

            # Clear accumulated content
            self.accumulated_content.clear()

        except Exception as e:
            self.logger.error(f"Error processing simple batch: {str(e)}")

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

        # Process accumulated content with two-stage AI approach
        if self.accumulated_content:
            self.process_with_two_stage_ai()
            
    def sync_obsidian_notes(self):
        """
        Sync notes from Obsidian vault to vector database.
        """
        try:
            self.logger.info("Syncing Obsidian notes to vector database...")
            
            # Import notes from Obsidian
            imported_count = self.ai_processor.vector_db.import_from_obsidian()
            
            self.logger.info(f"Successfully imported {imported_count} notes from Obsidian vault")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"Error syncing Obsidian notes: {str(e)}")
            return 0

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
            
            # Sync Obsidian notes at startup
            self.sync_obsidian_notes()

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
                            self.process_with_two_stage_ai()
                except KeyboardInterrupt:
                    self.logger.info("Stopping watch mode...")
                    self.file_watcher.stop()
                    # Process any remaining accumulated content
                    if self.accumulated_content:
                        self.process_with_two_stage_ai()
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
    parser.add_argument(
        "--sync-obsidian",
        action="store_true",
        help="Sync Obsidian notes only and exit"
    )

    args = parser.parse_args()

    # Initialize and run the orchestrator
    orchestrator = SATActNotesOrganizer(args.config, args.watch)
    
    if args.sync_obsidian:
        # Sync Obsidian notes only
        orchestrator.sync_obsidian_notes()
    else:
        # Run normal processing
        orchestrator.run()

if __name__ == "__main__":
    main()