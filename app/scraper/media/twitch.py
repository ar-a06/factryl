"""Twitch and streaming platform scraper for live streams and VODs."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TwitchScraper(WebBasedScraper):
    """Scraper for Twitch streams and VODs"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Twitch API configuration
        twitch_config = self.config.get('twitch', {})
        self.client_id = twitch_config.get('client_id', '')
        self.client_secret = twitch_config.get('client_secret', '')
        self.access_token = None
        
        # Scraping settings
        self.max_streams = self.config.get('max_streams', 50)
        self.min_viewers = self.config.get('min_viewers', 100)
        self.include_vods = self.config.get('include_vods', True)
        self.categories = self.config.get('categories', [
            'Science & Technology',
            'Just Chatting',
            'Programming',
            'Software and Game Development'
        ])

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "twitch"

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            # Check if we have Twitch API credentials
            if not self.client_id or not self.client_secret:
                logger.warning("Twitch API credentials not configured, using web scraping fallback")
                return True  # Still valid, just limited functionality
            
            # Test API access
            await self._get_access_token()
            return self.access_token is not None
            
        except Exception as e:
            logger.error(f"Twitch scraper validation failed: {str(e)}")
            return False

    async def _get_access_token(self):
        """Get OAuth access token for Twitch API."""
        if not self.client_id or not self.client_secret:
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://id.twitch.tv/oauth2/token"
                data = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'client_credentials'
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.access_token = result.get('access_token')
                        return self.access_token
                    else:
                        logger.error(f"Failed to get Twitch access token: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting Twitch access token: {e}")
            return None

    async def _search_streams_api(self, query: str) -> List[Dict[str, Any]]:
        """Search streams using Twitch API."""
        if not self.access_token:
            return []
            
        try:
            headers = {
                'Client-ID': self.client_id,
                'Authorization': f'Bearer {self.access_token}'
            }
            
            streams = []
            
            # Search for live streams
            async with aiohttp.ClientSession() as session:
                # Get streams by game/category
                for category in self.categories:
                    # First get game ID
                    game_url = f"https://api.twitch.tv/helix/games?name={category}"
                    async with session.get(game_url, headers=headers) as response:
                        if response.status == 200:
                            games_data = await response.json()
                            if games_data.get('data'):
                                game_id = games_data['data'][0]['id']
                                
                                # Get streams for this game
                                streams_url = f"https://api.twitch.tv/helix/streams?game_id={game_id}&first=20"
                                async with session.get(streams_url, headers=headers) as stream_response:
                                    if stream_response.status == 200:
                                        streams_data = await stream_response.json()
                                        
                                        for stream in streams_data.get('data', []):
                                            # Filter by query and viewer count
                                            if (stream['viewer_count'] >= self.min_viewers and
                                                query.lower() in stream['title'].lower()):
                                                
                                                # Get user info
                                                user_url = f"https://api.twitch.tv/helix/users?id={stream['user_id']}"
                                                async with session.get(user_url, headers=headers) as user_response:
                                                    user_data = {}
                                                    if user_response.status == 200:
                                                        user_result = await user_response.json()
                                                        if user_result.get('data'):
                                                            user_data = user_result['data'][0]
                                                
                                                # Calculate credibility based on followers, views, etc.
                                                credibility_score = self._calculate_stream_credibility(stream, user_data)
                                                
                                                stream_info = {
                                                    'title': stream['title'],
                                                    'link': f"https://twitch.tv/{stream['user_login']}",
                                                    'streamer': stream['user_name'],
                                                    'game_name': stream['game_name'],
                                                    'viewer_count': stream['viewer_count'],
                                                    'language': stream['language'],
                                                    'started_at': stream['started_at'],
                                                    'thumbnail_url': stream['thumbnail_url'],
                                                    'is_live': True,
                                                    'source': 'twitch',
                                                    'source_name': 'Twitch',
                                                    'type': 'Live Stream',
                                                    'source_detail': f"Twitch - {stream['user_name']}",
                                                    'credibility_info': {
                                                        'score': credibility_score,
                                                        'category': 'Live Content',
                                                        'bias': 'real-time'
                                                    },
                                                    'metadata': {
                                                        'platform': 'Twitch',
                                                        'streamer': stream['user_name'],
                                                        'game': stream['game_name'],
                                                        'viewers': stream['viewer_count'],
                                                        'language': stream['language'],
                                                        'started_at': stream['started_at'],
                                                        'stream_type': 'live'
                                                    },
                                                    'scraped_at': time.time()
                                                }
                                                streams.append(stream_info)
            
            return streams
            
        except Exception as e:
            logger.error(f"Error searching Twitch streams via API: {e}")
            return []

    def _calculate_stream_credibility(self, stream: Dict, user_data: Dict) -> float:
        """Calculate credibility score for a stream."""
        try:
            base_score = 50.0
            
            # Viewer count factor (more viewers = higher credibility)
            viewer_count = stream.get('viewer_count', 0)
            if viewer_count > 10000:
                base_score += 20
            elif viewer_count > 1000:
                base_score += 15
            elif viewer_count > 500:
                base_score += 10
            elif viewer_count > 100:
                base_score += 5
            
            # User factors
            if user_data:
                # Follower count
                follower_count = user_data.get('follower_count', 0)
                if follower_count > 100000:
                    base_score += 15
                elif follower_count > 10000:
                    base_score += 10
                elif follower_count > 1000:
                    base_score += 5
                
                # Account age (older accounts tend to be more credible)
                created_at = user_data.get('created_at', '')
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        account_age_years = (datetime.now().replace(tzinfo=created_date.tzinfo) - created_date).days / 365
                        if account_age_years > 5:
                            base_score += 10
                        elif account_age_years > 2:
                            base_score += 5
                    except:
                        pass
            
            # Category credibility
            category = stream.get('game_name', '').lower()
            if any(tech_term in category for tech_term in ['programming', 'software', 'science', 'technology']):
                base_score += 10
            
            return min(100.0, max(0.0, base_score))
            
        except Exception:
            return 50.0

    async def _search_streams_web(self, query: str) -> List[Dict[str, Any]]:
        """Fallback web scraping for Twitch (limited functionality)."""
        try:
            # This is a simplified fallback - in practice, Twitch's anti-bot measures
            # make web scraping challenging. API is strongly recommended.
            streams = []
            
            # For demo purposes, return some mock data indicating API is needed
            streams.append({
                'title': f'API credentials needed for live Twitch search: {query}',
                'link': 'https://dev.twitch.tv/docs/api/',
                'streamer': 'System Notice',
                'game_name': 'Configuration Required',
                'viewer_count': 0,
                'is_live': False,
                'source': 'twitch',
                'source_name': 'Twitch',
                'type': 'Configuration Notice',
                'source_detail': 'Twitch - Setup Required',
                'credibility_info': {
                    'score': 100.0,
                    'category': 'System Notice',
                    'bias': 'informational'
                },
                'metadata': {
                    'platform': 'Twitch',
                    'note': 'Configure Twitch API credentials for full functionality',
                    'stream_type': 'notice'
                },
                'scraped_at': time.time()
            })
            
            return streams
            
        except Exception as e:
            logger.error(f"Error in Twitch web scraping fallback: {e}")
            return []

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """Scrape Twitch streams matching the query."""
        logger.info(f"Scraping Twitch for: {query}")
        
        # Try API first, fall back to web scraping
        if self.access_token or await self._get_access_token():
            streams = await self._search_streams_api(query)
        else:
            streams = await self._search_streams_web(query)
        
        # Sort by viewer count and credibility
        sorted_streams = sorted(
            streams,
            key=lambda x: (x.get('viewer_count', 0), x['credibility_info']['score']),
            reverse=True
        )
        
        return sorted_streams[:self.max_streams] 