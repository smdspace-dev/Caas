from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Chatbot, Document, Query
from datetime import datetime
import uuid

chatbots_bp = Blueprint('chatbots', __name__, url_prefix='/api/chatbots')

@chatbots_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_chatbots():
    """Get all chatbots for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        chatbots = Chatbot.query.filter_by(user_id=current_user_id).all()
        
        # Add stats for each chatbot
        chatbots_data = []
        for chatbot in chatbots:
            chatbot_dict = chatbot.to_dict()
            
            # Add document and query counts
            doc_count = Document.query.filter_by(chatbot_id=chatbot.id).count()
            query_count = Query.query.filter_by(chatbot_id=chatbot.id).count()
            
            chatbot_dict['document_count'] = doc_count
            chatbot_dict['query_count'] = query_count
            
            chatbots_data.append(chatbot_dict)
        
        return jsonify({
            'chatbots': chatbots_data,
            'total': len(chatbots_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get chatbots error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve chatbots'}), 500

@chatbots_bp.route('/', methods=['POST'])
@jwt_required()
def create_chatbot():
    """Create a new chatbot"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({'error': 'Chatbot name is required'}), 400
        
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Chatbot name cannot be empty'}), 400
        
        # Check if chatbot name already exists for this user
        existing = Chatbot.query.filter_by(user_id=current_user_id, name=name).first()
        if existing:
            return jsonify({'error': 'A chatbot with this name already exists'}), 409
        
        # Create new chatbot
        chatbot = Chatbot(
            user_id=current_user_id,
            name=name,
            description=data.get('description', ''),
            theme=data.get('theme', 'default'),
            tone=data.get('tone', 'friendly')
        )
        
        db.session.add(chatbot)
        db.session.commit()
        
        return jsonify({
            'message': 'Chatbot created successfully',
            'chatbot': chatbot.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Create chatbot error: {str(e)}")
        return jsonify({'error': 'Failed to create chatbot'}), 500

@chatbots_bp.route('/<chatbot_id>', methods=['GET'])
@jwt_required()
def get_chatbot(chatbot_id):
    """Get a specific chatbot"""
    try:
        current_user_id = get_jwt_identity()
        
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        chatbot_data = chatbot.to_dict()
        
        # Add additional stats
        doc_count = Document.query.filter_by(chatbot_id=chatbot_id).count()
        query_count = Query.query.filter_by(chatbot_id=chatbot_id).count()
        
        chatbot_data['document_count'] = doc_count
        chatbot_data['query_count'] = query_count
        
        return jsonify({'chatbot': chatbot_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get chatbot error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve chatbot'}), 500

@chatbots_bp.route('/<chatbot_id>', methods=['PUT'])
@jwt_required()
def update_chatbot(chatbot_id):
    """Update a chatbot"""
    try:
        current_user_id = get_jwt_identity()
        
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({'error': 'Chatbot name cannot be empty'}), 400
            
            # Check if name already exists for this user (excluding current chatbot)
            existing = Chatbot.query.filter_by(
                user_id=current_user_id, 
                name=name
            ).filter(Chatbot.id != chatbot_id).first()
            
            if existing:
                return jsonify({'error': 'A chatbot with this name already exists'}), 409
            
            chatbot.name = name
        
        if 'description' in data:
            chatbot.description = data['description']
        
        if 'theme' in data:
            chatbot.theme = data['theme']
        
        if 'tone' in data:
            chatbot.tone = data['tone']
        
        if 'is_active' in data:
            chatbot.is_active = bool(data['is_active'])
        
        chatbot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Chatbot updated successfully',
            'chatbot': chatbot.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Update chatbot error: {str(e)}")
        return jsonify({'error': 'Failed to update chatbot'}), 500

@chatbots_bp.route('/<chatbot_id>', methods=['DELETE'])
@jwt_required()
def delete_chatbot(chatbot_id):
    """Delete a chatbot and all its data"""
    try:
        current_user_id = get_jwt_identity()
        
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Get stats before deletion
        doc_count = Document.query.filter_by(chatbot_id=chatbot_id).count()
        query_count = Query.query.filter_by(chatbot_id=chatbot_id).count()
        
        # Note: The database relationships are set up with cascade delete,
        # so deleting the chatbot will also delete all associated documents and queries
        
        chatbot_name = chatbot.name
        db.session.delete(chatbot)
        db.session.commit()
        
        return jsonify({
            'message': f'Chatbot "{chatbot_name}" deleted successfully',
            'deleted_documents': doc_count,
            'deleted_queries': query_count
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete chatbot error: {str(e)}")
        return jsonify({'error': 'Failed to delete chatbot'}), 500

@chatbots_bp.route('/<chatbot_id>/regenerate-api-key', methods=['POST'])
@jwt_required()
def regenerate_api_key(chatbot_id):
    """Regenerate API key for a chatbot"""
    try:
        current_user_id = get_jwt_identity()
        
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Generate new API key
        chatbot.api_key = str(uuid.uuid4().hex)
        chatbot.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'API key regenerated successfully',
            'api_key': chatbot.api_key
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Regenerate API key error: {str(e)}")
        return jsonify({'error': 'Failed to regenerate API key'}), 500

@chatbots_bp.route('/<chatbot_id>/embed-code', methods=['GET'])
@jwt_required()
def get_embed_code(chatbot_id):
    """Get embed code for a chatbot"""
    try:
        current_user_id = get_jwt_identity()
        
        chatbot = Chatbot.query.filter_by(id=chatbot_id, user_id=current_user_id).first()
        if not chatbot:
            return jsonify({'error': 'Chatbot not found or access denied'}), 404
        
        # Generate embed code
        api_endpoint = f"{request.host_url}api/chat/public/{chatbot.api_key}/query"
        
        embed_script = f"""
<!-- {chatbot.name} Chatbot Embed -->
<div id="chatbot-{chatbot_id}"></div>
<script>
(function() {{
    const chatbotConfig = {{
        apiKey: "{chatbot.api_key}",
        apiEndpoint: "{api_endpoint}",
        chatbotName: "{chatbot.name}",
        theme: "{chatbot.theme}",
        containerId: "chatbot-{chatbot_id}"
    }};
    
    // Basic chatbot widget implementation
    // This would be replaced with a more sophisticated widget in production
    const container = document.getElementById(chatbotConfig.containerId);
    if (container) {{
        container.innerHTML = `
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; max-width: 400px;">
                <h4>{chatbot.name}</h4>
                <div id="chat-messages-{chatbot_id}" style="height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 8px; margin: 8px 0;"></div>
                <input type="text" id="chat-input-{chatbot_id}" placeholder="Type your message..." style="width: 100%; padding: 8px; margin-bottom: 8px;">
                <button onclick="sendMessage()" style="width: 100%; padding: 8px; background: #007bff; color: white; border: none; border-radius: 4px;">Send</button>
            </div>
        `;
        
        window.sendMessage = function() {{
            const input = document.getElementById("chat-input-{chatbot_id}");
            const messages = document.getElementById("chat-messages-{chatbot_id}");
            
            if (input.value.trim()) {{
                const userMessage = input.value;
                messages.innerHTML += `<div><strong>You:</strong> ${{userMessage}}</div>`;
                
                fetch(chatbotConfig.apiEndpoint, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message: userMessage}})
                }})
                .then(response => response.json())
                .then(data => {{
                    messages.innerHTML += `<div><strong>${{chatbotConfig.chatbotName}}:</strong> ${{data.response || data.message || 'Sorry, I encountered an error.'}}</div>`;
                    messages.scrollTop = messages.scrollHeight;
                }})
                .catch(error => {{
                    messages.innerHTML += `<div><strong>${{chatbotConfig.chatbotName}}:</strong> Sorry, I'm having trouble responding right now.</div>`;
                }});
                
                input.value = '';
            }}
        }};
        
        document.getElementById("chat-input-{chatbot_id}").addEventListener("keypress", function(e) {{
            if (e.key === "Enter") {{
                sendMessage();
            }}
        }});
    }}
}})();
</script>
"""

        return jsonify({
            'embed_code': embed_script.strip(),
            'api_endpoint': api_endpoint,
            'chatbot_name': chatbot.name,
            'instructions': 'Copy and paste this code into your website where you want the chatbot to appear.'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get embed code error: {str(e)}")
        return jsonify({'error': 'Failed to generate embed code'}), 500