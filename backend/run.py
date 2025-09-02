from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import redis
import json
from datetime import datetime
from celery_app import celery_app, analyze_sentiment_task, test_task

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# Redis client for storing analysis data
redis_client = redis.from_url('redis://redis:6379/0', decode_responses=True)


@app.route('/health')
def health():
    try:
        # Test Redis connection
        redis_client.ping()
        return {'status': 'healthy', 'message': 'Backend is running', 'redis': 'connected'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': str(e)}, 500


@app.route('/test')
def test():
    return {'message': 'Hello from Flask!'}


@app.route('/test-celery')
def test_celery():
    """Test Celery connection"""
    try:
        # Queue a test task
        task = test_task.delay("Hello from Flask!")
        return {
            'message': 'Celery task queued',
            'task_id': task.id,
            'status': 'queued'
        }
    except Exception as e:
        return {'error': f'Celery connection failed: {str(e)}'}, 500


@app.route('/analyze', methods=['POST'])
def submit_analysis():
    """Submit Instagram URL for analysis"""
    try:
        data = request.get_json()
        if not data or 'post_url' not in data:
            return {'error': 'post_url is required'}, 400

        post_url = data['post_url'].strip()

        # Basic Instagram URL validation
        if 'instagram.com' not in post_url:
            return {'error': 'Invalid Instagram URL'}, 400

        # Generate analysis ID
        analysis_id = str(uuid.uuid4())

        # Store analysis metadata in Redis
        analysis_data = {
            'id': analysis_id,
            'post_url': post_url,
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        redis_client.hset(f"analysis:{analysis_id}", mapping=analysis_data)
        redis_client.zadd('analyses:all', {analysis_id: datetime.now().timestamp()})
        redis_client.expire(f"analysis:{analysis_id}", 86400)  # 24 hours

        # Queue the background task
        task = analyze_sentiment_task.delay(analysis_id, post_url)

        # Store task ID
        redis_client.hset(f"analysis:{analysis_id}", 'task_id', task.id)

        return {
            'analysis_id': analysis_id,
            'task_id': task.id,
            'status': 'queued',
            'message': 'Analysis queued successfully'
        }, 201

    except Exception as e:
        return {'error': f'Failed to queue analysis: {str(e)}'}, 500


@app.route('/analysis/<analysis_id>')
def get_analysis(analysis_id):
    """Get analysis status and results"""
    try:
        # Get analysis data from Redis
        analysis_data = redis_client.hgetall(f"analysis:{analysis_id}")

        if not analysis_data:
            return {'error': 'Analysis not found'}, 404

        # Get task status if we have a task_id
        task_id = analysis_data.get('task_id')
        if task_id:
            task_result = celery_app.AsyncResult(task_id)

            # Update status based on Celery task state
            if task_result.state == 'PENDING':
                analysis_data['status'] = 'queued'
            elif task_result.state == 'PROGRESS':
                analysis_data['status'] = 'processing'
                analysis_data['progress'] = task_result.info
            elif task_result.state == 'SUCCESS':
                analysis_data['status'] = 'completed'
                analysis_data['results'] = task_result.result.get('results')
                # Update Redis with results
                redis_client.hset(f"analysis:{analysis_id}", 'status', 'completed')
                redis_client.set(f"analysis:{analysis_id}:results", json.dumps(task_result.result.get('results')))
            elif task_result.state == 'FAILURE':
                analysis_data['status'] = 'failed'
                analysis_data['error'] = str(task_result.info)
                redis_client.hset(f"analysis:{analysis_id}", 'status', 'failed')

        # Get stored results if they exist
        if analysis_data['status'] == 'completed' and 'results' not in analysis_data:
            stored_results = redis_client.get(f"analysis:{analysis_id}:results")
            if stored_results:
                analysis_data['results'] = json.loads(stored_results)

        return analysis_data

    except Exception as e:
        return {'error': f'Failed to get analysis: {str(e)}'}, 500


@app.route('/analyses')
def get_recent_analyses():
    """Get recent analyses"""
    try:
        limit = request.args.get('limit', 10, type=int)

        # Get recent analysis IDs from Redis sorted set
        analysis_ids = redis_client.zrevrange('analyses:all', 0, limit - 1)

        analyses = []
        for analysis_id in analysis_ids:
            analysis_data = redis_client.hgetall(f"analysis:{analysis_id}")
            if analysis_data:
                analyses.append(analysis_data)

        return {
            'analyses': analyses,
            'total': len(analyses)
        }

    except Exception as e:
        return {'error': f'Failed to get analyses: {str(e)}'}, 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)