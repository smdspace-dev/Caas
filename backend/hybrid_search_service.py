import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class HybridSearchService:
    """Enhanced vector service with hybrid search capabilities"""
    
    def __init__(self, 
                 db_path: str = "./chroma_db", 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize text splitter with multiple strategies
        self.text_splitters = {
            'recursive': RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            ),
            'semantic': RecursiveCharacterTextSplitter(
                chunk_size=int(chunk_size * 0.8),
                chunk_overlap=int(chunk_overlap * 1.5),
                length_function=len,
                separators=["\n\n", ". ", "! ", "? ", "\n", " ", ""]
            ),
            'paragraph': RecursiveCharacterTextSplitter(
                chunk_size=int(chunk_size * 1.2),
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n"]
            )
        }
        
        # Initialize TF-IDF for keyword search
        self.tfidf_vectorizers = {}  # Per chatbot
        self.tfidf_matrices = {}     # Per chatbot
        self.chunk_texts = {}        # Per chatbot
        
        logger.info(f"HybridSearchService initialized with model: {embedding_model}")
    
    def get_or_create_collection(self, chatbot_id: str) -> chromadb.Collection:
        """Get or create ChromaDB collection for a chatbot"""
        collection_name = f"chatbot_{chatbot_id}"
        
        try:
            collection = self.client.get_collection(collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")
        except Exception:
            # Create new collection
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"chatbot_id": chatbot_id, "created_at": str(datetime.now())}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        return collection
    
    def create_chunks_with_strategy(self, 
                                  text: str, 
                                  strategy: str = "recursive",
                                  preserve_metadata: bool = True) -> List[Dict[str, Any]]:
        """Create text chunks using specified strategy with enhanced metadata"""
        
        if strategy not in self.text_splitters:
            strategy = "recursive"
            logger.warning(f"Unknown chunking strategy, using default: {strategy}")
        
        splitter = self.text_splitters[strategy]
        chunks = splitter.split_text(text)
        
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'text': chunk,
                'chunk_index': i,
                'chunk_length': len(chunk),
                'word_count': len(chunk.split()),
                'strategy': strategy,
                'chunk_hash': self._generate_chunk_hash(chunk)
            }
            
            if preserve_metadata:
                # Add content analysis
                chunk_data.update(self._analyze_chunk(chunk))
            
            enhanced_chunks.append(chunk_data)
        
        return enhanced_chunks
    
    def _analyze_chunk(self, text: str) -> Dict[str, Any]:
        """Analyze chunk content for enhanced metadata"""
        analysis = {}
        
        # Basic statistics
        sentences = text.split('.')
        analysis['sentence_count'] = len([s for s in sentences if s.strip()])
        analysis['avg_sentence_length'] = len(text) / max(1, analysis['sentence_count'])
        
        # Content type detection
        if any(keyword in text.lower() for keyword in ['table', 'row', 'column', '|', '\t']):
            analysis['content_type'] = 'table'
        elif any(keyword in text.lower() for keyword in ['figure', 'image', 'chart', 'graph']):
            analysis['content_type'] = 'figure_reference'
        elif text.count('\n') > len(text) / 50:  # Many line breaks
            analysis['content_type'] = 'list'
        elif any(keyword in text.lower() for keyword in ['introduction', 'conclusion', 'summary']):
            analysis['content_type'] = 'section_header'
        else:
            analysis['content_type'] = 'paragraph'
        
        # Information density (ratio of unique words to total words)
        words = text.lower().split()
        unique_words = set(words)
        analysis['information_density'] = len(unique_words) / max(1, len(words))
        
        # Question detection
        analysis['has_questions'] = '?' in text
        analysis['question_count'] = text.count('?')
        
        return analysis
    
    def _generate_chunk_hash(self, text: str) -> str:
        """Generate unique hash for chunk deduplication"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def add_document_chunks(self, 
                          chatbot_id: str, 
                          document_id: str, 
                          chunks: List[Dict[str, Any]], 
                          document_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add document chunks to vector database with enhanced indexing"""
        
        collection = self.get_or_create_collection(chatbot_id)
        
        # Prepare data for ChromaDB
        chunk_ids = []
        chunk_texts = []
        chunk_embeddings = []
        chunk_metadatas = []
        
        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data['text']
            
            # Generate unique ID
            chunk_id = f"{document_id}_chunk_{i}_{chunk_data.get('chunk_hash', '')[:8]}"
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk_text)
            
            # Create embedding
            embedding = self.embedding_model.encode(chunk_text).tolist()
            chunk_embeddings.append(embedding)
            
            # Prepare metadata
            metadata = {
                'document_id': document_id,
                'chatbot_id': chatbot_id,
                'chunk_index': i,
                'chunk_length': len(chunk_text),
                'word_count': chunk_data.get('word_count', 0),
                'strategy': chunk_data.get('strategy', 'unknown'),
                'content_type': chunk_data.get('content_type', 'paragraph'),
                'information_density': chunk_data.get('information_density', 0.0),
                'created_at': str(datetime.now())
            }
            
            # Add document metadata if provided
            if document_metadata:
                metadata.update({
                    'document_filename': document_metadata.get('filename', ''),
                    'document_language': document_metadata.get('language', 'unknown'),
                    'document_quality': document_metadata.get('content_quality', 'unknown'),
                    'document_categories': json.dumps(document_metadata.get('content_categories', []))
                })
            
            chunk_metadatas.append(metadata)
        
        # Add to ChromaDB
        try:
            collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                embeddings=chunk_embeddings,
                metadatas=chunk_metadatas
            )
            
            # Update TF-IDF index for keyword search
            self._update_tfidf_index(chatbot_id, chunk_texts, chunk_ids)
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id}")
            
            return {
                'chunks_added': len(chunks),
                'chunk_ids': chunk_ids,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error adding chunks to collection: {str(e)}")
            raise
    
    def _update_tfidf_index(self, chatbot_id: str, new_texts: List[str], new_ids: List[str]):
        """Update TF-IDF index for keyword-based search"""
        try:
            # Initialize or update the corpus for this chatbot
            if chatbot_id not in self.chunk_texts:
                self.chunk_texts[chatbot_id] = {}
            
            # Add new texts
            for text, chunk_id in zip(new_texts, new_ids):
                self.chunk_texts[chatbot_id][chunk_id] = text
            
            # Rebuild TF-IDF matrix
            all_texts = list(self.chunk_texts[chatbot_id].values())
            all_ids = list(self.chunk_texts[chatbot_id].keys())
            
            if len(all_texts) > 0:
                vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95
                )
                
                tfidf_matrix = vectorizer.fit_transform(all_texts)
                
                self.tfidf_vectorizers[chatbot_id] = vectorizer
                self.tfidf_matrices[chatbot_id] = tfidf_matrix
                
                logger.info(f"Updated TF-IDF index for chatbot {chatbot_id}: {len(all_texts)} documents")
                
        except Exception as e:
            logger.error(f"Error updating TF-IDF index: {str(e)}")
    
    def hybrid_search(self, 
                     chatbot_id: str, 
                     query: str, 
                     top_k: int = 5,
                     semantic_weight: float = 0.7,
                     keyword_weight: float = 0.3,
                     filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search"""
        
        # Perform semantic search
        semantic_results = self.semantic_search(chatbot_id, query, top_k * 2, filter_metadata)
        
        # Perform keyword search
        keyword_results = self.keyword_search(chatbot_id, query, top_k * 2)
        
        # Combine and re-rank results
        combined_results = self._combine_search_results(
            semantic_results, keyword_results, 
            semantic_weight, keyword_weight, top_k
        )
        
        return combined_results
    
    def semantic_search(self, 
                       chatbot_id: str, 
                       query: str, 
                       top_k: int = 5,
                       filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perform semantic similarity search"""
        
        collection = self.get_or_create_collection(chatbot_id)
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Prepare where clause for filtering
        where_clause = {}
        if filter_metadata:
            where_clause.update(filter_metadata)
        
        try:
            # Query ChromaDB
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'semantic_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'search_type': 'semantic'
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    def keyword_search(self, chatbot_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword-based search using TF-IDF"""
        
        if chatbot_id not in self.tfidf_vectorizers:
            logger.warning(f"No TF-IDF index found for chatbot {chatbot_id}")
            return []
        
        try:
            vectorizer = self.tfidf_vectorizers[chatbot_id]
            tfidf_matrix = self.tfidf_matrices[chatbot_id]
            
            # Transform query
            query_vector = vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # Format results
            chunk_ids = list(self.chunk_texts[chatbot_id].keys())
            formatted_results = []
            
            for idx in top_indices:
                if similarities[idx] > 0:  # Only include non-zero similarities
                    chunk_id = chunk_ids[idx]
                    result = {
                        'id': chunk_id,
                        'text': self.chunk_texts[chatbot_id][chunk_id],
                        'keyword_score': float(similarities[idx]),
                        'search_type': 'keyword'
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            return []
    
    def _combine_search_results(self, 
                               semantic_results: List[Dict], 
                               keyword_results: List[Dict],
                               semantic_weight: float,
                               keyword_weight: float,
                               top_k: int) -> List[Dict[str, Any]]:
        """Combine and re-rank search results"""
        
        # Create a dictionary to combine results by ID
        combined = {}
        
        # Add semantic results
        for result in semantic_results:
            chunk_id = result['id']
            combined[chunk_id] = result.copy()
            combined[chunk_id]['combined_score'] = result.get('semantic_score', 0) * semantic_weight
        
        # Add/update with keyword results
        for result in keyword_results:
            chunk_id = result['id']
            if chunk_id in combined:
                # Update existing result
                combined[chunk_id]['keyword_score'] = result.get('keyword_score', 0)
                combined[chunk_id]['combined_score'] += result.get('keyword_score', 0) * keyword_weight
                combined[chunk_id]['search_type'] = 'hybrid'
            else:
                # Add new result (keyword only)
                combined[chunk_id] = result.copy()
                combined[chunk_id]['semantic_score'] = 0
                combined[chunk_id]['combined_score'] = result.get('keyword_score', 0) * keyword_weight
        
        # Sort by combined score and return top_k
        sorted_results = sorted(
            combined.values(), 
            key=lambda x: x['combined_score'], 
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    def get_collection_stats(self, chatbot_id: str) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            collection = self.get_or_create_collection(chatbot_id)
            count = collection.count()
            
            # Get sample of metadata for analysis
            if count > 0:
                sample_size = min(100, count)
                sample = collection.get(limit=sample_size, include=['metadatas'])
                
                # Analyze content types
                content_types = {}
                languages = {}
                qualities = {}
                
                for metadata in sample['metadatas']:
                    # Content types
                    content_type = metadata.get('content_type', 'unknown')
                    content_types[content_type] = content_types.get(content_type, 0) + 1
                    
                    # Languages
                    language = metadata.get('document_language', 'unknown')
                    languages[language] = languages.get(language, 0) + 1
                    
                    # Quality
                    quality = metadata.get('document_quality', 'unknown')
                    qualities[quality] = qualities.get(quality, 0) + 1
                
                return {
                    'total_chunks': count,
                    'content_types': content_types,
                    'languages': languages,
                    'quality_distribution': qualities,
                    'tfidf_indexed': chatbot_id in self.tfidf_vectorizers
                }
            else:
                return {
                    'total_chunks': 0,
                    'content_types': {},
                    'languages': {},
                    'quality_distribution': {},
                    'tfidf_indexed': False
                }
                
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}
    
    def delete_document_chunks(self, document_id: str, chatbot_id: str) -> Dict[str, Any]:
        """Delete all chunks for a specific document"""
        try:
            collection = self.get_or_create_collection(chatbot_id)
            
            # Get chunks for this document
            results = collection.get(
                where={"document_id": document_id},
                include=['ids']
            )
            
            chunk_ids = results['ids']
            
            if chunk_ids:
                # Delete from ChromaDB
                collection.delete(ids=chunk_ids)
                
                # Remove from TF-IDF index
                if chatbot_id in self.chunk_texts:
                    for chunk_id in chunk_ids:
                        self.chunk_texts[chatbot_id].pop(chunk_id, None)
                    
                    # Rebuild TF-IDF if there are remaining chunks
                    if self.chunk_texts[chatbot_id]:
                        remaining_texts = list(self.chunk_texts[chatbot_id].values())
                        self._update_tfidf_index(chatbot_id, remaining_texts, list(self.chunk_texts[chatbot_id].keys()))
                    else:
                        # Remove empty indexes
                        self.tfidf_vectorizers.pop(chatbot_id, None)
                        self.tfidf_matrices.pop(chatbot_id, None)
                        self.chunk_texts.pop(chatbot_id, None)
                
                logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
                
                return {
                    'chunks_deleted': len(chunk_ids),
                    'status': 'success'
                }
            else:
                return {
                    'chunks_deleted': 0,
                    'status': 'no_chunks_found'
                }
                
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            return {'error': str(e)}

# Factory function
def create_hybrid_search_service(db_path: str = "./chroma_db", 
                                embedding_model: str = "all-MiniLM-L6-v2") -> HybridSearchService:
    """Create hybrid search service instance"""
    return HybridSearchService(db_path=db_path, embedding_model=embedding_model)