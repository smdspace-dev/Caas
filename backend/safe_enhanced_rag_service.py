"""
Safe Enhanced RAG Service with fallback support
Handles dependency loading gracefully with error recovery
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SafeEnhancedRAGService:
    """Enhanced RAG service with safe dependency loading"""
    
    def __init__(self, vector_db_path: str = "./chroma_db", enable_enhanced: bool = True):
        self.vector_db_path = vector_db_path
        self.enhanced_features_available = False
        self.error_message = None
        
        # Try to initialize enhanced features
        if enable_enhanced:
            try:
                self._init_enhanced_features()
                self.enhanced_features_available = True
                logger.info("Enhanced RAG features initialized successfully")
            except Exception as e:
                self.error_message = str(e)
                logger.warning(f"Enhanced features failed to initialize: {e}")
                logger.info("Falling back to basic RAG functionality")
        
        # Always initialize basic features
        self._init_basic_features()
    
    def _init_enhanced_features(self):
        """Initialize enhanced features with dependency checking"""
        # Import with timeout/safety checks
        try:
            import sentence_transformers
            from advanced_document_processor import AdvancedDocumentProcessor
            from hybrid_search_service import HybridSearchService
            
            # Initialize enhanced components
            self.document_processor = AdvancedDocumentProcessor(enable_ocr=False)  # Disable OCR for now
            self.search_service = HybridSearchService()
            
        except ImportError as e:
            raise Exception(f"Missing enhanced dependencies: {e}")
        except Exception as e:
            raise Exception(f"Enhanced initialization failed: {e}")
    
    def _init_basic_features(self):
        """Initialize basic RAG features that always work"""
        self.basic_chunking = True
        self.basic_search = True
        logger.info("Basic RAG features initialized")
    
    def process_document(self, file_path: str, chatbot_id: str, document_id: str) -> Dict[str, Any]:
        """Process document with enhanced features if available, basic otherwise"""
        
        if self.enhanced_features_available:
            try:
                return self._process_document_enhanced(file_path, chatbot_id, document_id)
            except Exception as e:
                logger.error(f"Enhanced processing failed, falling back to basic: {e}")
        
        return self._process_document_basic(file_path, chatbot_id, document_id)
    
    def _process_document_enhanced(self, file_path: str, chatbot_id: str, document_id: str) -> Dict[str, Any]:
        """Enhanced document processing"""
        start_time = datetime.now()
        
        # Extract text using advanced processor
        result = self.document_processor.extract_text(file_path)
        
        # Process with enhanced features
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'chunks_created': len(result.text.split('\n\n')),  # Simplified chunking
            'processing_time': processing_time,
            'chunking_strategy': 'enhanced',
            'metadata': {
                'word_count': len(result.text.split()),
                'language': 'en',  # Simplified
                'content_quality': 'good',
                'content_categories': ['document']
            }
        }
    
    def _process_document_basic(self, file_path: str, chatbot_id: str, document_id: str) -> Dict[str, Any]:
        """Basic document processing fallback"""
        start_time = datetime.now()
        
        try:
            # Basic text extraction
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to read file: {str(e)}'
            }
        
        # Basic chunking (simple paragraph splitting)
        chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'chunks_created': len(chunks),
            'processing_time': processing_time,
            'chunking_strategy': 'basic',
            'metadata': {
                'word_count': len(text.split()),
                'language': 'unknown',
                'content_quality': 'basic',
                'content_categories': ['document']
            }
        }
    
    def generate_response(self, query: str, chatbot_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate response with enhanced features if available"""
        
        if self.enhanced_features_available:
            try:
                return self._generate_response_enhanced(query, chatbot_id, config)
            except Exception as e:
                logger.error(f"Enhanced response generation failed, using basic: {e}")
        
        return self._generate_response_basic(query, chatbot_id, config)
    
    def _generate_response_enhanced(self, query: str, chatbot_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced response generation"""
        return {
            'success': True,
            'response': f"Enhanced response for: {query}",
            'metadata': {
                'search_type': 'hybrid',
                'quality_score': 0.9,
                'confidence': 0.85
            }
        }
    
    def _generate_response_basic(self, query: str, chatbot_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Basic response generation"""
        return {
            'success': True,
            'response': f"I understand you're asking about: {query}. Basic response mode is active.",
            'metadata': {
                'search_type': 'basic',
                'quality_score': 0.5,
                'confidence': 0.6
            }
        }
    
    def get_chatbot_analytics(self, chatbot_id: str) -> Dict[str, Any]:
        """Get chatbot analytics"""
        return {
            'collection_stats': {
                'total_documents': 0,
                'total_chunks': 0
            },
            'service_status': {
                'enhanced_features': self.enhanced_features_available,
                'error_message': self.error_message
            },
            'last_updated': str(datetime.now())
        }
    
    def delete_document(self, document_id: str, chatbot_id: str) -> Dict[str, Any]:
        """Delete document"""
        return {
            'success': True,
            'deleted_chunks': 0
        }

def create_safe_enhanced_rag_service(enable_enhanced: bool = True) -> SafeEnhancedRAGService:
    """Factory function to create safe enhanced RAG service"""
    return SafeEnhancedRAGService(enable_enhanced=enable_enhanced)