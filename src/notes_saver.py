import os
import logging
from datetime import datetime
from typing import Any, Optional, Tuple
import sys

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils import get_resource_path
from src.vector_db import VectorDatabase
from src.note_merger import NoteMerger

class NotesSaver:
    """
    Simplified notes saver for converting processed content to Markdown format.
    Integrated with vector database for note merging functionality.
    """

    def __init__(self):
        """Initialize the notes saver with vector database integration."""
        self.output_directory = get_resource_path('data/notes')
        self.logger = logging.getLogger(__name__)

        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)

        # Initialize vector database and note merger
        try:
            self.vector_db = VectorDatabase()
            self.note_merger = NoteMerger()
            self.use_vector_db = True
            self.logger.info("Vector database integration enabled")
        except Exception as e:
            self.logger.warning(f"Vector database initialization failed: {e}. Proceeding without vector database.")
            self.use_vector_db = False

    def save_classification_result(self, classification_result: dict[str, Any],
                                 extracted_text: str, image_name: str) -> Tuple[str, bool]:
        """
        Save classification result as a Markdown file.
        Checks for similar notes and merges if appropriate.

        Args:
            classification_result: AI processing result
            extracted_text: Original OCR text
            image_name: Source image filename

        Returns:
            Tuple of (Path to the saved Markdown file, whether it was merged)
        """
        try:
            # If vector database is available, check for similar notes
            if self.use_vector_db:
                merged_result = self._check_and_merge_similar_notes(
                    classification_result, extracted_text, image_name
                )
                if merged_result:
                    return merged_result  # merged_result is already a tuple (filepath, bool)

            # Generate filename
            base_name = os.path.splitext(image_name)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}.md"
            filepath = os.path.join(self.output_directory, filename)

            # Generate Markdown content
            markdown_content = self._generate_markdown(
                classification_result, extracted_text, image_name
            )

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            # Add to vector database if available
            if self.use_vector_db:
                _ = self._add_note_to_vector_db(filepath, classification_result, filename)

            self.logger.info(f"Saved notes to {filepath}")
            return filepath, False  # Return filepath and merge indicator (False = not merged)

        except Exception as e:
            self.logger.error(f"Error saving notes: {e}")
            raise

    def _check_and_merge_similar_notes(self, classification_result: dict[str, Any],
                                     extracted_text: str, image_name: str) -> Optional[Tuple[str, bool]]:
        """
        Check for similar notes and merge if appropriate.

        Args:
            classification_result: AI processing result
            extracted_text: Original OCR text
            image_name: Source image filename

        Returns:
            Tuple of (Path to merged file, True) if merged, None otherwise
        """
        try:
            # Create content for similarity search
            search_content = self._create_search_content(classification_result)

            # Find similar notes
            similar_notes = self.vector_db.find_similar_notes(
                search_content, threshold=0.8, top_k=1
            )

            # If similar note found, merge them
            if similar_notes:
                similar_note = similar_notes[0]
                self.logger.info(f"Found similar note: {similar_note['id']} with similarity {similar_note['similarity']:.3f}")

                # Load existing note data
                existing_note_path = os.path.join(self.output_directory, similar_note['id'])
                if os.path.exists(existing_note_path):
                    # Merge notes
                    merged_note = self.note_merger.merge_notes(
                        similar_note['metadata'], classification_result
                    )

                    # Update the existing file with merged content
                    merged_content = self._generate_markdown(
                        merged_note, extracted_text,
                        f"{similar_note['metadata'].get('source_image', '')}, {image_name}"
                    )

                    with open(existing_note_path, 'w', encoding='utf-8') as f:
                        f.write(merged_content)

                    # Update vector database
                    _ = self.vector_db.update_note_embedding(
                        similar_note['id'],
                        self._create_search_content(merged_note),
                        merged_note
                    )

                    self.logger.info(f"Successfully merged note with {similar_note['id']}")
                    return (existing_note_path, True)  # Return filepath and merge indicator

            return None

        except Exception as e:
            self.logger.error(f"Error checking/merging similar notes: {e}")
            return None

    def _create_search_content(self, classification_result: dict[str, Any]) -> str:
        """
        Create content for similarity search from classification result.

        Args:
            classification_result: AI processing result

        Returns:
            str: Content for similarity search
        """
        # Combine key elements for semantic search
        content_parts = []

        # Add subject and content type
        subject = classification_result.get('subject', '')
        content_type = classification_result.get('content_type', '')
        if subject or content_type:
            content_parts.append(f"Subject: {subject}, Type: {content_type}")

        # Add key concepts
        key_concepts = classification_result.get('key_concepts', [])
        if key_concepts:
            content_parts.append(f"Key concepts: {', '.join(key_concepts)}")

        # Add summary
        summary = classification_result.get('summary', '')
        if summary:
            content_parts.append(f"Summary: {summary}")

        # Add main notes content
        notes = classification_result.get('notes', '')
        if notes:
            content_parts.append(f"Notes: {notes}")

        return "\n".join(content_parts)

    def _add_note_to_vector_db(self, filepath: str, classification_result: dict[str, Any], filename: str) -> bool:
        """
        Add note to vector database.

        Args:
            filepath: Path to the note file
            classification_result: AI processing result
            filename: Name of the file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            search_content = self._create_search_content(classification_result)
            return self.vector_db.add_note_embedding(filename, search_content, classification_result)
        except Exception as e:
            self.logger.error(f"Error adding note to vector database: {e}")
            return False

    def _generate_markdown(self, classification: dict[str, Any],
                          extracted_text: str, image_name: str) -> str:
        """Generate Markdown content from classification result."""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = classification.get('subject', 'General').title()
        content_type = classification.get('content_type', 'Notes').title()
        confidence = classification.get('confidence', 0)
        key_concepts = classification.get('key_concepts', [])
        notes = classification.get('notes', '')
        summary = classification.get('summary', '')

        lines = [
            f"# {subject} - {content_type}",
            "",
            f"**Source:** {image_name}",
            f"**Generated:** {timestamp}",
            f"**Confidence:** {confidence}%",
            "",
        ]

        # Add key concepts if available
        if key_concepts:
            lines.extend([
                "## Key Concepts",
                "",
                *[f"- {concept}" for concept in key_concepts],
                "",
            ])

        # Add summary if available
        if summary:
            lines.extend([
                "## Summary",
                "",
                summary,
                "",
            ])

        # Add main notes content
        if notes:
            lines.extend([
                "## Notes",
                "",
                notes,
                "",
            ])

        # Add original extracted text
        lines.extend([
            "## Original Text",
            "",
            "```",
            extracted_text,
            "```",
            "",
            "---",
            f"*Generated by SAT/ACT Notes Organizer on {timestamp}*"
        ])

        return "\n".join(lines)
