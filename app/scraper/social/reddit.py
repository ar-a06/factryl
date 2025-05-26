"""
Reddit scraper module for collecting posts and comments from Reddit using RSS feeds.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from loguru import logger
import hashlib
import json
import redis.asyncio as redis
import aiohttp
import feedparser
import html
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from .plugin_loader import BaseScraper, rate_limited

class RedditScraper(BaseScraper):
    """Reddit scraper implementation using RSS feeds."""

    def __init__(self, config: dict):
        """Initialize the Reddit scraper."""
        super().__init__(config)
        
        # Get cache settings from config
        cache_config = config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', False)
        self.redis_url = f"redis://{cache_config.get('host', 'localhost')}:{cache_config.get('port', 6379)}"
        self.redis = None
        
        # Get Reddit-specific settings
        reddit_config = config.get('reddit', {})
        self.max_posts = reddit_config.get('max_posts', 10)
        self.max_comments = reddit_config.get('max_comments', 5)
        self.min_score = reddit_config.get('min_score', 10)
        self.time_filter = reddit_config.get('time_filter', 'year')
        self.sort_by = reddit_config.get('sort_by', 'relevance')
        
        # Initialize HTTP session
        self.session = None

    async def _init_session(self):
        """Initialize aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def _get_subreddit_feed(self, subreddit: str) -> List[Dict]:
        """Get posts from a subreddit's RSS feed."""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/.rss"
            async with self.session.get(url) as response:
                if response.status == 200:
                    feed_content = await response.text()
                    feed = feedparser.parse(feed_content)
                    return feed.entries
        except Exception as e:
            logger.error(f"Error fetching subreddit feed {subreddit}: {e}")
        return []

    async def _search_subreddits(self, query: str) -> List[str]:
        """Search for relevant subreddits."""
        relevant_subreddits = [
            "artificial", "MachineLearning", "datascience", "technology",
            "science", "Futurology", "tech", "compsci", "programming",
            "Philosophy", "Ethics", "business", "news"
        ]
        return relevant_subreddits

    def _extract_score_from_html(self, content: str) -> int:
        """Extract score from post HTML content."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            score_text = soup.find('span', class_='score').text
            return int(''.join(filter(str.isdigit, score_text)))
        except:
            return 0

    def _process_feed_entry(self, entry: Dict) -> Dict[str, Any]:
        """Process a feed entry into standardized format."""
        # Extract subreddit from link
        subreddit = entry.link.split('/r/')[-1].split('/')[0] if '/r/' in entry.link else "unknown"
        
        # Clean up content
        content = html.unescape(entry.summary) if hasattr(entry, 'summary') else ""
        soup = BeautifulSoup(content, 'html.parser')
        clean_content = soup.get_text()
        
        # Generate unique ID
        content_hash = hashlib.md5(f"{entry.link}{clean_content}".encode()).hexdigest()
        
        return {
            'id': f"reddit-post-{content_hash}",
            'title': html.unescape(entry.title),
            'url': entry.link,
            'content': clean_content,
            'source': 'reddit',
            'source_detail': f"r/{subreddit}",
            'credibility_info': {
                'score': 85,  # Default score since we can't get upvote ratio
                'bias': 'Community Rated',
                'category': 'Social Media'
            },
            'timestamp': datetime(*entry.published_parsed[:6]).isoformat(),
            'author': entry.author if hasattr(entry, 'author') else "[unknown]",
            'metadata': {
                'preview': clean_content[:500],
                'post_type': 'reddit_post',
                'subreddit': subreddit,
                'scraped_at': datetime.utcnow().isoformat()
            }
        }

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape Reddit posts matching the query using RSS feeds.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing post data
        """
        logger.info(f"Scraping Reddit for: {query}")
        
        # Initialize HTTP session
        await self._init_session()
        
        # Check cache first
        await self._init_cache()
        cached_results = await self._get_cached_results(query)
        if cached_results:
            logger.info("Returning cached Reddit results")
            return cached_results
            
        results = []
        
        try:
            # Get relevant subreddits
            subreddits = await self._search_subreddits(query)
            
            # Fetch feeds from each subreddit
            for subreddit in subreddits:
                entries = await self._get_subreddit_feed(subreddit)
                
                # Process entries that match the query
                query_terms = query.lower().split()
                for entry in entries:
                    title = entry.title.lower()
                    if any(term in title for term in query_terms):
                        results.append(self._process_feed_entry(entry))
                        
                        if len(results) >= self.max_posts:
                            break
                            
                await asyncio.sleep(1)  # Rate limiting
                
            # Sort by relevance (basic implementation)
            results.sort(
                key=lambda x: sum(term in x['title'].lower() for term in query_terms),
                reverse=True
            )
            
            # Cache results
            if results:
                await self._cache_results(query, results)
            
        except Exception as e:
            logger.error(f"Reddit scraping failed: {e}")
            
        logger.info(f"Scraped {len(results)} items from Reddit")
        return results

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            await self._init_session()
            async with self.session.get("https://www.reddit.com/.rss") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Reddit scraper validation failed: {e}")
            return False

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "reddit"

    async def close(self):
        """Clean up resources."""
        if self.redis:
            await self.redis.close()
        if self.session:
            await self.session.close()

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
            cache_key = f"reddit:{hashlib.md5(query.encode()).hexdigest()}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Cache for 30 minutes for Reddit content
                if datetime.fromisoformat(data['timestamp']) > datetime.now() - timedelta(minutes=30):
                    return data['results']
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None

    async def _cache_results(self, query: str, results: List[Dict[str, Any]]):
        """Cache results for future use."""
        if not self.cache_enabled:
            return
            
        try:
            cache_key = f"reddit:{hashlib.md5(query.encode()).hexdigest()}"
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            # Cache for 30 minutes
            await self.redis.setex(cache_key, 1800, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
