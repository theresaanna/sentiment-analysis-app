# utils/instagram_parser.py
import re
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstagramURLParser:
    """
    A utility class to parse Instagram post IDs from various URL formats.
    Supports posts, reels, TV/IGTV, and stories.
    """

    # Instagram URL patterns - comprehensive list
    INSTAGRAM_PATTERNS = [
        # Standard post URLs
        r'https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)',
        r'https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)',
        r'https?://(?:www\.)?instagram\.com/tv/([A-Za-z0-9_-]+)',

        # Mobile URLs
        r'https?://(?:m\.)?instagram\.com/p/([A-Za-z0-9_-]+)',
        r'https?://(?:m\.)?instagram\.com/reel/([A-Za-z0-9_-]+)',

        # Short URLs
        r'https?://instagr\.am/p/([A-Za-z0-9_-]+)',

        # URLs with additional parameters
        r'https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)/?\?.*',
        r'https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)/?\?.*',
    ]

    # Valid Instagram post ID pattern
    POST_ID_PATTERN = r'^[A-Za-z0-9_-]{11}$'

    @classmethod
    def extract_post_id(cls, url: str) -> Optional[str]:
        """
        Extract Instagram post ID from a given URL.

        Args:
            url (str): Instagram post URL

        Returns:
            Optional[str]: Post ID if found and valid, None otherwise
        """
        if not url or not isinstance(url, str):
            logger.warning("Invalid URL provided: empty or non-string")
            return None

        # Clean the URL
        url = url.strip()

        logger.info(f"Attempting to extract post ID from: {url}")

        # Try each pattern
        for pattern in cls.INSTAGRAM_PATTERNS:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                post_id = match.group(1)

                # Validate post ID format
                if re.match(cls.POST_ID_PATTERN, post_id):
                    logger.info(f"Successfully extracted post ID: {post_id}")
                    return post_id
                else:
                    logger.warning(f"Invalid post ID format: {post_id}")

        logger.warning(f"No valid post ID found in URL: {url}")
        return None

    @classmethod
    def is_valid_instagram_url(cls, url: str) -> bool:
        """
        Check if the URL is a valid Instagram post URL.

        Args:
            url (str): URL to validate

        Returns:
            bool: True if valid Instagram URL, False otherwise
        """
        return cls.extract_post_id(url) is not None

    @classmethod
    def normalize_url(cls, url: str) -> Optional[str]:
        """
        Normalize an Instagram URL to a standard format.

        Args:
            url (str): Instagram URL

        Returns:
            Optional[str]: Normalized URL if valid, None otherwise
        """
        post_id = cls.extract_post_id(url)
        if post_id:
            return f"https://www.instagram.com/p/{post_id}/"
        return None

    @classmethod
    def parse_url_details(cls, url: str) -> Dict[str, Any]:
        """
        Parse Instagram URL and return detailed information.

        Args:
            url (str): Instagram URL

        Returns:
            Dict[str, Any]: Dictionary containing parsed URL details
        """
        result = {
            'original_url': url,
            'is_valid': False,
            'post_id': None,
            'normalized_url': None,
            'post_type': None,
            'parameters': {},
            'error': None
        }

        try:
            if not url or not isinstance(url, str):
                result['error'] = 'Invalid URL: empty or non-string'
                return result

            # Extract post ID
            post_id = cls.extract_post_id(url)
            if not post_id:
                result['error'] = 'Invalid Instagram URL or post ID not found'
                return result

            # Determine post type
            post_type = 'post'  # default
            if '/reel/' in url:
                post_type = 'reel'
            elif '/tv/' in url:
                post_type = 'tv'

            # Parse URL parameters
            parsed_url = urlparse(url)
            parameters = parse_qs(parsed_url.query)

            # Update result
            result.update({
                'is_valid': True,
                'post_id': post_id,
                'normalized_url': f"https://www.instagram.com/p/{post_id}/",
                'post_type': post_type,
                'parameters': parameters
            })

        except Exception as e:
            result['error'] = f"Parsing error: {str(e)}"
            logger.error(f"Error parsing URL {url}: {str(e)}")

        return result

    @classmethod
    def get_post_url_from_id(cls, post_id: str) -> Optional[str]:
        """
        Generate Instagram post URL from post ID.

        Args:
            post_id (str): Instagram post ID

        Returns:
            Optional[str]: Instagram post URL if valid post ID, None otherwise
        """
        if post_id and re.match(cls.POST_ID_PATTERN, post_id):
            return f"https://www.instagram.com/p/{post_id}/"
        return None


