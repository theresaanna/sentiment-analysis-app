# tasks/instagram_sentiment_tasks.py
from celery import Celery
from typing import Dict, Optional, Any, List
import json
import time
from datetime import datetime
import logging
import traceback

# Import your Instagram parser
from utils.instagram_parser import InstagramURLParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery app configuration
celery_app = Celery(
    'instagram_sentiment_analyzer',
    broker='redis://redis:6379/0',  # Use redis service name for Docker
    backend='redis://redis:6379/0'
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,  # Results expire after 1 hour
    task_routes={
        'tasks.instagram_sentiment_tasks.analyze_instagram_post': {'queue': 'instagram_queue'},
        'tasks.instagram_sentiment_tasks.batch_analyze_instagram': {'queue': 'batch_queue'},
    }
)


@celery_app.task(bind=True, name='analyze_instagram_post')
def analyze_instagram_post(self, instagram_url: str, user_id: Optional[str] = None,
                           options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Celery task to analyze sentiment of an Instagram post.

    Args:
        self: Celery task instance
        instagram_url: Instagram post URL
        user_id: Optional user ID for tracking
        options: Additional analysis options

    Returns:
        Dict containing analysis results
    """

    task_id = self.request.id
    options = options or {}

    try:
        logger.info(f"Starting Instagram sentiment analysis for URL: {instagram_url}")

        # Update task state to PROGRESS - URL Parsing
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Parsing Instagram URL...',
                'progress': 5,
                'step': 'url_parsing',
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Parse Instagram URL
        url_details = InstagramURLParser.parse_url_details(instagram_url)

        if not url_details['is_valid']:
            raise ValueError(f"Invalid Instagram URL: {url_details.get('error', 'Unknown error')}")

        post_id = url_details['post_id']
        normalized_url = url_details['normalized_url']
        post_type = url_details['post_type']

        logger.info(f"Successfully parsed URL. Post ID: {post_id}, Type: {post_type}")

        # Update progress - Post Data Fetching
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Fetching {post_type} data...',
                'progress': 20,
                'step': 'data_fetching',
                'post_id': post_id,
                'post_type': post_type,
                'normalized_url': normalized_url,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Simulate fetching Instagram post data
        # In a real implementation, you'd use Instagram's API or web scraping
        time.sleep(2)  # Simulate API call delay

        # Mock post data - replace with actual Instagram API call
        post_data = {
            'id': post_id,
            'type': post_type,
            'url': normalized_url,
            'caption': f'Sample {post_type} caption for sentiment analysis! 🎉 This is amazing content! #positive #sentiment',
            'likes': 1250,
            'comments_count': 45,
            'timestamp': '2025-09-01T10:00:00Z',
            'author': {
                'username': 'sample_user',
                'followers': 10000
            }
        }

        # Update progress - Comments Fetching
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Fetching comments...',
                'progress': 40,
                'step': 'comments_fetching',
                'post_data': post_data,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Simulate fetching comments
        time.sleep(3)

        # Mock comments data - replace with actual comment fetching
        comments_data = [
            {'id': '1', 'text': 'This is amazing! Love it! 😍', 'author': 'user1', 'likes': 5},
            {'id': '2', 'text': 'Great content as always!', 'author': 'user2', 'likes': 3},
            {'id': '3', 'text': 'Not sure about this one...', 'author': 'user3', 'likes': 1},
            {'id': '4', 'text': 'Terrible quality, disappointed 😞', 'author': 'user4', 'likes': 0},
            {'id': '5', 'text': 'Perfect! Exactly what I needed! 👌', 'author': 'user5', 'likes': 8},
        ]

        total_comments = len(comments_data)
        max_comments = options.get('max_comments', 50)

        # Update progress - Sentiment Analysis
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Analyzing sentiment...',
                'progress': 65,
                'step': 'sentiment_analysis',
                'comments_fetched': total_comments,
                'max_comments': max_comments,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Simulate sentiment analysis processing
        time.sleep(4)

        # Mock sentiment analysis results - replace with actual ML model
        comment_sentiments = []
        overall_positive = 0
        overall_negative = 0
        overall_neutral = 0

        for comment in comments_data:
            # Simple mock sentiment classification
            text = comment['text'].lower()
            if any(word in text for word in ['amazing', 'great', 'love', 'perfect', '😍', '👌']):
                sentiment = 'positive'
                confidence = 0.85 + (len([w for w in ['amazing', 'great', 'love', 'perfect'] if w in text]) * 0.05)
                overall_positive += 1
            elif any(word in text for word in ['terrible', 'disappointed', 'bad', '😞']):
                sentiment = 'negative'
                confidence = 0.80
                overall_negative += 1
            else:
                sentiment = 'neutral'
                confidence = 0.65
                overall_neutral += 1

            comment_sentiments.append({
                'comment_id': comment['id'],
                'text': comment['text'],
                'author': comment['author'],
                'likes': comment['likes'],
                'sentiment': sentiment,
                'confidence': min(confidence, 0.95)
            })

        # Calculate overall sentiment metrics
        total_analyzed = len(comment_sentiments)
        sentiment_summary = {
            'total_comments': total_analyzed,
            'positive': overall_positive,
            'negative': overall_negative,
            'neutral': overall_neutral,
            'positive_percentage': round((overall_positive / total_analyzed) * 100, 2) if total_analyzed > 0 else 0,
            'negative_percentage': round((overall_negative / total_analyzed) * 100, 2) if total_analyzed > 0 else 0,
            'neutral_percentage': round((overall_neutral / total_analyzed) * 100, 2) if total_analyzed > 0 else 0,
        }

        # Determine overall post sentiment
        if overall_positive > overall_negative and overall_positive > overall_neutral:
            overall_sentiment = 'positive'
        elif overall_negative > overall_positive and overall_negative > overall_neutral:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'

        # Update progress - Finalizing
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Finalizing analysis...',
                'progress': 95,
                'step': 'finalizing',
                'sentiment_summary': sentiment_summary,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Final result compilation
        final_result = {
            'task_id': task_id,
            'success': True,
            'instagram_url': instagram_url,
            'url_details': url_details,
            'post_data': post_data,
            'sentiment_analysis': {
                'overall_sentiment': overall_sentiment,
                'summary': sentiment_summary,
                'comment_sentiments': comment_sentiments,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'model_version': 'mock_v1.0',  # Replace with actual model version
                'options_used': options
            },
            'metadata': {
                'user_id': user_id,
                'processing_time_seconds': time.time() - self.request.kwargs.get('start_time', time.time()),
                'processed_at': datetime.utcnow().isoformat(),
                'task_queue': 'instagram_queue'
            }
        }

        logger.info(f"Successfully completed sentiment analysis for post {post_id}")
        return final_result

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in analyze_instagram_post: {error_msg}\n{error_trace}")

        # Update task state to FAILURE
        self.update_state(
            state='FAILURE',
            meta={
                'status': f'Analysis failed: {error_msg}',
                'error': error_msg,
                'error_type': type(e).__name__,
                'traceback': error_trace,
                'instagram_url': instagram_url,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Re-raise the exception for Celery to handle
        raise


@celery_app.task(bind=True, name='batch_analyze_instagram')
def batch_analyze_instagram(self, instagram_urls: List[str], user_id: Optional[str] = None,
                            options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Celery task to analyze sentiment of multiple Instagram posts.

    Args:
        self: Celery task instance
        instagram_urls: List of Instagram post URLs
        user_id: Optional user ID for tracking
        options: Additional analysis options

    Returns:
        Dict containing batch analysis results
    """

    task_id = self.request.id
    total_urls = len(instagram_urls)
    options = options or {}
    results = []

    try:
        logger.info(f"Starting batch Instagram sentiment analysis for {total_urls} URLs")

        for i, url in enumerate(instagram_urls):
            current_progress = int((i / total_urls) * 90)  # Reserve 10% for final processing

            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Processing URL {i + 1} of {total_urls}',
                    'progress': current_progress,
                    'current_url': url,
                    'completed': i,
                    'total': total_urls,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            # Process individual post
            try:
                # Use .apply_async() to process each URL as a subtask
                subtask_result = analyze_instagram_post.apply_async(
                    args=[url, user_id, options],
                    countdown=i * 2  # Stagger requests to avoid rate limiting
                )

                # Wait for subtask completion (with timeout)
                result = subtask_result.get(timeout=300)  # 5 minute timeout per URL
                results.append({
                    'url': url,
                    'status': 'success',
                    'result': result
                })

                logger.info(f"Successfully processed URL {i + 1}/{total_urls}: {url}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to process URL {i + 1}/{total_urls}: {url} - {error_msg}")

                results.append({
                    'url': url,
                    'status': 'failed',
                    'error': error_msg,
                    'error_type': type(e).__name__
                })

        # Final processing and aggregation
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Aggregating batch results...',
                'progress': 95,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Calculate batch statistics
        successful_results = [r for r in results if r['status'] == 'success']
        failed_results = [r for r in results if r['status'] == 'failed']

        # Aggregate sentiment statistics
        total_positive = sum(
            r['result']['sentiment_analysis']['summary']['positive']
            for r in successful_results
        )
        total_negative = sum(
            r['result']['sentiment_analysis']['summary']['negative']
            for r in successful_results
        )
        total_neutral = sum(
            r['result']['sentiment_analysis']['summary']['neutral']
            for r in successful_results
        )
        total_comments = total_positive + total_negative + total_neutral

        batch_result = {
            'task_id': task_id,
            'success': True,
            'batch_summary': {
                'total_urls': total_urls,
                'successful': len(successful_results),
                'failed': len(failed_results),
                'success_rate': round((len(successful_results) / total_urls) * 100, 2),
                'total_comments_analyzed': total_comments,
                'aggregate_sentiment': {
                    'positive': total_positive,
                    'negative': total_negative,
                    'neutral': total_neutral,
                    'positive_percentage': round((total_positive / total_comments) * 100,
                                                 2) if total_comments > 0 else 0,
                    'negative_percentage': round((total_negative / total_comments) * 100,
                                                 2) if total_comments > 0 else 0,
                    'neutral_percentage': round((total_neutral / total_comments) * 100, 2) if total_comments > 0 else 0,
                }
            },
            'individual_results': results,
            'metadata': {
                'user_id': user_id,
                'options_used': options,
                'processed_at': datetime.utcnow().isoformat(),
                'task_queue': 'batch_queue'
            }
        }

        logger.info(f"Successfully completed batch analysis: {len(successful_results)}/{total_urls} URLs processed")
        return batch_result

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in batch_analyze_instagram: {error_msg}\n{error_trace}")

        self.update_state(
            state='FAILURE',
            meta={
                'status': f'Batch analysis failed: {error_msg}',
                'error': error_msg,
                'error_type': type(e).__name__,
                'traceback': error_trace,
                'instagram_urls': instagram_urls,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        raise


# Flask routes for task management
def create_task_management_routes(app):
    """
    Create Flask routes for managing Instagram sentiment analysis tasks.

    Args:
        app: Flask application instance
    """

    @app.route('/api/sentiment/instagram/analyze', methods=['POST'])
    def start_instagram_analysis():
        """
        Start Instagram sentiment analysis task.

        Expected JSON payload:
        {
            "url": "https://www.instagram.com/p/ABC123/",
            "user_id": "optional_user_id",
            "options": {
                "max_comments": 50,
                "include_replies": true
            }
        }

        Returns:
        JSON response with task ID and status
        """
        from flask import request, jsonify

        try:
            data = request.get_json()

            if not data or 'url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Instagram URL is required',
                    'example': {
                        'url': 'https://www.instagram.com/p/ABC123/',
                        'user_id': 'optional_user_id',
                        'options': {'max_comments': 50}
                    }
                }), 400

            instagram_url = data['url'].strip()
            user_id = data.get('user_id')
            options = data.get('options', {})

            # Validate URL before starting task
            if not InstagramURLParser.is_valid_instagram_url(instagram_url):
                return jsonify({
                    'success': False,
                    'error': 'Invalid Instagram URL provided',
                    'url': instagram_url
                }), 400

            # Start Celery task
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
            logger.error(f"Error starting Instagram analysis: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to start analysis: {str(e)}'
            }), 500

    @app.route('/api/sentiment/instagram/batch', methods=['POST'])
    def start_batch_instagram_analysis():
        """
        Start batch Instagram sentiment analysis task.

        Expected JSON payload:
        {
            "urls": [
                "https://www.instagram.com/p/ABC123/",
                "https://www.instagram.com/reel/DEF456/"
            ],
            "user_id": "optional_user_id",
            "options": {
                "max_comments": 50
            }
        }
        """
        from flask import request, jsonify

        try:
            data = request.get_json()

            if not data or 'urls' not in data:
                return jsonify({
                    'success': False,
                    'error': 'URLs array is required',
                    'example': {
                        'urls': [
                            'https://www.instagram.com/p/ABC123/',
                            'https://www.instagram.com/reel/DEF456/'
                        ]
                    }
                }), 400

            urls = data['urls']
            user_id = data.get('user_id')
            options = data.get('options', {})

            # Validate URLs
            if not isinstance(urls, list) or len(urls) == 0:
                return jsonify({
                    'success': False,
                    'error': 'URLs must be a non-empty array'
                }), 400

            if len(urls) > 10:  # Limit batch size
                return jsonify({
                    'success': False,
                    'error': 'Maximum 10 URLs allowed per batch'
                }), 400

            # Validate each URL
            invalid_urls = []
            for url in urls:
                if not InstagramURLParser.is_valid_instagram_url(url):
                    invalid_urls.append(url)

            if invalid_urls:
                return jsonify({
                    'success': False,
                    'error': 'Invalid Instagram URLs found',
                    'invalid_urls': invalid_urls
                }), 400

            # Start batch Celery task
            task = batch_analyze_instagram.apply_async(
                args=[urls, user_id, options]
            )

            logger.info(f"Started batch Instagram sentiment analysis task {task.id} for {len(urls)} URLs")

            return jsonify({
                'success': True,
                'task_id': task.id,
                'status': 'started',
                'message': f'Batch Instagram sentiment analysis started for {len(urls)} URLs',
                'urls_count': len(urls),
                'estimated_completion': f'{len(urls) * 2}-{len(urls) * 5} minutes'
            })

        except Exception as e:
            logger.error(f"Error starting batch Instagram analysis: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to start batch analysis: {str(e)}'
            }), 500

    @app.route('/api/task/status/<task_id>', methods=['GET'])
    def get_task_status(task_id):
        """
        Get status of a running task.

        Returns:
        JSON response with current task status and progress
        """
        from flask import jsonify

        try:
            task = celery_app.AsyncResult(task_id)

            if task.state == 'PENDING':
                response = {
                    'task_id': task_id,
                    'state': task.state,
                    'status': 'Task is waiting to be processed',
                    'progress': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            elif task.state == 'PROGRESS':
                response = {
                    'task_id': task_id,
                    'state': task.state,
                    'progress': task.info.get('progress', 0),
                    'status': task.info.get('status', 'Processing...'),
                    'step': task.info.get('step', 'unknown'),
                    'timestamp': task.info.get('timestamp', datetime.utcnow().isoformat()),
                    **{k: v for k, v in task.info.items() if k not in ['progress', 'status', 'step', 'timestamp']}
                }
            elif task.state == 'SUCCESS':
                response = {
                    'task_id': task_id,
                    'state': task.state,
                    'progress': 100,
                    'status': 'Task completed successfully',
                    'result': task.result,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:  # FAILURE, RETRY, REVOKED
                response = {
                    'task_id': task_id,
                    'state': task.state,
                    'progress': 0,
                    'status': f'Task {task.state.lower()}',
                    'error': str(task.info) if hasattr(task.info, '__str__') else 'Unknown error',
                    'timestamp': datetime.utcnow().isoformat()
                }

                if hasattr(task.info, 'get'):
                    response.update({
                        'error_type': task.info.get('error_type', 'Unknown'),
                        'error_details': task.info.get('error', 'No details available')
                    })

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return jsonify({
                'task_id': task_id,
                'error': f'Failed to get task status: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }), 500

    @app.route('/api/task/cancel/<task_id>', methods=['POST'])
    def cancel_task(task_id):
        """
        Cancel a running task.
        """
        from flask import jsonify

        try:
            task = celery_app.AsyncResult(task_id)

            if task.state in ['PENDING', 'PROGRESS']:
                task.revoke(terminate=True)

                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'Task cancelled successfully',
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'task_id': task_id,
                    'error': f'Cannot cancel task in state: {task.state}',
                    'timestamp': datetime.utcnow().isoformat()
                }), 400

        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return jsonify({
                'success': False,
                'task_id': task_id,
                'error': f'Failed to cancel task: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }), 500

    @app.route('/api/tasks/active', methods=['GET'])
    def get_active_tasks():
        """
        Get list of currently active tasks.
        """
        from flask import jsonify, request

        try:
            # Get optional user_id filter
            user_id = request.args.get('user_id')

            # Get active tasks from Celery
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()

            if not active_tasks:
                return jsonify({
                    'success': True,
                    'active_tasks': [],
                    'count': 0,
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Flatten and format active tasks
            formatted_tasks = []
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    task_info = {
                        'task_id': task['id'],
                        'name': task['name'],
                        'worker': worker,
                        'args': task.get('args', []),
                        'kwargs': task.get('kwargs', {}),
                        'time_start': task.get('time_start')
                    }

                    # Filter by user_id if provided
                    if user_id:
                        task_args = task.get('args', [])
                        task_kwargs = task.get('kwargs', {})

                        # Check if user_id matches (assuming user_id is second argument)
                        if len(task_args) > 1 and task_args[1] == user_id:
                            formatted_tasks.append(task_info)
                        elif task_kwargs.get('user_id') == user_id:
                            formatted_tasks.append(task_info)
                    else:
                        formatted_tasks.append(task_info)

            return jsonify({
                'success': True,
                'active_tasks': formatted_tasks,
                'count': len(formatted_tasks),
                'user_id_filter': user_id,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error getting active tasks: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to get active tasks: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }), 500


# Health check and monitoring endpoints
def create_monitoring_routes(app):
    """
    Create monitoring and health check routes.
    """

    @app.route('/api/health/celery', methods=['GET'])
    def celery_health_check():
        """
        Check Celery worker health and connectivity.
        """
        from flask import jsonify

        try:
            # Check if Celery workers are available
            inspect = celery_app.control.inspect()

            # Get worker stats
            stats = inspect.stats()
            active = inspect.active()

            if not stats:
                return jsonify({
                    'success': False,
                    'status': 'unhealthy',
                    'error': 'No Celery workers available',
                    'timestamp': datetime.utcnow().isoformat()
                }), 503

            worker_count = len(stats)
            active_tasks_count = sum(len(tasks) for tasks in active.values()) if active else 0

            return jsonify({
                'success': True,
                'status': 'healthy',
                'workers': {
                    'count': worker_count,
                    'names': list(stats.keys()),
                    'active_tasks': active_tasks_count
                },
                'broker': {
                    'type': 'redis',
                    'status': 'connected'
                },
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Celery health check failed: {str(e)}")
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503


if __name__ == "__main__":
    print("Instagram Sentiment Analysis Celery Tasks")
    print("=" * 50)
    print("Make sure Redis is running and start Celery workers with:")
    print("celery -A tasks.instagram_sentiment_tasks worker --loglevel=info --queues=instagram_queue,batch_queue")
    print("\nTo monitor tasks, start Celery Flower with:")
    print("celery -A tasks.instagram_sentiment_tasks flower")
    print("\nHealth check endpoint: /api/health/celery")