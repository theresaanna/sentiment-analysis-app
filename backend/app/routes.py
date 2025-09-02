from flask import Blueprint, request, jsonify
from backend.run import redis_client
from backend.run import analyze_sentiment_task
import re

main = Blueprint('main', __name__)


def is_valid_instagram_url(url):
    """Basic Instagram URL validation"""
    pattern = r'https?://(www\.)?(instagram\.com|instagr\.am)/p/[A-Za-z0-9_-]+/?'
    return bool(re.match(pattern, url))


@main.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.redis.ping()
        return jsonify({
            'status': 'healthy',
            'redis': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@main.route('/analyze', methods=['POST'])
def submit_analysis():
    """Submit Instagram post for sentiment analysis"""
    data = request.get_json()

    if not data or 'post_url' not in data:
        return jsonify({'error': 'post_url is required'}), 400

    post_url = data['post_url'].strip()

    if not is_valid_instagram_url(post_url):
        return jsonify({'error': 'Invalid Instagram URL'}), 400

    try:
        # Create analysis entry
        analysis_id = redis_client.create_analysis(post_url)

        # Queue background task
        analyze_sentiment_task.delay(analysis_id, post_url)

        return jsonify({
            'analysis_id': analysis_id,
            'status': 'pending',
            'message': 'Analysis queued successfully'
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to queue analysis: {str(e)}'}), 500


@main.route('/analysis/<analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Get analysis results by ID"""
    try:
        analysis = redis_client.get_analysis(analysis_id)

        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404

        return jsonify(analysis)

    except Exception as e:
        return jsonify({'error': f'Failed to get analysis: {str(e)}'}), 500


@main.route('/analyses', methods=['GET'])
def get_recent_analyses():
    """Get recent analyses"""
    try:
        limit = request.args.get('limit', 10, type=int)
        analyses = redis_client.get_recent_analyses(limit)

        return jsonify({
            'analyses': analyses,
            'total': len(analyses)
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get analyses: {str(e)}'}), 500