from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'message': 'Backend is running'}

    @app.route('/test')
    def test():
        return {'message': 'Hello from Flask!'}

    return app