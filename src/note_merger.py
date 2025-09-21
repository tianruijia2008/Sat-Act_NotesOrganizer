from typing import Dict, List
import re
from collections import Counter

class NoteMerger:
    """
    Handles intelligent merging of similar notes based on their content.
    """
    
    def __init__(self):
        """Initialize the note merger."""
        pass
    
    def merge_notes(self, existing_note: Dict, new_note: Dict) -> Dict:
        """
        Merge two similar notes intelligently.
        
        Args:
            existing_note (Dict): The existing note to merge into
            new_note (Dict): The new note with additional information
            
        Returns:
            Dict: Merged note with combined information
        """
        # Create a copy of the existing note to avoid modifying the original
        merged_note = existing_note.copy()
        
        # Merge the main content
        merged_note['notes'] = self._merge_content(
            existing_note.get('notes', ''), 
            new_note.get('notes', '')
        )
        
        # Merge key concepts
        merged_note['key_concepts'] = self._merge_key_concepts(
            existing_note.get('key_concepts', []), 
            new_note.get('key_concepts', [])
        )
        
        # Merge summaries
        merged_note['summary'] = self._merge_summaries(
            existing_note.get('summary', ''), 
            new_note.get('summary', '')
        )
        
        # Update confidence to the maximum of both
        merged_note['confidence'] = max(
            existing_note.get('confidence', 0), 
            new_note.get('confidence', 0)
        )
        
        # Update source image to include both sources
        merged_note['source_image'] = self._merge_source_images(
            existing_note.get('source_image', ''), 
            new_note.get('source_image', '')
        )
        
        # Update subject if new one is more specific
        merged_note['subject'] = self._merge_subjects(
            existing_note.get('subject', 'general'), 
            new_note.get('subject', 'general')
        )
        
        return merged_note
    
    def _merge_content(self, existing_content: str, new_content: str) -> str:
        """
        Merge note content intelligently.
        
        Args:
            existing_content (str): Existing note content
            new_content (str): New note content
            
        Returns:
            str: Merged content
        """
        # If existing content is empty, use new content
        if not existing_content.strip():
            return new_content
        
        # If new content is empty, keep existing content
        if not new_content.strip():
            return existing_content
        
        # Check if new content is significantly longer (more detailed)
        if len(new_content) > len(existing_content) * 1.5:
            return new_content
        
        # Check if new content contains more structured information
        existing_sections = existing_content.count('\n\n')
        new_sections = new_content.count('\n\n')
        
        if new_sections > existing_sections:
            return new_content
        
        # Otherwise, keep the existing content but append new information
        # that's not already present
        combined_content = existing_content
        
        # Split new content into sentences
        new_sentences = self._split_into_sentences(new_content)
        existing_sentences = self._split_into_sentences(existing_content)
        
        # Add sentences that are not already present
        for sentence in new_sentences:
            # Simple check for sentence similarity
            sentence_present = False
            for existing_sentence in existing_sentences:
                if self._sentences_similar(sentence, existing_sentence):
                    sentence_present = True
                    break
            
            if not sentence_present:
                combined_content += f"\n{sentence}"
        
        return combined_content
    
    def _merge_key_concepts(self, existing_concepts: List[str], new_concepts: List[str]) -> List[str]:
        """
        Merge key concepts from both notes.
        
        Args:
            existing_concepts (List[str]): Existing key concepts
            new_concepts (List[str]): New key concepts
            
        Returns:
            List[str]: Merged key concepts
        """
        # Combine and deduplicate concepts
        all_concepts = list(set(existing_concepts + new_concepts))
        
        # Sort by frequency/importance (this is a simple approach)
        # In a more advanced implementation, we could use TF-IDF or similar
        return sorted(all_concepts, key=len, reverse=True)
    
    def _merge_summaries(self, existing_summary: str, new_summary: str) -> str:
        """
        Merge summaries from both notes.
        
        Args:
            existing_summary (str): Existing summary
            new_summary (str): New summary
            
        Returns:
            str: Merged summary
        """
        # If new summary is significantly longer, use it
        if len(new_summary) > len(existing_summary) * 1.3:
            return new_summary
        
        # If existing summary is empty, use new summary
        if not existing_summary.strip():
            return new_summary
        
        # Otherwise, keep existing summary
        return existing_summary
    
    def _merge_source_images(self, existing_source: str, new_source: str) -> str:
        """
        Merge source image information.
        
        Args:
            existing_source (str): Existing source
            new_source (str): New source
            
        Returns:
            str: Merged source information
        """
        if existing_source and new_source:
            return f"{existing_source}, {new_source}"
        elif new_source:
            return new_source
        else:
            return existing_source
    
    def _merge_subjects(self, existing_subject: str, new_subject: str) -> str:
        """
        Merge subject information.
        
        Args:
            existing_subject (str): Existing subject
            new_subject (str): New subject
            
        Returns:
            str: Merged subject
        """
        # If new subject is more specific than 'general', use it
        if existing_subject.lower() == 'general' and new_subject.lower() != 'general':
            return new_subject
        # Otherwise, keep existing subject
        return existing_subject
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text (str): Text to split
            
        Returns:
            List[str]: List of sentences
        """
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _sentences_similar(self, sentence1: str, sentence2: str, threshold: float = 0.8) -> bool:
        """
        Check if two sentences are similar.
        
        Args:
            sentence1 (str): First sentence
            sentence2 (str): Second sentence
            threshold (float): Similarity threshold
            
        Returns:
            bool: True if sentences are similar
        """
        # Simple word overlap approach
        words1 = set(sentence1.lower().split())
        words2 = set(sentence2.lower().split())
        
        if not words1 or not words2:
            return sentence1.lower() == sentence2.lower()
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold

# Example usage
if __name__ == "__main__":
    merger = NoteMerger()
    
    # Example notes to merge
    existing_note = {
        'notes': 'A comma is a punctuation mark. It is used in lists.',
        'key_concepts': ['comma', 'punctuation'],
        'summary': 'Basic information about commas.',
        'confidence': 75,
        'source_image': 'image1.jpg',
        'subject': 'english'
    }
    
    new_note = {
        'notes': 'A comma is a punctuation mark used to separate elements in a list. It also separates clauses in complex sentences.',
        'key_concepts': ['comma', 'punctuation', 'clauses'],
        'summary': 'Detailed information about commas and their usage in English grammar.',
        'confidence': 85,
        'source_image': 'image2.jpg',
        'subject': 'english'
    }
    
    merged = merger.merge_notes(existing_note, new_note)
    print("Merged note:")
    for key, value in merged.items():
        print(f"  {key}: {value}")