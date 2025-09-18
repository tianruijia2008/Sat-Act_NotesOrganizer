import os
import logging
from typing import Optional, Any
from datetime import datetime

class NotesSaver:
    """
    Notes saver for converting organized content to Markdown format for Obsidian.
    """

    def __init__(self, output_directory: str = "data/notes"):
        """
        Initialize the notes saver.

        Args:
            output_directory (str): Directory to save the Markdown notes
        """
        self.output_directory: str = output_directory
        self.logger: logging.Logger = logging.getLogger(__name__)

        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)

    def save_organized_content(self, organized_content: dict[str, Any], batch_name: Optional[str] = None) -> str:
        """
        Save organized content as a Markdown file for Obsidian.

        Args:
            organized_content (dict): Organized content from AI processor
            batch_name (Optional[str], optional): Name for the batch of content

        Returns:
            str: Path to the saved Markdown file
        """
        try:
            # Generate filename with timestamp
            if batch_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                batch_name = f"sat_act_notes_{timestamp}"

            filename = f"{batch_name}.md"
            filepath = os.path.join(self.output_directory, filename)

            # Generate Markdown content
            markdown_content = self._generate_markdown(organized_content)

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            self.logger.info(f"Successfully saved organized content to {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error saving organized content: {str(e)}")
            raise

    def _generate_markdown(self, organized_content: dict[str, Any]) -> str:
        """
        Generate Markdown content from organized content.

        Args:
            organized_content (dict): Organized content from AI processor

        Returns:
            str: Generated Markdown content
        """
        lines = []

        # Add title
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"# SAT/ACT Study Materials - {timestamp}")
        lines.append("")

        # Add summary
        summary = organized_content.get("summary", "No summary provided")
        lines.append(f"## Summary")
        lines.append(summary)
        lines.append("")

        # Add relationships
        relationships = organized_content.get("relationships", "No relationships identified")
        lines.append(f"## Content Relationships")
        lines.append(relationships)
        lines.append("")

        # Add notes section
        notes = organized_content.get("notes", [])
        if notes:
            lines.append("## Notes")
            for i, note in enumerate(notes, 1):
                lines.append(f"### Note {i}")
                content = note.get("content", "No content")
                lines.append(content)

                # Add related wrong questions if any
                related_questions = note.get("related_wrong_questions", [])
                if related_questions:
                    related_list = ", ".join([f"Question {q+1}" for q in related_questions])
                    lines.append(f"**Related Wrong Questions:** {related_list}")

                lines.append("")

        # Add wrong questions section
        wrong_questions = organized_content.get("wrong_questions", [])
        if wrong_questions:
            lines.append("## Wrong Questions")
            for i, question in enumerate(wrong_questions, 1):
                lines.append(f"### Question {i}")
                content = question.get("content", "No content")
                lines.append(content)

                # Add related notes if any
                related_notes = question.get("related_notes", [])
                if related_notes:
                    related_list = ", ".join([f"Note {n+1}" for n in related_notes])
                    lines.append(f"**Related Notes:** {related_list}")

                # Add mistake explanation
                mistake = question.get("mistake_explanation", "")
                if mistake:
                    lines.append(f"**Mistake Explanation:** {mistake}")

                # Add correct approach
                approach = question.get("correct_approach", "")
                if approach:
                    lines.append(f"**Correct Approach:** {approach}")

                lines.append("")

        # Add metadata
        lines.append("---")
        lines.append(f"**Generated on:** {timestamp}")
        lines.append(f"**Total Notes:** {len(notes)}")
        lines.append(f"**Total Wrong Questions:** {len(wrong_questions)}")

        return "\n".join(lines)

    def save_classification_result(self, ocr_text: str, classification_result: dict[str, Any],
                                 image_filename: Optional[str] = None) -> str:
        """
        Save individual classification result as a Markdown file.

        Args:
            ocr_text (str): Original OCR extracted text
            classification_result (dict): Classification result from AI processor
            image_filename (Optional[str], optional): Original image filename

        Returns:
            str: Path to the saved Markdown file
        """
        try:
            # Generate filename
            if image_filename:
                base_name = os.path.splitext(image_filename)[0]
                filename = f"classification_{base_name}.md"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"classification_{timestamp}.md"

            filepath = os.path.join(self.output_directory, filename)

            # Generate Markdown content
            lines = []

            # Add title
            lines.append(f"# Classification Result - {filename}")
            lines.append("")

            # Add classification info
            classification = classification_result.get("classification", "unknown")
            confidence = classification_result.get("confidence", 0.0)
            reasoning = classification_result.get("reasoning", "No reasoning provided")

            lines.append(f"**Type:** {classification}")
            lines.append(f"**Confidence:** {confidence:.2f}")
            lines.append(f"**Reasoning:** {reasoning}")
            lines.append("")

            # Add original OCR text
            lines.append("## Original OCR Text")
            lines.append("```")
            lines.append(ocr_text)
            lines.append("```")
            lines.append("")

            # Add metadata
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append("---")
            lines.append(f"**Classified on:** {timestamp}")
            if image_filename:
                lines.append(f"**Source Image:** {image_filename}")

            markdown_content = "\n".join(lines)

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            self.logger.info(f"Successfully saved classification result to {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error saving classification result: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Example organized content
    example_content = {
        "summary": "This batch contains 2 notes and 1 wrong question about quadratic equations.",
        "notes": [
            {
                "content": "The quadratic formula is x = (-b +/- sqrt(b^2 - 4ac)) / (2a) for equations of the form ax^2 + bx + c = 0.",
                "related_wrong_questions": [0]
            }
        ],
        "wrong_questions": [
            {
                "content": "Solve x^2 + 5x + 6 = 0. I tried factoring but got x = -2, -4 which is wrong.",
                "related_notes": [0],
                "mistake_explanation": "Incorrect factoring - the factors of 6 that add to 5 are 2 and 3, not 4 and 1.",
                "correct_approach": "Factor as (x + 2)(x + 3) = 0, giving solutions x = -2, -3."
            }
        ],
        "relationships": "The note on quadratic formula directly relates to the wrong question about solving quadratic equations."
    }

    # Initialize notes saver
    notes_saver = NotesSaver()

    # Save organized content
    try:
        filepath = notes_saver.save_organized_content(example_content, "quadratic_equations_example")
        print(f"Saved example content to: {filepath}")
    except Exception as e:
        print(f"Error saving example content: {e}")
