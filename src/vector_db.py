import os
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding

# Local imports
from src.obsidian_reader import ObsidianReader

class VectorDB:
    """
    Vector database for storing and retrieving OCR-extracted text using LlamaIndex.
    """
    
    def __init__(self, storage_path: str = "data/vector_db", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the vector database.
        
        Args:
            storage_path (str): Path to store the vector database
            config (Dict[str, Any], optional): Configuration dictionary
        """
        self.storage_path = storage_path
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize vector store
        self._init_vector_store()
        
        # Initialize Obsidian reader if vault path is provided
        self.obsidian_reader = None
        obsidian_vault_path = self.config.get('obsidian_vault_path')
        if obsidian_vault_path and os.path.exists(obsidian_vault_path):
            self.obsidian_reader = ObsidianReader(obsidian_vault_path, self.config)
        
    def _init_vector_store(self):
        """
        Initialize the vector store, loading existing data if available.
        """
        try:
            # Initialize embedding model
            # Use a local embedding model to avoid API key requirements
            embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
            
            # Try to load existing index
            storage_context = StorageContext.from_defaults(persist_dir=self.storage_path)
            self.index = load_index_from_storage(storage_context, embed_model=embed_model)
            self.logger.info(f"Loaded existing vector database from {self.storage_path}")
        except Exception as e:
            # Create new index if loading fails
            self.logger.info(f"Creating new vector database at {self.storage_path}")
            
            # Initialize embedding model
            embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
            
            self.index = VectorStoreIndex(nodes=[], embed_model=embed_model)
            
    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a document to the vector database.
        
        Args:
            text (str): The document text to store
            metadata (Dict[str, Any], optional): Metadata to associate with the document
            
        Returns:
            str: The document ID
        """
        try:
            # Create a unique document ID
            doc_id = str(uuid4())
            
            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata["doc_id"] = doc_id
            doc_metadata["created_at"] = datetime.now().isoformat()
            
            # Create TextNode
            node = TextNode(
                id_=doc_id,
                text=text,
                metadata=doc_metadata
            )
            
            # Add to index
            self.index.insert_nodes([node])
            
            # Persist the index
            self.index.storage_context.persist(persist_dir=self.storage_path)
            
            self.logger.info(f"Successfully added document {doc_id} to vector database")
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Error adding document to vector database: {str(e)}")
            raise
            
    def query_similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the vector database for similar documents.
        
        Args:
            query_text (str): The query text
            top_k (int): Number of similar documents to return
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with their metadata
        """
        try:
            # Use retriever directly to avoid LLM dependency
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            
            # Perform similarity search
            nodes = retriever.retrieve(query_text)
            
            # Extract similar documents
            similar_docs = []
            for node in nodes:
                doc_info = {
                    "id": node.node_id,
                    "text": node.text,
                    "metadata": node.metadata,
                    "similarity_score": node.score if hasattr(node, 'score') else None
                }
                similar_docs.append(doc_info)
            
            self.logger.info(f"Found {len(similar_docs)} similar documents")
            return similar_docs
            
        except Exception as e:
            self.logger.error(f"Error querying similar documents: {str(e)}")
            return []
            
    def query_by_metadata(self, metadata_filter: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the vector database for documents matching specific metadata.
        
        Args:
            metadata_filter (Dict[str, Any]): Metadata key-value pairs to filter by
            top_k (int): Number of documents to return
            
        Returns:
            List[Dict[str, Any]]: List of matching documents with their metadata
        """
        try:
            # This is a simplified implementation
            # In a production system, you would use LlamaIndex's filtering capabilities
            all_docs = []  # This would need to be implemented properly
            
            # Filter documents by metadata
            filtered_docs = []
            for doc in all_docs:
                match = True
                for key, value in metadata_filter.items():
                    if doc["metadata"].get(key) != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
                    
            # Sort by some relevance metric and return top_k
            # This is a placeholder implementation
            result = filtered_docs[:top_k]
            
            self.logger.info(f"Found {len(result)} documents matching metadata filter")
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying documents by metadata: {str(e)}")
            return []
            
    def get_similar_by_metadata(self, query_text: str, metadata_filter: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query for similar documents with metadata filtering.
        
        Args:
            query_text (str): The query text
            metadata_filter (Dict[str, Any]): Metadata key-value pairs to filter by
            top_k (int): Number of documents to return
            
        Returns:
            List[Dict[str, Any]]: List of similar documents with their metadata
        """
        try:
            # First get similar documents
            similar_docs = self.query_similar(query_text, top_k * 2)  # Get more candidates
            
            # Then filter by metadata
            filtered_docs = []
            for doc in similar_docs:
                match = True
                for key, value in metadata_filter.items():
                    if doc["metadata"].get(key) != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
                    
            # Return top_k results
            result = filtered_docs[:top_k]
            
            self.logger.info(f"Found {len(result)} similar documents matching metadata filter")
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying similar documents with metadata filter: {str(e)}")
            return []
            
    def update_document(self, doc_id: str, new_text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing document in the vector database.
        
        Args:
            doc_id (str): The document ID to update
            new_text (str): The new text content
            metadata (Dict[str, Any], optional): Updated metadata
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # First, we need to remove the old document and add a new one
            # LlamaIndex doesn't directly support document updates, so we simulate it
            
            # Get the existing document metadata if not provided
            existing_metadata = {}
            if metadata is None:
                # Try to retrieve existing document to get metadata
                # This is a simplified approach - in practice, you might want to store
                # metadata separately for easier retrieval
                similar_docs = self.query_similar(new_text, top_k=10)
                for doc in similar_docs:
                    if doc["id"] == doc_id:
                        existing_metadata = doc["metadata"]
                        break
            
            # Merge metadata
            updated_metadata = existing_metadata.copy()
            if metadata:
                updated_metadata.update(metadata)
            updated_metadata["updated_at"] = datetime.now().isoformat()
            
            # Remove old document (simplified approach)
            # In a production system, you would want a more robust method
            
            # Add updated document
            new_doc_id = self.add_document(new_text, updated_metadata)
            
            self.logger.info(f"Updated document {doc_id} (new ID: {new_doc_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating document {doc_id}: {str(e)}")
            return False
            
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id (str): The document ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The document information or None if not found
        """
        try:
            # Query with a filter for the specific document ID
            # This is a simplified approach - in practice, you might want to implement
            # a more direct retrieval method
            
            # For now, we'll use a workaround by querying for content that should be unique
            # and then filtering by ID
            # In a real implementation, you would store document IDs in a separate lookup
            
            return None  # Placeholder implementation
            
        except Exception as e:
            self.logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            return None
            
    def get_document_count(self) -> int:
        """
        Get the total number of documents in the vector database.
        
        Returns:
            int: The number of documents
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you might want to track this separately
            return len(self.index.ref_doc_info) if hasattr(self.index, 'ref_doc_info') else 0
        except Exception as e:
            self.logger.error(f"Error getting document count: {str(e)}")
            return 0
            
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the vector database.
        
        Args:
            doc_id (str): The document ID to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # LlamaIndex doesn't directly support document deletion
            # This is a placeholder implementation
            self.logger.warning(f"Document deletion not implemented (doc_id: {doc_id})")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return False
            
    def import_from_obsidian(self, folders: Optional[List[str]] = None, 
                           required_tags: Optional[List[str]] = None,
                           excluded_tags: Optional[List[str]] = None) -> int:
        """
        Import notes from Obsidian vault into the vector database.
        
        Args:
            folders (List[str], optional): Specific folders to import from
            required_tags (List[str], optional): Only import notes with these tags
            excluded_tags (List[str], optional): Skip notes with these tags
            
        Returns:
            int: Number of notes successfully imported
        """
        if not self.obsidian_reader:
            self.logger.warning("Obsidian reader not initialized. Cannot import notes.")
            return 0
            
        try:
            imported_count = 0
            
            # Scan vault for markdown files
            markdown_files = self.obsidian_reader.scan_vault(folders)
            
            if not markdown_files:
                self.logger.info("No markdown files found in Obsidian vault.")
                return 0
            
            # Read and process each note
            for file_path in markdown_files:
                try:
                    # Read the note
                    note_data = self.obsidian_reader.read_note(file_path)
                    
                    if not note_data or not note_data.get('content'):
                        continue
                    
                    # Filter by tags if specified
                    if required_tags or excluded_tags:
                        filtered_notes = self.obsidian_reader.filter_notes_by_tags(
                            [note_data], required_tags, excluded_tags
                        )
                        if not filtered_notes:
                            continue
                    
                    # Prepare metadata
                    metadata = {
                        "source": "obsidian",
                        "file_path": file_path,
                        "title": note_data.get('title', ''),
                        "created_time": note_data.get('created_time', ''),
                        "modified_time": note_data.get('modified_time', ''),
                        "file_hash": note_data.get('file_hash', ''),
                        "obsidian_metadata": note_data.get('metadata', {})
                    }
                    
                    # Add to vector database
                    doc_id = self.add_document(note_data['content'], metadata)
                    if doc_id:
                        imported_count += 1
                        self.logger.debug(f"Imported Obsidian note: {note_data['title']}")
                        
                except Exception as e:
                    self.logger.warning(f"Error processing Obsidian note {file_path}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully imported {imported_count} notes from Obsidian vault")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"Error importing from Obsidian: {str(e)}")
            return 0
            
    def sync_obsidian_changes(self) -> int:
        """
        Sync changes from Obsidian vault (incremental update).
        This method checks for modified files and updates them in the vector database.
        
        Returns:
            int: Number of notes updated
        """
        # This is a simplified implementation
        # In a full implementation, you would track file hashes and only update changed files
        self.logger.info("Syncing Obsidian changes...")
        return self.import_from_obsidian()

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize vector database with config
    config = {
        "obsidian_vault_path": "/Users/tianruijia/Library/Mobile Documents/iCloud~md~obsidian/Documents/SAT&ACT Prepare"
    }
    vector_db = VectorDB(config=config)
    
    # Add sample documents
    doc1_id = vector_db.add_document(
        "The quadratic formula is x = (-b ± √(b² - 4ac)) / (2a)",
        {"subject": "math", "topic": "algebra", "type": "formula", "source": "ocr"}
    )
    
    doc2_id = vector_db.add_document(
        "To solve quadratic equations, first try factoring, then use the quadratic formula if factoring doesn't work",
        {"subject": "math", "topic": "algebra", "type": "technique", "source": "ocr"}
    )
    
    # Query for similar documents
    similar_docs = vector_db.query_similar("How to solve quadratic equations?", top_k=2)
    print("Similar documents:")
    for doc in similar_docs:
        print(f"  ID: {doc['id']}")
        print(f"  Text: {doc['text'][:100]}...")
        print(f"  Metadata: {doc['metadata']}")
        print()
    
    # Import from Obsidian if reader is available
    if vector_db.obsidian_reader:
        print("Importing from Obsidian...")
        imported_count = vector_db.import_from_obsidian()
        print(f"Imported {imported_count} notes from Obsidian")