"""
Social media scraper module for LinkedIn and Facebook using official SDKs.
"""

import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger
import aiohttp
import json
import re
from datetime import datetime, timedelta
from linkedin import Linkedin  # LinkedIn official SDK
from facebook_sdk import GraphAPI  # Facebook official SDK
from .plugin_loader import BaseScraper, rate_limited

class SocialScraper(BaseScraper):
    """Social media scraper implementation using official SDKs."""

    def __init__(self, config: dict):
        """Initialize the social media scraper."""
        super().__init__(config)
        
        # Get social-specific settings
        social_config = config.get('social', {})
        self.platforms = social_config.get('platforms', ['linkedin', 'facebook'])
        self.max_posts = social_config.get('max_posts', 10)
        self.min_engagement = social_config.get('min_engagement', 50)
        self.time_filter = social_config.get('time_filter', 'week')
        self.min_credibility = social_config.get('min_credibility', 70)
        
        # Get authentication settings
        auth_config = social_config.get('auth', {})
        self.linkedin_config = auth_config.get('linkedin', {})
        self.facebook_config = auth_config.get('facebook', {})
        
        # Initialize clients
        self.linkedin_client = None
        self.facebook_client = None

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "social"

    async def _init_linkedin_client(self):
        """Initialize LinkedIn client with authentication."""
        if not self.linkedin_client and 'linkedin' in self.platforms:
            try:
                self.linkedin_client = Linkedin(
                    client_id=self.linkedin_config.get('client_id'),
                    client_secret=self.linkedin_config.get('client_secret'),
                    redirect_uri=self.linkedin_config.get('redirect_uri'),
                    access_token=self.linkedin_config.get('access_token')
                )
            except Exception as e:
                logger.error(f"Failed to initialize LinkedIn client: {str(e)}")

    async def _init_facebook_client(self):
        """Initialize Facebook client with authentication."""
        if not self.facebook_client and 'facebook' in self.platforms:
            try:
                self.facebook_client = GraphAPI(
                    access_token=self.facebook_config.get('access_token'),
                    version=self.facebook_config.get('api_version', '12.0')
                )
            except Exception as e:
                logger.error(f"Failed to initialize Facebook client: {str(e)}")

    async def validate(self) -> bool:
        """Validate the scraper configuration and authentication."""
        try:
            # Initialize clients
            await self._init_linkedin_client()
            await self._init_facebook_client()
            
            # Validate LinkedIn
            if 'linkedin' in self.platforms:
                if not self.linkedin_client:
                    logger.error("LinkedIn client not initialized")
                    return False
                # Test API access
                try:
                    self.linkedin_client.get_profile()
                except Exception as e:
                    logger.error(f"LinkedIn validation failed: {str(e)}")
                    return False
            
            # Validate Facebook
            if 'facebook' in self.platforms:
                if not self.facebook_client:
                    logger.error("Facebook client not initialized")
                    return False
                # Test API access
                try:
                    self.facebook_client.get_object('me')
                except Exception as e:
                    logger.error(f"Facebook validation failed: {str(e)}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Social scraper validation failed: {str(e)}")
            return False

    @rate_limited(max_per_second=2)
    async def _fetch_linkedin_posts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch posts from LinkedIn using official SDK."""
        if not self.linkedin_client:
            return []
            
        try:
            # Search for posts
            search_results = self.linkedin_client.search_posts(
                keywords=query,
                limit=self.max_posts,
                time_filter=self.time_filter
            )
            
            posts = []
            for post in search_results:
                engagement = (
                    post.get('numLikes', 0) +
                    post.get('numComments', 0) +
                    post.get('numShares', 0)
                )
                
                if engagement < self.min_engagement:
                    continue
                    
                processed_post = {
                    'title': post.get('title', ''),
                    'content': post.get('text', ''),
                    'author': post.get('author', {}).get('name', 'Unknown'),
                    'url': post.get('url', ''),
                    'source': 'linkedin',
                    'source_detail': f"LinkedIn - {post.get('author', {}).get('headline', '')}",
                    'credibility_info': {
                        'score': self._calculate_credibility(post),
                        'bias': 'Professional Network',
                        'category': 'Social Media'
                    },
                    'metadata': {
                        'likes': post.get('numLikes', 0),
                        'comments': post.get('numComments', 0),
                        'shares': post.get('numShares', 0),
                        'author_connections': post.get('author', {}).get('connections', 0)
                    }
                }
                posts.append(processed_post)
                
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching LinkedIn posts: {str(e)}")
            return []

    @rate_limited(max_per_second=2)
    async def _fetch_facebook_posts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch posts from Facebook using official SDK."""
        if not self.facebook_client:
            return []
            
        try:
            # Search for posts
            search_results = self.facebook_client.search(
                type='post',
                q=query,
                limit=self.max_posts,
                fields='id,message,from,created_time,reactions.summary(true),comments.summary(true),shares'
            )
            
            posts = []
            for post in search_results['data']:
                engagement = (
                    post.get('reactions', {}).get('summary', {}).get('total_count', 0) +
                    post.get('comments', {}).get('summary', {}).get('total_count', 0) +
                    post.get('shares', {}).get('count', 0)
                )
                
                if engagement < self.min_engagement:
                    continue
                    
                processed_post = {
                    'title': post.get('message', '')[:100] + '...' if len(post.get('message', '')) > 100 else post.get('message', ''),
                    'content': post.get('message', ''),
                    'author': post.get('from', {}).get('name', 'Unknown'),
                    'url': f"https://www.facebook.com/{post.get('id')}",
                    'source': 'facebook',
                    'source_detail': f"Facebook - {post.get('from', {}).get('name', '')}",
                    'credibility_info': {
                        'score': self._calculate_credibility(post),
                        'bias': 'Social Network',
                        'category': 'Social Media'
                    },
                    'metadata': {
                        'likes': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
                        'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                        'shares': post.get('shares', {}).get('count', 0)
                    }
                }
                posts.append(processed_post)
                
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching Facebook posts: {str(e)}")
            return []

    def _calculate_credibility(self, post: Dict[str, Any]) -> float:
        """Calculate credibility score for a social media post."""
        base_score = 70.0
        
        # Engagement metrics
        engagement_score = min((
            post.get('numLikes', 0) +
            post.get('numComments', 0) * 2 +
            post.get('numShares', 0) * 3
        ) / 100, 15)
        
        # Author credibility
        author_score = 0
        if 'author' in post:
            connections = post.get('author', {}).get('connections', 0)
            author_score = min(connections / 1000, 10)
            
            # Check for verification
            if post.get('author', {}).get('verified', False):
                author_score += 5
        
        # Content quality
        content_score = 0
        content = post.get('message', '') or post.get('text', '')
        if content:
            # Length score
            content_score += min(len(content.split()) / 50, 5)
            
            # Link presence
            if 'http' in content or 'https' in content:
                content_score += 2
            
            # Hashtag usage (not too many)
            hashtags = len(re.findall(r'#\w+', content))
            if 0 < hashtags <= 3:
                content_score += 1
            elif hashtags > 3:
                content_score -= 1
        
        total_score = base_score + engagement_score + author_score + content_score
        return min(max(total_score, 0), 100)

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape social media posts matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing post data
        """
        logger.info(f"Scraping social media for: {query}")
        
        try:
            # Initialize clients
            await self._init_linkedin_client()
            await self._init_facebook_client()
            
            tasks = []
            if 'linkedin' in self.platforms:
                tasks.append(self._fetch_linkedin_posts(query))
            if 'facebook' in self.platforms:
                tasks.append(self._fetch_facebook_posts(query))
            
            results = await asyncio.gather(*tasks)
            
            # Combine and sort results by credibility
            all_posts = []
            for platform_posts in results:
                all_posts.extend(platform_posts)
            
            # Filter by minimum credibility
            filtered_posts = [
                post for post in all_posts
                if post['credibility_info']['score'] >= self.min_credibility
            ]
            
            # Sort by credibility score
            sorted_posts = sorted(
                filtered_posts,
                key=lambda x: x['credibility_info']['score'],
                reverse=True
            )
            
            return sorted_posts[:self.max_posts]
            
        except Exception as e:
            logger.error(f"Error during social media scraping: {str(e)}")
            return []

    async def close(self):
        """Clean up resources."""
        # Nothing to clean up for SDK clients 