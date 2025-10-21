from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///chatbot_builder.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
    
    # Initialize extensions
    from models import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:4200", "http://127.0.0.1:4200"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Test enhanced service initialization
    try:
        from safe_enhanced_rag_service import create_safe_enhanced_rag_service
        enhanced_service = create_safe_enhanced_rag_service(enable_enhanced=True)
        app.config['ENHANCED_FEATURES'] = enhanced_service.enhanced_features_available
        logger.info(f"Enhanced features available: {enhanced_service.enhanced_features_available}")
        if not enhanced_service.enhanced_features_available:
            logger.warning(f"Enhanced features disabled: {enhanced_service.error_message}")
    except Exception as e:
        app.config['ENHANCED_FEATURES'] = False
        logger.error(f"Could not initialize enhanced service: {e}")
    
    # Register blueprints
    try:
        # Basic blueprints (should always work)
        from auth import auth_bp
        from chatbots import chatbots_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(chatbots_bp)
        logger.info("Basic blueprints registered successfully")
        
        # Enhanced blueprints (only if features are available)
        if app.config.get('ENHANCED_FEATURES', False):
            try:
                from documents import documents_bp
                from chat import chat_bp
                
                app.register_blueprint(documents_bp)
                app.register_blueprint(chat_bp)
                logger.info("Enhanced blueprints registered successfully")
            except Exception as e:
                logger.warning(f"Could not register enhanced blueprints: {e}")
        else:
            logger.info("Enhanced blueprints skipped (features not available)")
            
    except Exception as e:
        logger.error(f"Error registering blueprints: {e}")
    
    # Enhanced test routes
    @app.route('/api/hello', methods=['GET'])
    def hello_world():
        return jsonify({
            'message': 'Hello from Enhanced Flask Backend!',
            'timestamp': '2025-11-01',
            'service': 'RAG Chatbot Builder - Phase 4',
            'enhanced_features': app.config.get('ENHANCED_FEATURES', False),
            'version': '4.0.0'
        })
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'enhanced_features': app.config.get('ENHANCED_FEATURES', False),
            'features': {
                'auth': 'enabled',
                'chatbots': 'enabled',
                'enhanced_processing': 'enabled' if app.config.get('ENHANCED_FEATURES') else 'disabled',
                'hybrid_search': 'enabled' if app.config.get('ENHANCED_FEATURES') else 'disabled',
                'document_intelligence': 'enabled' if app.config.get('ENHANCED_FEATURES') else 'disabled'
            }
        })
    
    @app.route('/api/system/status', methods=['GET'])
    def system_status():
        """Enhanced system status endpoint"""
        try:
            from safe_enhanced_rag_service import create_safe_enhanced_rag_service
            service = create_safe_enhanced_rag_service(enable_enhanced=True)
            
            return jsonify({
                'system': 'operational',
                'enhanced_features': service.enhanced_features_available,
                'error_details': service.error_message if not service.enhanced_features_available else None,
                'capabilities': {
                    'document_processing': service.enhanced_features_available,
                    'hybrid_search': service.enhanced_features_available,
                    'advanced_chunking': service.enhanced_features_available,
                    'content_analysis': service.enhanced_features_available
                },
                'dependencies': {
                    'sentence_transformers': _check_dependency('sentence_transformers'),
                    'torch': _check_dependency('torch'),
                    'sklearn': _check_dependency('sklearn'),
                    'pandas': _check_dependency('pandas')
                }
            })
        except Exception as e:
            return jsonify({
                'system': 'degraded',
                'error': str(e),
                'enhanced_features': False
            }), 500
    
    def _check_dependency(module_name: str) -> bool:
        """Check if a dependency is available"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    @app.route('/api/test', methods=['POST'])
    def test_post():
        data = request.get_json()
        return jsonify({
            'received': data,
            'message': 'Data received successfully',
            'status': 'success',
            'enhanced_mode': app.config.get('ENHANCED_FEATURES', False)
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    enhanced_status = "✅ ENABLED" if app.config.get('ENHANCED_FEATURES') else "⚠️ DISABLED"
    
    print("🚀 Starting Enhanced RAG Chatbot Backend")
    print("=" * 50)
    print(f"📈 Phase 4 Features: {enhanced_status}")
    print("🌐 Server: http://localhost:5000")
    print("📊 Health Check: http://localhost:5000/api/health")
    print("🔧 System Status: http://localhost:5000/api/system/status")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)