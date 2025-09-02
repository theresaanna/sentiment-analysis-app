from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    # Enable CORS for React frontend
    CORS(app, origins=["http://localhost:3000"])

    # Simple health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        return {'status': 'healthy', 'message': 'Backend is running'}

    # Test route
    @app.route('/test', methods=['GET'])
    def test():
        return {'message': 'Hello from Flask!'}

    return app