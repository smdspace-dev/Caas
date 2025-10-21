import os
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
import numpy as np
import uuid
from pathlib import Path

class VectorService:
    """Handle text chunking, embeddings, and vector storage"""
    
    def __init__(self, persist_directory: str = "./data/chroma_db", use_openai: bool = False):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.use_openai = use_openai
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        if use_openai and os.getenv('OPENAI_API_KEY'):
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
            self.embedding_dimension = 1536
        else:
            # Use local sentence transformer model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dimension = 384
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create chunk objects with metadata
            chunk_objects = []
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_obj = {
                    "id": chunk_id,
                    "text": chunk,
                    "chunk_index": i,
                    "metadata": metadata or {}
                }
                chunk_objects.append(chunk_obj)
            
            return chunk_objects
            
        except Exception as e:
            raise Exception(f"Error chunking text: {str(e)}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            if self.use_openai and hasattr(self, 'embeddings'):
                # Use OpenAI embeddings
                embeddings = self.embeddings.embed_documents(texts)
                return embeddings
            else:
                # Use local sentence transformer
                embeddings = self.embedding_model.encode(texts)
                return embeddings.tolist()
                
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    def get_or_create_collection(self, chatbot_id: str) -> Any:
        """Get or create ChromaDB collection for chatbot"""
        try:
            collection_name = f"chatbot_{chatbot_id}"
            
            # Try to get existing collection
            try:
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=None  # We'll provide embeddings manually
                )
            except ValueError:
                # Collection doesn't exist, create it
                collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=None,
                    metadata={"chatbot_id": chatbot_id}
                )
            
            return collection
            
        except Exception as e:
            raise Exception(f"Error accessing collection: {str(e)}")
    
    def store_chunks(self, chunks: List[Dict[str, Any]], chatbot_id: str, document_id: str) -> Dict[str, Any]:
        """Store text chunks in vector database"""
        try:
            if not chunks:
                return {"success": False, "error": "No chunks to store"}
            
            collection = self.get_or_create_collection(chatbot_id)
            
            # Extract texts for embedding
            texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Prepare data for ChromaDB
            ids = [chunk["id"] for chunk in chunks]
            metadatas = []
            
            for chunk in chunks:
                metadata = {
                    "document_id": document_id,
                    "chatbot_id": chatbot_id,
                    "chunk_index": chunk["chunk_index"],
                    **chunk.get("metadata", {})
                }
                metadatas.append(metadata)
            
            # Store in ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "chunks_stored": len(chunks),
                "collection_name": collection.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def similarity_search(self, query: str, chatbot_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            collection = self.get_or_create_collection(chatbot_id)
            
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search for similar chunks
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    result = {
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if results['distances'] else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            raise Exception(f"Error in similarity search: {str(e)}")
    
    def delete_document_chunks(self, document_id: str, chatbot_id: str) -> Dict[str, Any]:
        """Delete all chunks for a specific document"""
        try:
            collection = self.get_or_create_collection(chatbot_id)
            
            # Get all chunks for this document
            results = collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if results['ids']:
                # Delete the chunks
                collection.delete(ids=results['ids'])
                return {
                    "success": True,
                    "deleted_chunks": len(results['ids'])
                }
            else:
                return {
                    "success": True,
                    "deleted_chunks": 0,
                    "message": "No chunks found for document"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_collection_stats(self, chatbot_id: str) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            collection = self.get_or_create_collection(chatbot_id)
            count = collection.count()
            
            return {
                "collection_name": collection.name,
                "total_chunks": count,
                "embedding_dimension": self.embedding_dimension,
                "model_type": "openai" if self.use_openai else "sentence-transformer"
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }