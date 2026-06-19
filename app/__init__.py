from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from .config import Config

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    """
    Application factory function
    Creates and configures the Flask application
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = 'my-super-secret-key'

    # Initialize extensions
    db.init_app(app)

    # Configure CORS for cross-origin requests
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", 
                       "http://localhost:5000", "http://127.0.0.1:5000", "null"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["X-Total-Count", "X-Page-Count"],
            "supports_credentials": True
        }
    })

    # Register blueprints/routes
    from .routes import api
    app.register_blueprint(api, url_prefix='/api')

    # Register MySQL demonstration routes
    from .mysql_routes import mysql_demo
    app.register_blueprint(mysql_demo, url_prefix='/mysql')

    # Register authentication routes
    from .auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Register user functionality routes
    from .user_routes import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')

    # Register admin panel routes
    from .admin_routes import admin_api_bp, admin_bp
    # JSON admin API
    app.register_blueprint(admin_api_bp, url_prefix='/api/admin')
    # Session-based admin panel at /admin/...
    app.register_blueprint(admin_bp)

    # Register vendor panel routes
    from .vendor_routes import vendor_bp
    app.register_blueprint(vendor_bp, url_prefix='/api/vendor')

    # Serve vendor panel pages at /vendor/login and /vendor/dashboard
    from .vendor_pages import vendor_pages_bp
    app.register_blueprint(vendor_pages_bp)

    # Serve customer (frontend) pages
    from .user_pages import user_pages_bp
    app.register_blueprint(user_pages_bp)

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood or was missing required parameters.'
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource.'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource.'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found.'
        }), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()  # Rollback any pending transactions
        print(f"Internal Server Error: {str(error)}")  # Log for debugging
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500

    # Create database tables (don't crash if DB is unavailable)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create/connect to database: {e}")
            print("  App will run but API may fail until MySQL is running.")

    return app
