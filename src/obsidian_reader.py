import os
import logging
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime
import frontmatter  # For parsing Markdown with frontmatter

class ObsidianReader:
    """
    Reader for importing notes from Obsidian vault into the vector database.
    """
    
    def __init__(self, vault_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Obsidian reader.
        
        Args:
            vault_path (str): Path to the Obsidian vault
            config (Dict[str, Any], optional): Configuration dictionary
        """
        self.vault_path = vault_path
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Validate vault path
        if not os.path.exists(self.vault_path):
            raise ValueError(f"Obsidian vault path does not exist: {self.vault_path}")
        
        self.logger.info(f"Initialized ObsidianReader for vault: {self.vault_path}")
    
    def scan_vault(self, folders: Optional[List[str]] = None) -> List[str]:
        """
        Scan the Obsidian vault for markdown files.
        
        Args:
            folders (List[str], optional): Specific folders to scan. If None, scan all folders.
            
        Returns:
            List[str]: List of markdown file paths
        """
        markdown_files = []
        
        try:
            # Determine which directories to scan
            if folders:
                scan_paths = [os.path.join(self.vault_path, folder) for folder in folders]
            else:
                scan_paths = [self.vault_path]
            
            # Scan for markdown files
            for scan_path in scan_paths:
                if os.path.exists(scan_path):
                    for root, _, files in os.walk(scan_path):
                        for file in files:
                            if file.endswith('.md') and not file.startswith('.'):
                                file_path = os.path.join(root, file)
                                markdown_files.append(file_path)
                else:
                    self.logger.warning(f"Scan path does not exist: {scan_path}")
            
            self.logger.info(f"Found {len(markdown_files)} markdown files in vault")
            return markdown_files
            
        except Exception as e:
            self.logger.error(f"Error scanning vault: {str(e)}")
            return []
    
    def read_note(self, file_path: str) -> Dict[str, Any]:
        """
        Read and parse a single Obsidian note.
        
        Args:
            file_path (str): Path to the markdown file
            
        Returns:
            Dict[str, Any]: Parsed note content and metadata
        """
        try:
            # Get file metadata
            stat = os.stat(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter if present
            try:
                post = frontmatter.loads(content)
                metadata = post.metadata
                body = post.content
            except Exception:
                # If frontmatter parsing fails, treat entire content as body
                metadata = {}
                body = content
            
            # Extract title from filename or frontmatter
            title = metadata.get('title') or os.path.splitext(os.path.basename(file_path))[0]
            
            # Remove leading/trailing whitespace
            body = body.strip()
            
            note_data = {
                'title': title,
                'content': body,
                'file_path': file_path,
                'file_hash': file_hash,
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'metadata': metadata
            }
            
            self.logger.debug(f"Read note: {title} from {file_path}")
            return note_data
            
        except Exception as e:
            self.logger.error(f"Error reading note {file_path}: {str(e)}")
            return {}
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of a file for change detection.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            str: SHA256 hash of the file
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.warning(f"Error calculating file hash for {file_path}: {str(e)}")
            return ""
    
    def filter_notes_by_tags(self, notes: List[Dict[str, Any]], 
                           required_tags: Optional[List[str]] = None,
                           excluded_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Filter notes based on tags in their metadata.
        
        Args:
            notes (List[Dict[str, Any]]): List of parsed notes
            required_tags (List[str], optional): Tags that must be present
            excluded_tags (List[str], optional): Tags that must not be present
            
        Returns:
            List[Dict[str, Any]]: Filtered list of notes
        """
        if not required_tags and not excluded_tags:
            return notes
        
        filtered_notes = []
        
        for note in notes:
            note_tags = note.get('metadata', {}).get('tags', [])
            if isinstance(note_tags, str):
                note_tags = [note_tags]
            elif not isinstance(note_tags, list):
                note_tags = []
            
            # Check required tags
            if required_tags:
                has_all_required = all(tag in note_tags for tag in required_tags)
                if not has_all_required:
                    continue
            
            # Check excluded tags
            if excluded_tags:
                has_excluded = any(tag in note_tags for tag in excluded_tags)
                if has_excluded:
                    continue
            
            filtered_notes.append(note)
        
        return filtered_notes

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example: Initialize reader with vault path from config
    vault_path = "/Users/tianruijia/Library/Mobile Documents/iCloud~md~obsidian/Documents/SAT&ACT Prepare"
    
    try:
        reader = ObsidianReader(vault_path)
        
        # Scan for markdown files
        markdown_files = reader.scan_vault()
        print(f"Found {len(markdown_files)} markdown files")
        
        # Read first few notes as examples
        for file_path in markdown_files[:3]:
            note = reader.read_note(file_path)
            if note:
                print(f"Title: {note['title']}")
                print(f"Content preview: {note['content'][:100]}...")
                print("---")
                
    except Exception as e:
        print(f"Error: {e}")