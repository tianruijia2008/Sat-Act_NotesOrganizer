import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import os
import logging
from typing import List, Dict, Optional, Tuple
import json

class VectorDatabase:
    """
    Vector database for storing and searching note embeddings.
    Uses ChromaDB for vector storage and Sentence Transformers for embeddings.
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the vector database.
        
        Args:
            persist_directory (str): Directory to persist the database. 
                                   If None, uses default data/vector_db
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up persistence directory
        if persist_directory is None:
            persist_directory = os.path.join(os.path.dirname(__file__), '..', 'data', 'vector_db')
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize sentence transformer model for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name="sat_act_notes",
            embedding_function=None  # We'll compute embeddings manually
        )
        
        self.logger.info("Vector database initialized successfully")
    
    def add_note_embedding(self, note_id: str, content: str, metadata: Dict = None) -> bool:
        """
        Add a note's embedding to the database.
        
        Args:
            note_id (str): Unique identifier for the note
            content (str): Content of the note to embed
            metadata (Dict): Additional metadata about the note
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate embedding
            embedding = self.embedding_model.encode([content]).tolist()
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            # Add to collection
            self.collection.add(
                ids=[note_id],
                embeddings=embedding,
                documents=[content],
                metadatas=[metadata]
            )
            
            self.logger.info(f"Successfully added note {note_id} to vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding note {note_id} to vector database: {str(e)}")
            return False
    
    def find_similar_notes(self, content: str, threshold: float = 0.8, top_k: int = 5) -> List[Dict]:
        """
        Find similar notes based on semantic similarity.
        
        Args:
            content (str): Content to search for similar notes
            threshold (float): Minimum similarity threshold (0-1)
            top_k (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of similar notes with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([content]).tolist()
            
            # Search for similar notes
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            similar_notes = []
            if results['ids'] and results['ids'][0]:
                for i, note_id in enumerate(results['ids'][0]):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity = 1 - results['distances'][0][i]
                    
                    # Only include notes above threshold
                    if similarity >= threshold:
                        similar_notes.append({
                            'id': note_id,
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity': similarity
                        })
            
            self.logger.info(f"Found {len(similar_notes)} similar notes")
            return similar_notes
            
        except Exception as e:
            self.logger.error(f"Error finding similar notes: {str(e)}")
            return []
    
    def update_note_embedding(self, note_id: str, new_content: str, metadata: Dict = None) -> bool:
        """
        Update an existing note's embedding.
        
        Args:
            note_id (str): Unique identifier for the note
            new_content (str): New content of the note
            metadata (Dict): Updated metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove existing note
            self.collection.delete(ids=[note_id])
            
            # Add updated note
            return self.add_note_embedding(note_id, new_content, metadata)
            
        except Exception as e:
            self.logger.error(f"Error updating note {note_id}: {str(e)}")
            return False
    
    def delete_note_embedding(self, note_id: str) -> bool:
        """
        Delete a note's embedding from the database.
        
        Args:
            note_id (str): Unique identifier for the note
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[note_id])
            self.logger.info(f"Successfully deleted note {note_id} from vector database")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting note {note_id}: {str(e)}")
            return False
    
    def get_note_count(self) -> int:
        """
        Get the total number of notes in the database.
        
        Returns:
            int: Number of notes in the database
        """
        try:
            return self.collection.count()
        except Exception as e:
            self.logger.error(f"Error getting note count: {str(e)}")
            return 0

# Example usage
if __name__ == "__main__":
    # Create vector database instance
    vector_db = VectorDatabase()
    
    # Add some sample notes
    vector_db.add_note_embedding(
        note_id="note_1", 
        content="Commas are punctuation marks used to separate elements in a list.",
        metadata={"subject": "english", "type": "grammar"}
    )
    
    vector_db.add_note_embedding(
        note_id="note_2", 
        content="The comma is a punctuation mark that separates parts of a sentence.",
        metadata={"subject": "english", "type": "grammar"}
    )
    
    # Search for similar notes
    similar = vector_db.find_similar_notes(
        "What is a comma and how is it used in English grammar?",
        threshold=0.5
    )
    
    print(f"Found {len(similar)} similar notes:")
    for note in similar:
        print(f"  ID: {note['id']}, Similarity: {note['similarity']:.3f}")
        print(f"  Content: {note['content'][:100]}...")
        print()