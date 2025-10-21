import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import time
from datetime import datetime

# Import our enhanced services
from advanced_document_processor import create_processor, DocumentMetadata, ProcessingResult
from hybrid_search_service import create_hybrid_search_service
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Enhanced RAG service with advanced document processing and hybrid search"""
    
    def __init__(self, 
                 vector_db_path: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 enable_openai: bool = True,
                 enable_ocr: bool = True,
                 chunking_strategy: str = "semantic"):
        
        # Initialize components
        self.document_processor = create_processor(
            enable_ocr=enable_ocr, 
            extract_images=True
        )
        
        self.search_service = create_hybrid_search_service(
            db_path=vector_db_path,
            embedding_model=embedding_model
        )
        
        self.chunking_strategy = chunking_strategy
        self.enable_openai = enable_openai
        
        # OpenAI configuration
        if enable_openai and os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_available = True
            logger.info("OpenAI API configured")
        else:
            self.openai_available = False
            logger.warning("OpenAI API not available, using template responses")
        
        # Enhanced response templates with context awareness
        self.response_templates = {
            'no_context': [
                "I don't have specific information about '{query}' in the uploaded documents. Could you provide more details or upload relevant documents?",
                "Based on the available documents, I couldn't find information related to '{query}'. You might want to upload additional documents or rephrase your question.",
                "I don't see any relevant information about '{query}' in the current knowledge base. Try asking about topics covered in your uploaded documents."
            ],
            'partial_context': [
                "I found some information related to '{query}' in the documents. {context}",
                "Based on the available documents: {context}",
                "Here's what I found about '{query}': {context}"
            ],
            'good_context': [
                "Based on your documents, here's the information about '{query}': {context}",
                "According to the uploaded documents: {context}",
                "I found detailed information about '{query}': {context}"
            ],
            'technical_content': [
                "According to the technical documentation: {context}",
                "Based on the technical information provided: {context}"
            ],
            'business_content': [
                "Based on the business documents: {context}",
                "According to the business information: {context}"
            ]
        }
        
        logger.info(f"EnhancedRAGService initialized with strategy: {chunking_strategy}")
    
    def process_document(self, 
                        file_path: str, 
                        chatbot_id: str, 
                        document_id: str,
                        custom_chunking: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process document with enhanced analysis and chunking"""
        
        start_time = time.time()
        
        try:
            # Validate file
            file_size = os.path.getsize(file_path)
            is_valid, validation_msg = self.document_processor.validate_file(file_path, file_size)
            
            if not is_valid:
                return {
                    'success': False,
                    'error': validation_msg,
                    'processing_time': time.time() - start_time
                }
            
            # Extract text with advanced processing
            processing_result = self.document_processor.extract_text(file_path)
            
            if processing_result.errors:
                logger.warning(f"Processing warnings for {file_path}: {processing_result.errors}")
            
            if not processing_result.text.strip():
                return {
                    'success': False,
                    'error': 'No text content could be extracted from the document',
                    'processing_time': time.time() - start_time,
                    'metadata': processing_result.metadata.__dict__
                }
            
            # Determine chunking strategy based on document analysis
            strategy = self._select_chunking_strategy(processing_result.metadata, custom_chunking)
            
            # Create chunks with enhanced metadata
            chunks = self.search_service.create_chunks_with_strategy(
                text=processing_result.text,
                strategy=strategy,
                preserve_metadata=True
            )
            
            # Add document chunks to vector database
            doc_metadata = processing_result.metadata.__dict__
            indexing_result = self.search_service.add_document_chunks(
                chatbot_id=chatbot_id,
                document_id=document_id,
                chunks=chunks,
                document_metadata=doc_metadata
            )
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'chunks_created': len(chunks),
                'processing_time': processing_time,
                'metadata': doc_metadata,
                'chunking_strategy': strategy,
                'indexing_result': indexing_result,
                'document_analysis': {
                    'word_count': processing_result.metadata.word_count,
                    'language': processing_result.metadata.language,
                    'readability_score': processing_result.metadata.readability_score,
                    'content_quality': processing_result.metadata.content_quality,
                    'content_categories': processing_result.metadata.content_categories,
                    'has_images': processing_result.metadata.has_images,
                    'has_tables': processing_result.metadata.has_tables
                },
                'extracted_elements': {
                    'images': len(processing_result.images) if processing_result.images else 0,
                    'tables': len(processing_result.tables) if processing_result.tables else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _select_chunking_strategy(self, 
                                 metadata: DocumentMetadata, 
                                 custom_chunking: Dict[str, Any] = None) -> str:
        """Select optimal chunking strategy based on document characteristics"""
        
        if custom_chunking and custom_chunking.get('strategy'):
            return custom_chunking['strategy']
        
        # Strategy selection logic based on document analysis
        if metadata.content_categories:
            if 'technical' in metadata.content_categories:
                return 'semantic'  # Better for preserving technical context
            elif 'legal' in metadata.content_categories:
                return 'paragraph'  # Preserve legal structure
            elif 'academic' in metadata.content_categories:
                return 'semantic'  # Better for research content
        
        # Based on document structure
        if metadata.has_tables:
            return 'paragraph'  # Preserve table structure
        
        # Based on readability
        if metadata.readability_score < 30:  # Very difficult text
            return 'semantic'  # Smaller, more focused chunks
        elif metadata.readability_score > 80:  # Easy text
            return 'recursive'  # Standard chunking
        
        # Default strategy
        return self.chunking_strategy
    
    def query_with_context(self, 
                          chatbot_id: str, 
                          query: str,
                          search_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced query processing with context-aware responses"""
        
        start_time = time.time()
        
        # Default search parameters
        default_params = {
            'top_k': 5,
            'semantic_weight': 0.7,
            'keyword_weight': 0.3,
            'min_similarity_threshold': 0.3
        }
        
        if search_params:
            default_params.update(search_params)
        
        try:
            # Perform hybrid search
            search_results = self.search_service.hybrid_search(
                chatbot_id=chatbot_id,
                query=query,
                top_k=default_params['top_k'],
                semantic_weight=default_params['semantic_weight'],
                keyword_weight=default_params['keyword_weight']
            )
            
            # Filter by similarity threshold
            min_threshold = default_params['min_similarity_threshold']
            filtered_results = [
                r for r in search_results 
                if r.get('combined_score', 0) >= min_threshold or 
                   r.get('semantic_score', 0) >= min_threshold
            ]
            
            # Analyze context quality
            context_analysis = self._analyze_context_quality(filtered_results, query)
            
            # Generate response
            response = self._generate_enhanced_response(
                query=query,
                context_results=filtered_results,
                context_analysis=context_analysis
            )
            
            query_time = time.time() - start_time
            
            return {
                'response': response,
                'context_used': len(filtered_results) > 0,
                'context_quality': context_analysis['quality_level'],
                'sources_count': len(filtered_results),
                'search_results': filtered_results,
                'query_time': query_time,
                'search_params': default_params,
                'analysis': context_analysis
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'response': f"I'm sorry, I encountered an error while processing your question: {str(e)}",
                'context_used': False,
                'error': str(e),
                'query_time': time.time() - start_time
            }
    
    def _analyze_context_quality(self, search_results: List[Dict], query: str) -> Dict[str, Any]:
        """Analyze the quality and relevance of retrieved context"""
        
        if not search_results:
            return {
                'quality_level': 'no_context',
                'relevance_score': 0.0,
                'context_diversity': 0,
                'content_types': [],
                'document_sources': 0
            }
        
        # Calculate average relevance
        total_score = sum(r.get('combined_score', r.get('semantic_score', 0)) for r in search_results)
        avg_relevance = total_score / len(search_results)
        
        # Analyze content diversity
        content_types = set()
        document_sources = set()
        
        for result in search_results:
            metadata = result.get('metadata', {})
            if metadata.get('content_type'):
                content_types.add(metadata['content_type'])
            if metadata.get('document_id'):
                document_sources.add(metadata['document_id'])
        
        # Determine quality level
        if avg_relevance >= 0.7:
            quality_level = 'good_context'
        elif avg_relevance >= 0.4:
            quality_level = 'partial_context'
        else:
            quality_level = 'no_context'
        
        # Check for specialized content
        categories = []
        for result in search_results:
            metadata = result.get('metadata', {})
            doc_categories = metadata.get('document_categories', '[]')
            try:
                doc_categories = json.loads(doc_categories) if isinstance(doc_categories, str) else doc_categories
                categories.extend(doc_categories)
            except:
                pass
        
        # Override quality level for specialized content
        if 'technical' in categories and quality_level != 'no_context':
            quality_level = 'technical_content'
        elif 'business' in categories and quality_level != 'no_context':
            quality_level = 'business_content'
        
        return {
            'quality_level': quality_level,
            'relevance_score': avg_relevance,
            'context_diversity': len(content_types),
            'content_types': list(content_types),
            'document_sources': len(document_sources),
            'categories': list(set(categories))
        }
    
    def _generate_enhanced_response(self, 
                                  query: str, 
                                  context_results: List[Dict],
                                  context_analysis: Dict[str, Any]) -> str:
        """Generate enhanced response using context analysis"""
        
        quality_level = context_analysis['quality_level']
        
        if quality_level == 'no_context':
            return self._get_template_response('no_context', query=query)
        
        # Prepare context
        context_texts = []
        for result in context_results:
            text = result.get('text', '')
            score = result.get('combined_score', result.get('semantic_score', 0))
            context_texts.append(f"[Relevance: {score:.2f}] {text}")
        
        context = '\n\n'.join(context_texts)
        
        # Use OpenAI if available and context is good
        if self.openai_available and quality_level in ['good_context', 'technical_content', 'business_content']:
            try:
                return self._generate_openai_response(query, context, context_analysis)
            except Exception as e:
                logger.warning(f"OpenAI generation failed, using template: {e}")
        
        # Use template response
        return self._get_template_response(quality_level, query=query, context=context)
    
    def _generate_openai_response(self, 
                                 query: str, 
                                 context: str, 
                                 context_analysis: Dict[str, Any]) -> str:
        """Generate response using OpenAI with enhanced prompting"""
        
        # Customize prompt based on content type
        categories = context_analysis.get('categories', [])
        
        if 'technical' in categories:
            system_prompt = """You are a technical assistant. Provide accurate, detailed technical information based on the provided context. Include specific details and maintain technical precision."""
        elif 'business' in categories:
            system_prompt = """You are a business analyst. Provide clear, actionable business insights based on the provided context. Focus on practical implications and strategic considerations."""
        elif 'legal' in categories:
            system_prompt = """You are a legal information assistant. Provide accurate information based on the provided legal documents. Always remind users to consult with qualified legal professionals for advice."""
        else:
            system_prompt = """You are a helpful assistant. Provide accurate, comprehensive answers based on the provided context. Be clear and informative."""
        
        prompt = f"""Based on the following context from uploaded documents, please answer the user's question.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above. If the context doesn't fully answer the question, acknowledge this and provide what information is available."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _get_template_response(self, template_type: str, **kwargs) -> str:
        """Get template response with formatting"""
        import random
        
        templates = self.response_templates.get(template_type, self.response_templates['no_context'])
        template = random.choice(templates)
        
        try:
            return template.format(**kwargs)
        except KeyError:
            # Fallback if formatting fails
            return template.replace('{query}', kwargs.get('query', 'your question')).replace('{context}', kwargs.get('context', ''))
    
    def get_chatbot_analytics(self, chatbot_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a chatbot"""
        
        try:
            # Get collection statistics
            stats = self.search_service.get_collection_stats(chatbot_id)
            
            # Additional analytics could be added here
            # e.g., query frequency, response quality metrics, etc.
            
            return {
                'collection_stats': stats,
                'last_updated': str(datetime.now()),
                'service_status': {
                    'document_processor': 'active',
                    'search_service': 'active',
                    'openai_available': self.openai_available
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {'error': str(e)}
    
    def select_chunking_strategy(self, content: str, filename: str = "") -> str:
        """Automatically select the best chunking strategy based on content analysis"""
        content_length = len(content)
        
        # Analyze content structure
        line_count = len(content.split('\n'))
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        avg_line_length = content_length / max(line_count, 1)
        
        # Check file type
        file_ext = os.path.splitext(filename)[1].lower() if filename else ".txt"
        
        # Decision logic
        if file_ext in ['.csv', '.xlsx', '.xls']:
            return 'paragraph'  # Preserve table structure
        elif paragraph_count > 10 and avg_line_length > 100:
            return 'semantic'  # Well-structured documents
        elif content_length < 5000:
            return 'paragraph'  # Short documents
        else:
            return 'recursive'  # Default for long documents
    
    def delete_document(self, document_id: str, chatbot_id: str) -> Dict[str, Any]:
        """Delete document and all associated chunks"""
        return self.search_service.delete_document_chunks(document_id, chatbot_id)

# Factory function
def create_enhanced_rag_service(
    vector_db_path: str = "./chroma_db",
    embedding_model: str = "all-MiniLM-L6-v2",
    enable_openai: bool = True,
    enable_ocr: bool = True,
    chunking_strategy: str = "semantic"
) -> EnhancedRAGService:
    """Create enhanced RAG service instance"""
    
    return EnhancedRAGService(
        vector_db_path=vector_db_path,
        embedding_model=embedding_model,
        enable_openai=enable_openai,
        enable_ocr=enable_ocr,
        chunking_strategy=chunking_strategy
    )