import redis
import json
from datetime import datetime
from backend.run import Config


class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(Config.REDIS_URL, decode_responses=True)

    def create_analysis(self, post_url):
        """Create a new analysis entry"""
        analysis_id = f"analysis:{datetime.now().strftime('%Y%m%d%H%M%S')}:{hash(post_url) % 10000}"

        analysis_data = {
            'id': analysis_id,
            'post_url': post_url,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Store analysis
        self.redis.hset(analysis_id, mapping=analysis_data)

        # Add to analyses list (for history)
        self.redis.zadd('analyses:all', {analysis_id: datetime.now().timestamp()})

        # Set expiration (30 days)
        self.redis.expire(analysis_id, 30 * 24 * 60 * 60)

        return analysis_id

    def get_analysis(self, analysis_id):
        """Get analysis by ID"""
        data = self.redis.hgetall(analysis_id)
        if not data:
            return None

        # Get results if they exist
        results_key = f"{analysis_id}:results"
        results = self.redis.get(results_key)
        if results:
            data['results'] = json.loads(results)

        return data

    def update_analysis_status(self, analysis_id, status, results=None):
        """Update analysis status and optionally store results"""
        self.redis.hset(analysis_id, 'status', status)
        self.redis.hset(analysis_id, 'updated_at', datetime.now().isoformat())

        if results:
            results_key = f"{analysis_id}:results"
            self.redis.set(results_key, json.dumps(results))
            self.redis.expire(results_key, 30 * 24 * 60 * 60)

    def get_recent_analyses(self, limit=10):
        """Get recent analyses"""
        analysis_ids = self.redis.zrevrange('analyses:all', 0, limit - 1)
        analyses = []

        for analysis_id in analysis_ids:
            analysis = self.get_analysis(analysis_id)
            if analysis:
                analyses.append(analysis)

        return analyses


# Global instance
redis_client = RedisClient()