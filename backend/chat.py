from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_required
from models import db, User, Chatbot, Query
from enhanced_rag_service import create_enhanced_rag_service
from datetime import datetime
import time

# Initialize enhanced RAG service
enhanced_rag_service = create_enhanced_rag_service(
    enable_ocr=True,
    chunking_strategy="auto"  # Auto-select best strategy
)

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/<chatbot_id>/query', methods=['POST'])
@jwt_required()
def chat_query(chatbot_id):
    """Process a chat query for a specific chatbot with enhanced RAG"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify chatbot belongs to user
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get query context preferences
        search_type = data.get('search_type', 'hybrid')  # hybrid, semantic, or keyword
        context_limit = data.get('context_limit', 5)
        
        # Prepare enhanced chatbot configuration
        chatbot_config = {
            'name': chatbot.name,
            'tone': chatbot.tone,
            'instructions': f"You are {chatbot.name}, a helpful AI assistant.",
            'search_type': search_type,
            'context_limit': context_limit
        }
        
        # Process the query through enhanced RAG pipeline
        start_time = time.time()
        result = enhanced_rag_service.generate_response(
            query=user_message,
            chatbot_id=chatbot_id,
            config=chatbot_config
        )
        end_time = time.time()
        
        if not result['success']:
            return jsonify({
                'error': 'Failed to process query',
                'details': result.get('error', 'Unknown error')
            }), 500
        
        # Enhanced metadata
        response_metadata = result.get('metadata', {})
        
        # Save query to database with enhanced metadata
        query_record = Query(
            chatbot_id=chatbot_id,
            user_message=user_message,
            bot_response=result['response'],
            tokens_used=response_metadata.get('tokens_used', 0),
            response_time=end_time - start_time
        )
        
        db.session.add(query_record)
        db.session.commit()
        
        return jsonify({
            'response': result['response'],
            'metadata': {
                'query_id': query_record.id,
                'search_results': response_metadata.get('search_results', {}),
                'context_sources': response_metadata.get('context_sources', []),
                'tokens_used': response_metadata.get('tokens_used', 0),
                'response_time': end_time - start_time,
                'model_used': response_metadata.get('model_used', 'unknown'),
                'search_type': search_type,
                'chatbot_name': chatbot.name,
                'quality_score': response_metadata.get('quality_score', 0.0),
                'confidence': response_metadata.get('confidence', 0.0)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Enhanced chat query error: {str(e)}")
        return jsonify({'error': 'Failed to process chat query'}), 500

@chat_bp.route('/<chatbot_id>/history', methods=['GET'])
@jwt_required()
def get_chat_history(chatbot_id):
    """Get chat history for a chatbot"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify chatbot belongs to user
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)  # Limit to 100 per page
        
        # Get queries with pagination
        queries = Query.query.filter_by(chatbot_id=chatbot_id)\
                           .order_by(Query.created_at.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'queries': [query.to_dict() for query in queries.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': queries.total,
                'pages': queries.pages,
                'has_next': queries.has_next,
                'has_prev': queries.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get chat history error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve chat history'}), 500

@chat_bp.route('/public/<api_key>/query', methods=['POST'])
def public_chat_query(api_key):
    """Public endpoint for chatbot queries using API key with enhanced capabilities"""
    try:
        # Find chatbot by API key
        chatbot = Chatbot.query.filter_by(api_key=api_key, is_active=True).first()
        if not chatbot:
            return jsonify({'error': 'Invalid API key or chatbot not found'}), 404
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get search preferences from request
        search_type = data.get('search_type', 'hybrid')
        
        # Prepare enhanced chatbot configuration
        chatbot_config = {
            'name': chatbot.name,
            'tone': chatbot.tone,
            'instructions': f"You are {chatbot.name}, a helpful AI assistant.",
            'search_type': search_type
        }
        
        # Process the query through enhanced RAG pipeline
        start_time = time.time()
        result = enhanced_rag_service.generate_response(
            query=user_message,
            chatbot_id=chatbot.id,
            config=chatbot_config
        )
        end_time = time.time()
        
        if not result['success']:
            return jsonify({
                'error': 'Failed to process query',
                'message': 'I apologize, but I encountered an error processing your question.'
            }), 500
        
        # Save query to database (for analytics)
        query_record = Query(
            chatbot_id=chatbot.id,
            user_message=user_message,
            bot_response=result['response'],
            tokens_used=result.get('metadata', {}).get('tokens_used', 0),
            response_time=end_time - start_time
        )
        
        db.session.add(query_record)
        db.session.commit()
        
        return jsonify({
            'response': result['response'],
            'chatbot_name': chatbot.name,
            'timestamp': datetime.utcnow().isoformat(),
            'search_type': search_type
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Public enhanced chat query error: {str(e)}")
        return jsonify({
            'error': 'Service temporarily unavailable',
            'message': 'I apologize, but I encountered an error. Please try again later.'
        }), 500

@chat_bp.route('/test/<chatbot_id>', methods=['POST'])
@jwt_required()
def test_chatbot(chatbot_id):
    """Test endpoint for enhanced chatbot functionality"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify chatbot belongs to user
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Enhanced test queries
        test_queries = [
            "What is this document about?",
            "Can you summarize the main points?",
            "What topics are covered in the uploaded content?",
            "What key insights can you extract from the documents?",
            "Can you explain the most important concepts?"
        ]
        
        data = request.get_json()
        test_query = data.get('query', test_queries[0]) if data else test_queries[0]
        search_type = data.get('search_type', 'hybrid') if data else 'hybrid'
        
        # Get enhanced chatbot analytics
        analytics = enhanced_rag_service.get_chatbot_analytics(chatbot_id)
        
        # Process test query if there are documents
        collection_stats = analytics.get('collection_stats', {})
        total_chunks = collection_stats.get('total_chunks', 0)
        
        if total_chunks > 0:
            config = {
                'name': chatbot.name,
                'search_type': search_type
            }
            result = enhanced_rag_service.generate_response(
                query=test_query,
                chatbot_id=chatbot_id,
                config=config
            )
            test_response = result.get('response', 'No response generated')
            response_metadata = result.get('metadata', {})
        else:
            test_response = "No documents have been uploaded yet. Please upload some documents first to test the chatbot."
            response_metadata = {}
        
        return jsonify({
            'chatbot_name': chatbot.name,
            'test_query': test_query,
            'test_response': test_response,
            'search_type': search_type,
            'analytics': analytics,
            'response_metadata': response_metadata,
            'suggestions': test_queries,
            'available_search_types': ['semantic', 'keyword', 'hybrid'],
            'service_capabilities': {
                'ocr_enabled': enhanced_rag_service.document_processor.ocr_available,
                'supported_formats': enhanced_rag_service.document_processor.get_supported_formats(),
                'chunking_strategies': ['recursive', 'semantic', 'paragraph', 'auto']
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Test enhanced chatbot error: {str(e)}")
        return jsonify({'error': 'Failed to test chatbot'}), 500