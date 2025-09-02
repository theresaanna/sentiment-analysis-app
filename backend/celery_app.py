from celery import Celery
import os
import time
import random

# Create Celery instance
celery_app = Celery(
    'sentiment_analyzer',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
)


@celery_app.task(bind=True)
def analyze_sentiment_task(self, analysis_id, post_url):
    """Background task to analyze Instagram post sentiment"""
    try:
        # Simulate the sentiment analysis process
        print(f"Starting analysis for {analysis_id}: {post_url}")

        # Simulate processing time
        for i in range(5):
            time.sleep(1)
            print(f"Processing... {i + 1}/5")

            # Update progress (optional)
            self.update_state(
                state='PROGRESS',
                meta={'current': i + 1, 'total': 5, 'status': f'Processing step {i + 1}'}
            )

        # Simulate results
        results = {
            'total_comments': random.randint(20, 100),
            'sentiment_breakdown': {
                'positive': random.randint(10, 50),
                'negative': random.randint(5, 20),
                'neutral': random.randint(5, 30)
            },
            'average_sentiment': round(random.uniform(0.3, 0.8), 2),
            'top_keywords': ['amazing', 'love', 'beautiful', 'great', 'awesome'][:random.randint(3, 5)],
            'comments_sample': [
                {
                    'text': 'This is amazing! Love it!',
                    'sentiment': 'positive',
                    'confidence': 0.95
                },
                {
                    'text': 'Not really my style',
                    'sentiment': 'negative',
                    'confidence': 0.72
                }
            ]
        }

        print(f"Completed analysis for {analysis_id}")
        return {
            'status': 'completed',
            'analysis_id': analysis_id,
            'results': results
        }

    except Exception as e:
        print(f"Task failed: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task
def test_task(message):
    """Simple test task"""
    time.sleep(2)
    return f"Test completed: {message}"