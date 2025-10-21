from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_simple_app():
    """Create a simplified Flask app for testing basic functionality"""
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
    
    # Register basic blueprints (without enhanced services)
    from auth import auth_bp
    from chatbots import chatbots_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbots_bp)
    
    # Basic test routes
    @app.route('/api/hello', methods=['GET'])
    def hello_world():
        return jsonify({
            'message': 'Hello from Flask Backend!',
            'timestamp': '2025-11-01',
            'service': 'RAG Chatbot Builder',
            'status': 'Basic mode - enhanced features disabled',
            'version': 'Phase 4 - Testing Mode'
        })
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'features': {
                'auth': 'enabled',
                'chatbots': 'enabled',
                'enhanced_processing': 'disabled (testing mode)',
                'hybrid_search': 'disabled (testing mode)'
            }
        })
    
    @app.route('/api/test', methods=['POST'])
    def test_post():
        data = request.get_json()
        return jsonify({
            'received': data,
            'message': 'Data received successfully',
            'status': 'success'
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
    app = create_simple_app()
    print("🚀 Starting Flask server in testing mode...")
    print("📡 Enhanced features temporarily disabled for compatibility testing")
    print("🌐 Server will be available at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)