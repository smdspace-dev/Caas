from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, User, Chatbot, Document
from enhanced_rag_service import create_enhanced_rag_service
import os
from datetime import datetime
import uuid

# Initialize enhanced RAG service
rag_service = create_enhanced_rag_service(
    enable_ocr=True,
    chunking_strategy="semantic"
)

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    """Upload and process a document using enhanced RAG service"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if file and chatbot_id are provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        if 'chatbot_id' not in request.form:
            return jsonify({'error': 'Chatbot ID is required'}), 400
        
        file = request.files['file']
        chatbot_id = request.form['chatbot_id']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Verify chatbot ownership
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Validate file using enhanced processor
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Save file temporarily
        uploads_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), chatbot_id)
        os.makedirs(uploads_dir, exist_ok=True)
        
        file_path = os.path.join(uploads_dir, f"{uuid.uuid4()}{file_ext}")
        file.save(file_path)
        
        try:
            # Create document record
            document = Document(
                chatbot_id=chatbot_id,
                filename=filename,
                original_filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                file_type=file_ext,
                status='processing'
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Process document with enhanced RAG service
            processing_result = rag_service.process_document(
                file_path=file_path,
                chatbot_id=chatbot_id,
                document_id=document.id
            )
            
            if processing_result['success']:
                # Update document status and metadata
                document.status = 'completed'
                document.chunk_count = processing_result['chunks_created']
                document.processing_time = processing_result['processing_time']
                document.processed_at = datetime.utcnow()
                
                # Store additional metadata as JSON
                metadata = processing_result.get('metadata', {})
                document.metadata = {
                    'word_count': metadata.get('word_count', 0),
                    'language': metadata.get('language', 'unknown'),
                    'readability_score': metadata.get('readability_score', 0.0),
                    'content_quality': metadata.get('content_quality', 'unknown'),
                    'content_categories': metadata.get('content_categories', []),
                    'has_images': metadata.get('has_images', False),
                    'has_tables': metadata.get('has_tables', False),
                    'chunking_strategy': processing_result.get('chunking_strategy', 'unknown'),
                    'document_analysis': processing_result.get('document_analysis', {}),
                    'extracted_elements': processing_result.get('extracted_elements', {})
                }
                
                db.session.commit()
                
                return jsonify({
                    'message': 'Document uploaded and processed successfully',
                    'document': document.to_dict(),
                    'processing_result': {
                        'chunks_created': processing_result['chunks_created'],
                        'processing_time': processing_result['processing_time'],
                        'chunking_strategy': processing_result.get('chunking_strategy'),
                        'document_analysis': processing_result.get('document_analysis', {})
                    }
                }), 201
            else:
                # Processing failed
                document.status = 'failed'
                document.error_message = processing_result.get('error', 'Unknown processing error')
                db.session.commit()
                
                return jsonify({
                    'error': 'Document processing failed',
                    'details': processing_result.get('error', 'Unknown error')
                }), 500
                
        except Exception as e:
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        current_app.logger.error(f"Document upload error: {str(e)}")
        return jsonify({'error': 'Failed to upload document'}), 500

@documents_bp.route('/chatbot/<chatbot_id>', methods=['GET'])
@jwt_required()
def get_chatbot_documents(chatbot_id):
    """Get all documents for a specific chatbot"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify chatbot ownership
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Get documents
        documents = Document.query.filter_by(chatbot_id=chatbot_id).order_by(Document.created_at.desc()).all()
        
        documents_data = []
        for doc in documents:
            doc_data = doc.to_dict()
            
            # Add enhanced metadata if available
            if hasattr(doc, 'metadata') and doc.metadata:
                doc_data['enhanced_metadata'] = doc.metadata
                
            documents_data.append(doc_data)
        
        return jsonify({
            'documents': documents_data,
            'total': len(documents_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get documents error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve documents'}), 500

@documents_bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    """Delete a document and its chunks"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get document with user verification
        document = db.session.query(Document).join(Chatbot).filter(
            Document.id == document_id,
            Chatbot.user_id == current_user_id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found or access denied'}), 404
        
        # Delete from vector database using enhanced service
        delete_result = rag_service.delete_document(document_id, document.chatbot_id)
        
        # Delete file from disk
        if document.file_path and os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception as e:
                current_app.logger.warning(f"Could not delete file {document.file_path}: {str(e)}")
        
        # Delete from database
        filename = document.original_filename
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({
            'message': f'Document "{filename}" deleted successfully',
            'delete_result': delete_result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete document error: {str(e)}")
        return jsonify({'error': 'Failed to delete document'}), 500

@documents_bp.route('/stats/<chatbot_id>', methods=['GET'])
@jwt_required()
def get_chatbot_stats(chatbot_id):
    """Get comprehensive statistics for a chatbot"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify chatbot ownership
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Get basic document stats
        total_docs = Document.query.filter_by(chatbot_id=chatbot_id).count()
        completed_docs = Document.query.filter_by(chatbot_id=chatbot_id, status='completed').count()
        failed_docs = Document.query.filter_by(chatbot_id=chatbot_id, status='failed').count()
        processing_docs = Document.query.filter_by(chatbot_id=chatbot_id, status='processing').count()
        
        # Get total chunks and file sizes
        documents = Document.query.filter_by(chatbot_id=chatbot_id, status='completed').all()
        total_chunks = sum(doc.chunk_count or 0 for doc in documents)
        total_file_size = sum(doc.file_size or 0 for doc in documents)
        
        # Get enhanced analytics from RAG service
        analytics = rag_service.get_chatbot_analytics(chatbot_id)
        
        # Analyze document metadata for insights
        content_types = {}
        languages = {}
        quality_distribution = {}
        categories = {}
        
        for doc in documents:
            if hasattr(doc, 'metadata') and doc.metadata:
                metadata = doc.metadata
                
                # Content categories
                doc_categories = metadata.get('content_categories', [])
                for category in doc_categories:
                    categories[category] = categories.get(category, 0) + 1
                
                # Languages
                language = metadata.get('language', 'unknown')
                languages[language] = languages.get(language, 0) + 1
                
                # Quality
                quality = metadata.get('content_quality', 'unknown')
                quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        return jsonify({
            'document_stats': {
                'total_documents': total_docs,
                'completed': completed_docs,
                'failed': failed_docs,
                'processing': processing_docs,
                'total_chunks': total_chunks,
                'total_file_size': total_file_size
            },
            'content_analysis': {
                'content_categories': categories,
                'languages': languages,
                'quality_distribution': quality_distribution
            },
            'collection_analytics': analytics.get('collection_stats', {}),
            'service_status': analytics.get('service_status', {}),
            'last_updated': analytics.get('last_updated')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@documents_bp.route('/supported-formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported file formats with enhanced capabilities"""
    return jsonify({
        'supported_formats': {
            'documents': {
                '.pdf': {
                    'description': 'PDF documents with text extraction and OCR support',
                    'features': ['text_extraction', 'image_extraction', 'table_detection', 'ocr']
                },
                '.docx': {
                    'description': 'Microsoft Word documents',
                    'features': ['text_extraction', 'table_extraction', 'image_detection']
                },
                '.txt': {
                    'description': 'Plain text files',
                    'features': ['text_extraction', 'encoding_detection']
                }
            },
            'spreadsheets': {
                '.xlsx': {
                    'description': 'Microsoft Excel files',
                    'features': ['data_extraction', 'multi_sheet_support', 'table_structure']
                },
                '.csv': {
                    'description': 'Comma-separated values',
                    'features': ['data_extraction', 'delimiter_detection', 'encoding_detection']
                }
            },
            'presentations': {
                '.pptx': {
                    'description': 'Microsoft PowerPoint presentations',
                    'features': ['text_extraction', 'slide_structure', 'image_detection']
                }
            },
            'web_content': {
                '.html': {
                    'description': 'HTML web pages',
                    'features': ['text_extraction', 'structure_preservation', 'link_extraction']
                }
            },
            'images': {
                '.png': {'description': 'PNG images with OCR', 'features': ['ocr_extraction']},
                '.jpg': {'description': 'JPEG images with OCR', 'features': ['ocr_extraction']},
                '.jpeg': {'description': 'JPEG images with OCR', 'features': ['ocr_extraction']},
                '.gif': {'description': 'GIF images with OCR', 'features': ['ocr_extraction']},
                '.bmp': {'description': 'BMP images with OCR', 'features': ['ocr_extraction']},
                '.tiff': {'description': 'TIFF images with OCR', 'features': ['ocr_extraction']}
            }
        },
        'processing_features': {
            'chunking_strategies': ['recursive', 'semantic', 'paragraph'],
            'analysis_features': ['language_detection', 'readability_scoring', 'content_categorization', 'quality_assessment'],
            'search_capabilities': ['semantic_search', 'keyword_search', 'hybrid_search'],
            'content_intelligence': ['table_detection', 'image_extraction', 'structure_analysis']
        },
        'limits': {
            'max_file_size': '50MB',
            'supported_languages': 'Auto-detected (55+ languages)',
            'ocr_availability': rag_service.document_processor.ocr_available
        }
    }), 200