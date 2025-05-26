"""
Blog scraper module for various blog platforms (WordPress, Medium, etc.).
"""

import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger
import aiohttp
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import html
import json
import os
from urllib.parse import urljoin, urlparse
from .plugin_loader import BaseScraper, rate_limited

class BlogScraper(BaseScraper):
    """Blog scraper implementation."""

    def __init__(self, config: dict):
        """Initialize the blog scraper."""
        super().__init__(config)
        
        # Get blog-specific settings from the centralized config
        blog_config = config.get('scrapers', {}).get('blog', {})
        
        # Blog scraping settings
        self.max_results = blog_config.get('max_results', 10)
        self.min_words = blog_config.get('min_words', 500)
        self.time_filter = blog_config.get('time_filter', 'week')
        self.platforms = blog_config.get('platforms', ['wordpress', 'medium'])
        self.language = blog_config.get('language', 'en')
        self.sort_by = blog_config.get('sort_by', 'relevance')
        
        # Get API keys from environment variables first, then config
        self.wp_client_id = os.getenv('WP_CLIENT_ID') or blog_config.get('wordpress_client_id')
        self.wp_client_secret = os.getenv('WP_CLIENT_SECRET') or blog_config.get('wordpress_client_secret')
        self.wp_access_token = os.getenv('WP_ACCESS_TOKEN') or blog_config.get('wordpress_api_key')
        self.medium_token = os.getenv('MEDIUM_ACCESS_TOKEN') or blog_config.get('medium_api_key')
        
        # Cache settings from centralized config
        cache_config = config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', True)
        self.cache_duration = cache_config.get('duration', 3600)
        self.cache_location = os.path.join(cache_config.get('location', './cache'), 'blog')
        
        # Report settings from centralized config
        report_config = config.get('reporting', {})
        self.template_dir = report_config.get('template_dir', 'app/scraper/templates')
        self.report_output_dir = os.path.join(report_config.get('output_dir', './reports'), 'blog')
        
        # Initialize client
        self.http_client = None
        
        # Platform-specific API endpoints
        self.medium_api = "https://api.medium.com/v1"
        self.wordpress_api = "https://public-api.wordpress.com/rest/v1.1"

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "blog"

    async def _init_http_client(self):
        """Initialize aiohttp client with optimized settings."""
        if self.http_client is None:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            headers = {
                'User-Agent': self._get_user_agent()
            }
            
            # Add API authentication headers if available
            if self.medium_token:
                headers['Authorization'] = f'Bearer {self.medium_token}'
            if self.wp_access_token:
                headers['Authorization'] = f'Bearer {self.wp_access_token}'
                
            self.http_client = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )

    def _get_time_filter_date(self) -> str:
        """Convert time filter to ISO 8601 date string."""
        now = datetime.utcnow()
        
        if self.time_filter == 'hour':
            delta = timedelta(hours=1)
        elif self.time_filter == 'day':
            delta = timedelta(days=1)
        elif self.time_filter == 'week':
            delta = timedelta(weeks=1)
        elif self.time_filter == 'month':
            delta = timedelta(days=30)
        elif self.time_filter == 'year':
            delta = timedelta(days=365)
        else:
            delta = timedelta(weeks=1)  # default to week
            
        published_after = (now - delta).isoformat() + 'Z'
        return published_after

    def _calculate_credibility(self, blog_data: Dict[str, Any]) -> float:
        """Calculate credibility score for a blog post."""
        base_score = 70.0
        
        # Content quality score (up to 10 points)
        content_score = 0
        word_count = blog_data.get('word_count', 0)
        if word_count > self.min_words:
            content_score += min(word_count / 1000, 5)  # Up to 5 points for length
        if blog_data.get('has_images', False):
            content_score += 2
        if blog_data.get('has_references', False):
            content_score += 3
            
        # Author credibility (up to 10 points)
        author_score = 0
        if blog_data.get('author_verified', False):
            author_score += 5
        follower_count = blog_data.get('author_followers', 0)
        author_score += min(follower_count / 1000, 5)
        
        # Engagement score (up to 5 points)
        engagement_score = 0
        likes = blog_data.get('likes', 0)
        comments = blog_data.get('comments', 0)
        shares = blog_data.get('shares', 0)
        total_engagement = likes + comments + shares
        engagement_score = min(total_engagement / 100, 5)
        
        # Platform credibility (up to 5 points)
        platform_score = 0
        domain = urlparse(blog_data.get('url', '')).netloc
        if domain.endswith(('medium.com', 'wordpress.com')):
            platform_score += 3
        if blog_data.get('is_publication', False):
            platform_score += 2
            
        total_score = base_score + content_score + author_score + engagement_score + platform_score
        return min(max(total_score, 0), 100)

    @rate_limited(max_per_second=2)
    async def _fetch_wordpress_posts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch blog posts from WordPress."""
        try:
            params = {
                'search': query,
                'number': self.max_results,
                'after': self._get_time_filter_date(),
                'order_by': self.sort_by,
                'language': self.language
            }
            
            async with self.http_client.get(f"{self.wordpress_api}/posts", params=params) as response:
                if response.status == 200:
                    posts = await response.json()
                    return posts
                return []
                
        except Exception as e:
            logger.error(f"Error fetching WordPress posts: {str(e)}")
            return []

    @rate_limited(max_per_second=2)
    async def _fetch_medium_posts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch blog posts from Medium."""
        try:
            params = {
                'q': query,
                'limit': self.max_results,
                'format': 'json'
            }
            
            async with self.http_client.get(f"{self.medium_api}/search", params=params) as response:
                if response.status == 200:
                    posts = await response.json()
                    return posts.get('data', [])
                return []
                
        except Exception as e:
            logger.error(f"Error fetching Medium posts: {str(e)}")
            return []

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            await self._init_http_client()
            valid = True
            
            # Validate WordPress credentials if platform is enabled
            if 'wordpress' in self.platforms:
                if not (self.wp_client_id and self.wp_client_secret and self.wp_access_token):
                    logger.warning("WordPress API credentials missing. Please set WP_CLIENT_ID, WP_CLIENT_SECRET, and WP_ACCESS_TOKEN")
                    logger.warning("Get credentials from: https://developer.wordpress.com/apps/")
                    valid = False
                else:
                    # Test WordPress API access
                    wp_response = await self._fetch_wordpress_posts("test")
                    if not isinstance(wp_response, list):
                        logger.error("WordPress API validation failed")
                        valid = False
            
            # Validate Medium credentials if platform is enabled
            if 'medium' in self.platforms:
                if not self.medium_token:
                    logger.warning("Medium API token missing. Please set MEDIUM_ACCESS_TOKEN")
                    logger.warning("Get token from: https://medium.com/me/settings (Integration tokens)")
                    valid = False
                else:
                    # Test Medium API access
                    medium_response = await self._fetch_medium_posts("test")
                    if not isinstance(medium_response, list):
                        logger.error("Medium API validation failed")
                        valid = False
            
            if valid:
                logger.info("Blog scraper validation successful")
            return valid
            
        except Exception as e:
            logger.error(f"Blog scraper validation failed: {str(e)}")
            return False

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape blog posts matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing blog post data
        """
        logger.info(f"Scraping blogs for: {query}")
        
        try:
            await self._init_http_client()
            all_posts = []
            
            # Fetch WordPress posts
            if 'wordpress' in self.platforms:
                wp_posts = await self._fetch_wordpress_posts(query)
                for post in wp_posts:
                    # Process WordPress post data
                    processed_post = {
                        'title': html.unescape(post.get('title', {}).get('rendered', '')),
                        'description': html.unescape(post.get('excerpt', {}).get('rendered', '')),
                        'url': post.get('link', ''),
                        'author_name': post.get('_embedded', {}).get('author', [{}])[0].get('name', ''),
                        'author_url': post.get('_embedded', {}).get('author', [{}])[0].get('url', ''),
                        'published_at': post.get('date', ''),
                        'source': 'wordpress',
                        'source_detail': f"WordPress - {urlparse(post.get('link', '')).netloc}",
                        'metadata': {
                            'word_count': len(post.get('content', {}).get('rendered', '').split()),
                            'likes': post.get('like_count', 0),
                            'comments': post.get('comment_count', 0),
                            'shares': post.get('share_count', 0)
                        }
                    }
                    processed_post['credibility_info'] = {
                        'score': self._calculate_credibility(processed_post),
                        'bias': 'User Generated Content',
                        'category': 'Blog Platform'
                    }
                    all_posts.append(processed_post)
            
            # Fetch Medium posts
            if 'medium' in self.platforms:
                medium_posts = await self._fetch_medium_posts(query)
                for post in medium_posts:
                    # Process Medium post data
                    processed_post = {
                        'title': html.unescape(post.get('title', '')),
                        'description': html.unescape(post.get('subtitle', '')),
                        'url': post.get('url', ''),
                        'author_name': post.get('author', {}).get('name', ''),
                        'author_url': post.get('author', {}).get('url', ''),
                        'published_at': post.get('publishedAt', ''),
                        'source': 'medium',
                        'source_detail': f"Medium - {post.get('publication', {}).get('name', 'Personal Blog')}",
                        'metadata': {
                            'word_count': post.get('wordCount', 0),
                            'likes': post.get('claps', 0),
                            'comments': post.get('responses', 0),
                            'shares': post.get('shareCount', 0)
                        }
                    }
                    processed_post['credibility_info'] = {
                        'score': self._calculate_credibility(processed_post),
                        'bias': 'User Generated Content',
                        'category': 'Blog Platform'
                    }
                    all_posts.append(processed_post)
            
            # Sort by credibility score
            sorted_posts = sorted(
                all_posts,
                key=lambda x: x['credibility_info']['score'],
                reverse=True
            )
            
            return sorted_posts
            
        except Exception as e:
            logger.error(f"Error during blog scraping: {str(e)}")
            return []

    async def close(self):
        """Clean up resources."""
        if self.http_client:
            await self.http_client.close()
