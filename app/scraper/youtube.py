"""
YouTube scraper module using the official YouTube Data API v3.
"""

import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger
import aiohttp
from datetime import datetime, timedelta
from .plugin_loader import BaseScraper, rate_limited
import isodate
import html
import json
import os
from urllib.parse import urlencode

class YouTubeScraper(BaseScraper):
    """YouTube scraper implementation."""

    def __init__(self, config: dict):
        """Initialize the YouTube scraper."""
        super().__init__(config)
        
        # Get YouTube-specific settings from the centralized config
        youtube_config = config.get('scrapers', {}).get('youtube', {})
        
        # Try to get API key from environment first, then config
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            logger.debug("No API key found in environment, checking config...")
            self.api_key = youtube_config.get('api_key')
            if not self.api_key:
                raise ValueError("YouTube API key not found in environment variables or config")
            
        logger.debug(f"Initialized YouTube scraper with config: {json.dumps(youtube_config, indent=2)}")
        
        self.max_results = youtube_config.get('max_results', 10)
        self.min_views = youtube_config.get('min_views', 1000)
        self.time_filter = youtube_config.get('time_filter', 'week')
        self.content_type = youtube_config.get('content_type', 'video')
        self.sort_by = youtube_config.get('sort_by', 'relevance')
        self.language = youtube_config.get('language', 'en')
        self.region_code = youtube_config.get('region_code', 'US')
        self.safe_search = youtube_config.get('safe_search', 'moderate')
        
        # Cache settings from centralized config
        cache_config = config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', True)
        self.cache_duration = cache_config.get('duration', 3600)
        self.cache_location = os.path.join(cache_config.get('location', './cache'), 'youtube')
        
        # Report settings from centralized config
        report_config = config.get('reporting', {})
        self.template_dir = report_config.get('template_dir', 'app/scraper/templates')
        self.report_output_dir = os.path.join(report_config.get('output_dir', './reports'), 'youtube')
        
        # API endpoints
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        self.search_url = f"{self.base_url}/search"
        self.videos_url = f"{self.base_url}/videos"
        self.channels_url = f"{self.base_url}/channels"
        
        # Initialize client
        self.http_client = None

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "youtube"

    async def _init_http_client(self):
        """Initialize aiohttp client with optimized settings."""
        if self.http_client is None:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            self.http_client = aiohttp.ClientSession(timeout=timeout)

    async def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make a request to the YouTube API with proper encoding."""
        try:
            # Ensure the API key is properly encoded
            params['key'] = self.api_key.strip()
            logger.debug(f"Making request to URL: {url}")
            logger.debug(f"Request parameters: {json.dumps({k: v if k != 'key' else '[REDACTED]' for k, v in params.items()}, indent=2)}")
            
            # Build the URL with properly encoded parameters
            query_string = urlencode(params)
            full_url = f"{url}?{query_string}"
            
            async with self.http_client.get(full_url) as response:
                response_text = await response.text()
                logger.debug(f"Response status: {response.status}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                try:
                    response_data = json.loads(response_text)
                    if response.status != 200:
                        logger.debug(f"Error response: {json.dumps(response_data, indent=2)}")
                    return response_data
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response: {response_text}")
                    return None

        except Exception as e:
            logger.error(f"Error making YouTube API request: {str(e)}")
            return None

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            if not self.api_key:
                logger.error("YouTube API key is missing")
                return False
            
            logger.debug(f"Validating YouTube API key (length: {len(self.api_key)})")
            await self._init_http_client()
            
            # Test API access with a simple search
            params = {
                'part': 'snippet',
                'q': 'test',
                'type': 'video',
                'maxResults': 1
            }
            
            response_data = await self._make_request(self.search_url, params)
            if not response_data:
                return False
            
            if 'error' in response_data:
                error_msg = response_data['error'].get('message', 'Unknown error')
                logger.error(f"API Error: {error_msg}")
                return False
                
            if 'items' not in response_data:
                logger.error("YouTube API response missing 'items' field")
                return False

            logger.info("YouTube API validation successful")
            return True
            
        except Exception as e:
            logger.error(f"YouTube scraper validation failed: {str(e)}")
            return False

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

    def _calculate_credibility(self, video_data: Dict[str, Any]) -> float:
        """Calculate credibility score for a YouTube video."""
        base_score = 70.0
        
        # View count score (up to 10 points)
        views = int(video_data.get('statistics', {}).get('viewCount', 0))
        view_score = min(views / 10000, 10)
        
        # Like ratio score (up to 10 points)
        likes = int(video_data.get('statistics', {}).get('likeCount', 0))
        dislikes = int(video_data.get('statistics', {}).get('dislikeCount', 0))
        total_reactions = likes + dislikes
        if total_reactions > 0:
            like_ratio = likes / total_reactions
            like_score = like_ratio * 10
        else:
            like_score = 5  # neutral if no reactions
            
        # Comment engagement score (up to 5 points)
        comments = int(video_data.get('statistics', {}).get('commentCount', 0))
        comment_score = min(comments / 1000, 5)
        
        # Channel credibility (up to 10 points)
        channel_score = 0
        if 'channel' in video_data:
            subs = int(video_data['channel'].get('statistics', {}).get('subscriberCount', 0))
            channel_score += min(subs / 100000, 5)
            
            if video_data['channel'].get('status', {}).get('isVerified', False):
                channel_score += 5
                
        # Content quality indicators (up to 5 points)
        quality_score = 0
        
        # High definition
        if video_data.get('contentDetails', {}).get('definition', '') == 'hd':
            quality_score += 2
            
        # Has description
        if len(video_data.get('snippet', {}).get('description', '')) > 100:
            quality_score += 1
            
        # Has tags
        if len(video_data.get('snippet', {}).get('tags', [])) > 0:
            quality_score += 1
            
        # Caption availability
        if video_data.get('contentDetails', {}).get('caption', '') == 'true':
            quality_score += 1
            
        total_score = base_score + view_score + like_score + comment_score + channel_score + quality_score
        return min(max(total_score, 0), 100)

    @rate_limited(max_per_second=2)
    async def _fetch_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed information for a list of video IDs."""
        if not video_ids:
            return []
            
        try:
            # Get video details
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': ','.join(video_ids)
            }
            
            response_data = await self._make_request(self.videos_url, params)
            if not response_data:
                return []
                
            return response_data.get('items', [])
                
        except Exception as e:
            logger.error(f"Error fetching video details: {str(e)}")
            return []

    @rate_limited(max_per_second=2)
    async def _fetch_channel_details(self, channel_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch channel information for a list of channel IDs."""
        if not channel_ids:
            return []
            
        try:
            params = {
                'part': 'snippet,statistics,status',
                'id': ','.join(channel_ids)
            }
            
            response_data = await self._make_request(self.channels_url, params)
            if not response_data:
                return []
                
            return response_data.get('items', [])
                
        except Exception as e:
            logger.error(f"Error fetching channel details: {str(e)}")
            return []

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape YouTube videos matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing video data
        """
        logger.info(f"Scraping YouTube for: {query}")
        
        try:
            await self._init_http_client()
            
            # Initial search for videos
            params = {
                'part': 'snippet',
                'q': query,
                'type': self.content_type,
                'maxResults': self.max_results,
                'order': self.sort_by,
                'relevanceLanguage': self.language,
                'regionCode': self.region_code,
                'safeSearch': self.safe_search,
                'publishedAfter': self._get_time_filter_date()
            }
            
            response_data = await self._make_request(self.search_url, params)
            if not response_data:
                return []
                
            search_items = response_data.get('items', [])
            if not search_items:
                return []
                
            # Get video IDs and channel IDs
            video_ids = [item['id']['videoId'] for item in search_items]
            channel_ids = [item['snippet']['channelId'] for item in search_items]
            
            # Fetch detailed information
            video_details = await self._fetch_video_details(video_ids)
            channel_details = await self._fetch_channel_details(channel_ids)
            
            # Create channel lookup
            channel_lookup = {
                channel['id']: channel
                for channel in channel_details
            }
            
            # Process and filter results
            results = []
            for video in video_details:
                # Skip videos with too few views
                if int(video.get('statistics', {}).get('viewCount', 0)) < self.min_views:
                    continue
                    
                # Add channel information
                channel_id = video['snippet']['channelId']
                video['channel'] = channel_lookup.get(channel_id, {})
                
                # Calculate credibility
                credibility_score = self._calculate_credibility(video)
                
                # Format duration
                duration = isodate.parse_duration(video['contentDetails']['duration'])
                duration_str = str(duration).split('.')[0]  # Remove microseconds
                
                # Create result entry
                result = {
                    'title': html.unescape(video['snippet']['title']),
                    'description': html.unescape(video['snippet']['description']),
                    'url': f"https://www.youtube.com/watch?v={video['id']}",
                    'thumbnail': video['snippet']['thumbnails']['high']['url'],
                    'channel_name': html.unescape(video['snippet']['channelTitle']),
                    'channel_url': f"https://www.youtube.com/channel/{channel_id}",
                    'published_at': video['snippet']['publishedAt'],
                    'duration': duration_str,
                    'source': 'youtube',
                    'source_detail': f"YouTube - {video['snippet']['channelTitle']}",
                    'credibility_info': {
                        'score': credibility_score,
                        'bias': 'User Generated Content',
                        'category': 'Video Platform'
                    },
                    'metadata': {
                        'views': int(video['statistics'].get('viewCount', 0)),
                        'likes': int(video['statistics'].get('likeCount', 0)),
                        'comments': int(video['statistics'].get('commentCount', 0)),
                        'channel_subscribers': int(video['channel'].get('statistics', {}).get('subscriberCount', 0)),
                        'channel_verified': video['channel'].get('status', {}).get('isVerified', False)
                    }
                }
                results.append(result)
            
            # Sort by credibility score
            sorted_results = sorted(
                results,
                key=lambda x: x['credibility_info']['score'],
                reverse=True
            )
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error during YouTube scraping: {str(e)}")
            return []

    async def close(self):
        """Clean up resources."""
        if self.http_client:
            await self.http_client.close()