# Flask route handlers for Instagram URL parsing
def create_instagram_parser_routes(app):
    """
    Create Flask routes for Instagram URL parsing functionality.

    Args:
        app: Flask application instance
    """

    @app.route('/api/instagram/parse', methods=['POST'])
    def parse_instagram_url():
        """
        Parse Instagram URL and extract post details.

        Expected JSON payload:
        {
            "url": "https://www.instagram.com/p/ABC123/"
        }

        Returns:
        JSON response with parsed URL details
        """
        from flask import request, jsonify

        try:
            data = request.get_json()

            if not data or 'url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'URL is required in request body',
                    'example': {
                        'url': 'https://www.instagram.com/p/ABC123/'
                    }
                }), 400

            url = data['url']
            result = InstagramURLParser.parse_url_details(url)

            if result['is_valid']:
                return jsonify({
                    'success': True,
                    'data': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Invalid Instagram URL'),
                    'data': result
                }), 400

        except Exception as e:
            logger.error(f"Error in parse_instagram_url: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500

    @app.route('/api/instagram/validate', methods=['POST'])
    def validate_instagram_url():
        """
        Validate Instagram URL without full parsing.

        Expected JSON payload:
        {
            "url": "https://www.instagram.com/p/ABC123/"
        }

        Returns:
        JSON response with validation result
        """
        from flask import request, jsonify

        try:
            data = request.get_json()

            if not data or 'url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'URL is required in request body'
                }), 400

            url = data['url']
            is_valid = InstagramURLParser.is_valid_instagram_url(url)
            post_id = InstagramURLParser.extract_post_id(url) if is_valid else None

            return jsonify({
                'success': True,
                'is_valid': is_valid,
                'url': url,
                'post_id': post_id
            })

        except Exception as e:
            logger.error(f"Error in validate_instagram_url: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500

    @app.route('/api/instagram/normalize', methods=['POST'])
    def normalize_instagram_url():
        """
        Normalize Instagram URL to standard format.
        """
        from flask import request, jsonify

        try:
            data = request.get_json()

            if not data or 'url' not in data:
                return jsonify({
                    'success': False,
                    'error': 'URL is required in request body'
                }), 400

            url = data['url']
            normalized_url = InstagramURLParser.normalize_url(url)

            if normalized_url:
                return jsonify({
                    'success': True,
                    'original_url': url,
                    'normalized_url': normalized_url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid Instagram URL - cannot normalize'
                }), 400

        except Exception as e:
            logger.error(f"Error in normalize_instagram_url: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Server error: {str(e)}'
            }), 500


# Example usage and testing
if __name__ == "__main__":
    # Test cases for Instagram URL parsing
    test_urls = [
        "https://www.instagram.com/p/ABC123/",
        "https://instagram.com/p/XYZ789/",
        "https://www.instagram.com/reel/DEF456/",
        "https://instagram.com/reel/GHI789/",
        "https://www.instagram.com/tv/JKL012/",
        "https://m.instagram.com/p/MNO345/",
        "https://www.instagram.com/p/ABC123/?utm_source=ig_web_copy_link",
        "https://www.instagram.com/p/ABC123/?igshid=abc123",
        "https://instagr.am/p/PQR678/",
        "invalid_url",
        "",
        None,
        "https://www.instagram.com/some_user/",  # Profile URL (should be invalid)
        "https://www.instagram.com/p/invalid_id_format/",  # Invalid ID format
    ]

    print("Testing Instagram URL Parser:")
    print("=" * 60)

    for url in test_urls:
        print(f"\nURL: {url}")

        # Test basic extraction
        post_id = InstagramURLParser.extract_post_id(url)
        is_valid = InstagramURLParser.is_valid_instagram_url(url)
        normalized = InstagramURLParser.normalize_url(url)

        print(f"  Post ID: {post_id}")
        print(f"  Valid: {is_valid}")
        print(f"  Normalized: {normalized}")

        # Test detailed parsing
        if url:
            details = InstagramURLParser.parse_url_details(url)
            print(f"  Details: {details}")

        print("-" * 40)