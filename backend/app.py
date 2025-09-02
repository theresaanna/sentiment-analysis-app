# app.py - Main Flask application
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# Import your custom modules
from utils.instagram_parser import InstagramURLParser, create_instagram_parser_routes
from tasks.instagram_sentiment_tasks import (
    create_task_management_routes,
    create_monitoring_routes,
    celery_app
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory pattern for Flask app.
    """
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['CELERY_BROKER_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Environment-specific settings
    app.config['DEBUG'] = os.environ.get('FLASK_ENV') == 'development'
    app.config['TESTING'] = os.environ.get('FLASK_ENV') == 'testing'

    # Enable CORS for React frontend
    CORS(app, origins=[
        'http://localhost:3000',  # React development server
        'http://localhost:3001',  # Alternative React port
        os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    ])

    # Initialize Celery with Flask app context
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )

    # Register route blueprints/handlers
    register_routes(app)

    # Error handlers
    register_error_handlers(app)

    logger.info("Flask application created successfully")
    return app


def register_routes(app):
    """
    Register all route handlers with the Flask app.
    """

    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """
        Root endpoint with API information.
        """
        return jsonify({
            'message': 'Instagram Sentiment Analysis API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'instagram_parsing': {
                    'parse': '/api/instagram/parse',
                    'validate': '/api/instagram/validate',
                    'normalize': '/api/instagram/normalize'
                },
                'sentiment_analysis': {
                    'single': '/api/sentiment/instagram/analyze',
                    'batch': '/api/sentiment/instagram/batch'
                },
                'task_management': {
                    'status': '/api/task/status/<task_id>',
                    'cancel': '/api/task/cancel/<task_id>',
                    'active': '/api/tasks/active'
                },
                'monitoring': {
                    'health': '/api/health/celery'
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Basic health check endpoint.
        """
        return jsonify({
            'status': 'healthy',
            'service': 'Instagram Sentiment Analysis API',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })

    # Simple analyze endpoint for frontend compatibility
    @app.route('/analyze', methods=['POST', 'OPTIONS'])
    def simple_analyze():
        """
        Simple analyze endpoint that proxies to the full API path.
        This provides compatibility with frontends expecting a simple /analyze route.
        """
        if request.method == 'OPTIONS':
            # Handle CORS preflight request
            response = jsonify({'status': 'ok'})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
            
        # Forward POST requests to the main analysis endpoint        
        try:
            # Log the raw request data for debugging
            logger.info(f"Received POST request to /analyze")
            logger.info(f"Content-Type: {request.content_type}")
            logger.info(f"Request data: {request.get_data()}")
            
            # Handle JSON parsing with better error handling
            try:
                data = request.get_json(force=True)
                logger.info(f"Parsed JSON data: {data}")
            except Exception as json_error:
                logger.error(f"JSON parsing error: {str(json_error)}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON data. Please send valid JSON with a "url" field.',
                    'example': {
                        'url': 'https://www.instagram.com/p/ABC123/',
                        'user_id': 'optional_user_id',
                        'options': {'max_comments': 50}
                    }
                }), 400
            
            if not data or 'url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Instagram URL is required in the "url" field',
                    'example': {
                        'url': 'https://www.instagram.com/p/ABC123/',
                        'user_id': 'optional_user_id',
                        'options': {'max_comments': 50}
                    }
                }), 400
            
            instagram_url = data['url'].strip()
            user_id = data.get('user_id')
            options = data.get('options', {})
            
            # Validate URL
            if not InstagramURLParser.is_valid_instagram_url(instagram_url):
                return jsonify({
                    'success': False,
                    'error': 'Invalid Instagram URL provided',
                    'url': instagram_url
                }), 400
            
            # Start analysis task
            from tasks.instagram_sentiment_tasks import analyze_instagram_post
            task = analyze_instagram_post.apply_async(
                args=[instagram_url, user_id, options]
            )
            
            logger.info(f"Started Instagram sentiment analysis task {task.id} for URL: {instagram_url}")
            
            return jsonify({
                'success': True,
                'task_id': task.id,
                'status': 'started',
                'message': 'Instagram sentiment analysis task started',
                'url': instagram_url,
                'estimated_completion': '2-5 minutes'
            })
            
        except Exception as e:
            logger.error(f"Error in simple analyze endpoint: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to start analysis: {str(e)}'
            }), 500

    # Register Instagram parser routes
    create_instagram_parser_routes(app)

    # Register Celery task management routes
    create_task_management_routes(app)

    # Register monitoring routes
    create_monitoring_routes(app)

    logger.info("All routes registered successfully")


def register_error_handlers(app):
    """
    Register global error handlers.
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request',
            'status_code': 400,
            'timestamp': datetime.utcnow().isoformat()
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested endpoint was not found',
            'status_code': 404,
            'timestamp': datetime.utcnow().isoformat()
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': f'The method {request.method} is not allowed for this endpoint',
            'status_code': 405,
            'timestamp': datetime.utcnow().isoformat()
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred on the server',
            'status_code': 500,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable errors."""
        return jsonify({
            'success': False,
            'error': 'Service Unavailable',
            'message': 'Service is temporarily unavailable',
            'status_code': 503,
            'timestamp': datetime.utcnow().isoformat()
        }), 503


# Create the Flask app instance
app = create_app()

if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')

    print("=" * 60)
    print("Instagram Sentiment Analysis API Server")
    print("=" * 60)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"Debug mode: {debug_mode}")
    print(f"Server: http://{host}:{port}")
    print(f"Redis URL: {os.environ.get('REDIS_URL', 'redis://localhost:6379/0')}")
    print("=" * 60)
    print("\nIMPORTANT: Make sure to start Celery workers separately:")
    print("celery -A tasks.instagram_sentiment_tasks worker --loglevel=info")
    print("\nOptional: Start Celery monitoring with Flower:")
    print("celery -A tasks.instagram_sentiment_tasks flower")
    print("=" * 60)

    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )