"""
Twitter scraper module using Twitter's web interface.
"""

import asyncio
from datetime import datetime, timedelta
import json
import hashlib
import re
from typing import Dict, List, Any, Optional
from loguru import logger
import redis.asyncio as redis
import aiohttp
from bs4 import BeautifulSoup

from ..plugin_loader import BaseScraper, rate_limited

class TwitterScraper(BaseScraper):
    """Twitter scraper implementation using web interface."""

    def __init__(self, config: dict):
        """Initialize the Twitter scraper."""
        super().__init__(config)
        
        # Get cache settings from config
        cache_config = config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', False)
        self.redis_url = f"redis://{cache_config.get('host', 'localhost')}:{cache_config.get('port', 6379)}"
        self.redis = None
        
        # Get Twitter-specific settings
        twitter_config = config.get('twitter', {})
        self.max_tweets = twitter_config.get('max_tweets', 30)
        self.min_likes = twitter_config.get('min_likes', 10)
        self.time_filter = twitter_config.get('time_filter', 'week')
        self.include_replies = twitter_config.get('include_replies', False)
        self.min_credibility = twitter_config.get('min_credibility', 70)
        
        # Initialize HTTP session
        self.session = None

    async def _init_session(self):
        """Initialize aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def _init_cache(self):
        """Initialize Redis cache connection."""
        if self.cache_enabled and self.redis is None:
            try:
                self.redis = await redis.from_url(self.redis_url)
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.cache_enabled = False

    async def _get_cached_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get results from cache if available."""
        if not self.cache_enabled:
            return None
            
        try:
            cache_key = f"twitter:{hashlib.md5(query.encode()).hexdigest()}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Cache for 15 minutes for Twitter content
                if datetime.fromisoformat(data['timestamp']) > datetime.now() - timedelta(minutes=15):
                    return data['results']
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None

    async def _cache_results(self, query: str, results: List[Dict[str, Any]]):
        """Cache results for future use."""
        if not self.cache_enabled:
            return
            
        try:
            cache_key = f"twitter:{hashlib.md5(query.encode()).hexdigest()}"
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            # Cache for 15 minutes
            await self.redis.setex(cache_key, 900, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _extract_tweet_stats(self, tweet_element) -> Dict[str, int]:
        """Extract tweet statistics from the tweet element."""
        stats = {'likes': 0, 'retweets': 0, 'replies': 0}
        try:
            # Find all stat elements
            stat_elements = tweet_element.select('[data-testid$="-count"]')
            for stat in stat_elements:
                value_text = stat.get_text(strip=True)
                value = 0
                
                # Convert K/M numbers
                if 'K' in value_text:
                    value = int(float(value_text.replace('K', '')) * 1000)
                elif 'M' in value_text:
                    value = int(float(value_text.replace('M', '')) * 1000000)
                else:
                    try:
                        value = int(value_text)
                    except ValueError:
                        continue
                
                # Identify stat type by data-testid
                test_id = stat.get('data-testid', '')
                if 'like' in test_id:
                    stats['likes'] = value
                elif 'retweet' in test_id:
                    stats['retweets'] = value
                elif 'reply' in test_id:
                    stats['replies'] = value
        except Exception:
            pass
        return stats

    def _calculate_credibility(self, tweet_element, stats: Dict[str, int]) -> float:
        """Calculate credibility score for a tweet."""
        # Base score
        score = 75.0
        
        # Adjust based on user metrics
        if tweet_element.select_one('[data-testid="verifiedBadge"]'):
            score += 5
        
        # Engagement metrics
        score += min((stats['likes'] / 1000) * 2, 10)  # Up to 10 points for likes
        score += min((stats['retweets'] / 500) * 2, 5)  # Up to 5 points for retweets
        
        # Cap the score
        return min(max(score, 0), 95)

    def _process_tweet(self, tweet_element) -> Optional[Dict[str, Any]]:
        """Process a tweet element into standardized format."""
        try:
            # Get tweet link and ID
            tweet_link = tweet_element.select_one('a[href*="/status/"]')
            if not tweet_link:
                return None
            tweet_url = tweet_link['href']
            tweet_id = tweet_url.split('/status/')[-1]
            
            # Get tweet content
            content_element = tweet_element.select_one('[data-testid="tweetText"]')
            if not content_element:
                return None
            content = content_element.get_text(strip=True)
            
            # Get user info
            username = tweet_element.select_one('[data-testid="User-Name"] span').get_text(strip=True)
            display_name = tweet_element.select_one('[data-testid="User-Name"] a').get_text(strip=True)
            
            # Get timestamp
            time_element = tweet_element.select_one('time')
            tweet_time = datetime.fromisoformat(time_element['datetime'])
            
            # Get stats
            stats = self._extract_tweet_stats(tweet_element)
            
            # Calculate credibility
            credibility_score = self._calculate_credibility(tweet_element, stats)
            
            # Generate unique ID
            content_hash = hashlib.md5(f"{tweet_id}{content}".encode()).hexdigest()
            
            return {
                'id': f"twitter-{content_hash}",
                'title': content[:100] + "..." if len(content) > 100 else content,
                'url': f"https://twitter.com{tweet_url}",
                'content': content,
                'source': 'twitter',
                'source_detail': username,
                'credibility_info': {
                    'score': credibility_score,
                    'bias': 'Social Media',
                    'category': 'Twitter'
                },
                'timestamp': tweet_time.isoformat(),
                'author': display_name,
                'metadata': {
                    'preview': content[:500],
                    'likes': stats['likes'],
                    'retweets': stats['retweets'],
                    'replies': stats['replies'],
                    'verified': bool(tweet_element.select_one('[data-testid="verifiedBadge"]')),
                    'post_type': 'tweet',
                    'scraped_at': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Failed to process tweet: {e}")
            return None

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape tweets matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing tweet data
        """
        logger.info(f"Scraping Twitter for: {query}")
        
        # Initialize session
        await self._init_session()
        
        # Check cache first
        await self._init_cache()
        cached_results = await self._get_cached_results(query)
        if cached_results:
            logger.info("Returning cached Twitter results")
            return cached_results
            
        results = []
        
        try:
            # Build search URL
            search_url = "https://twitter.com/search"
            params = {
                'q': query,
                'src': 'typed_query',
                'f': 'live'
            }
            
            # Add headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Fetch search results
            async with self.session.get(search_url, params=params, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Search request failed with status {response.status}")
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Process tweets
                tweets = soup.select('[data-testid="tweet"]')
                for tweet in tweets[:self.max_tweets]:
                    try:
                        # Skip replies if configured
                        if not self.include_replies and tweet.select_one('[data-testid="reply"]'):
                            continue
                            
                        result = self._process_tweet(tweet)
                        if not result:
                            continue
                            
                        # Check minimum likes
                        if result['metadata']['likes'] < self.min_likes:
                            continue
                            
                        # Check minimum credibility
                        if result['credibility_info']['score'] < self.min_credibility:
                            continue
                            
                        # Check time filter
                        tweet_time = datetime.fromisoformat(result['timestamp'])
                        if self.time_filter == 'day' and tweet_time < datetime.now() - timedelta(days=1):
                            continue
                        elif self.time_filter == 'week' and tweet_time < datetime.now() - timedelta(days=7):
                            continue
                        elif self.time_filter == 'month' and tweet_time < datetime.now() - timedelta(days=30):
                            continue
                            
                        results.append(result)
                        
                        if len(results) >= self.max_tweets:
                            break
                            
                    except Exception as e:
                        logger.error(f"Failed to process tweet: {e}")
                        continue
                        
                    # Rate limiting
                    await asyncio.sleep(0.1)
            
            # Cache results
            if results:
                await self._cache_results(query, results)
            
        except Exception as e:
            logger.error(f"Twitter scraping failed: {e}")
            
        logger.info(f"Scraped {len(results)} items from Twitter")
        return results

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            await self._init_session()
            async with self.session.get("https://twitter.com/search", params={'q': 'test'}) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Twitter scraper validation failed: {e}")
            return False

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "twitter"

    async def close(self):
        """Clean up resources."""
        if self.redis:
            await self.redis.close()
        if self.session:
            await self.session.close()
