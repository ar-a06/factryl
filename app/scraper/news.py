"""
News scraper module for collecting articles from various news sources.
"""

import urllib.parse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from newspaper import Article, Config
from bs4 import BeautifulSoup
import aiohttp
from loguru import logger
import hashlib
import json
import redis.asyncio as redis

from .plugin_loader import BaseScraper

class NewsScraper(BaseScraper):
    """News scraper implementation."""

    def __init__(self, config: dict):
        """Initialize the news scraper."""
        super().__init__(config)
        
        # Get cache settings from config
        cache_config = config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', False)
        self.redis_url = f"redis://{cache_config.get('host', 'localhost')}:{cache_config.get('port', 6379)}"
        self.redis = None
        self.session = None
        
        # News sources with search patterns and credibility info
        self.news_sources = {
            "reuters": {
                "base_url": "https://www.reuters.com",
                "search_pattern": "https://www.reuters.com/search/news?blob={query}",
                "credibility_score": 95,  # High factual reporting
                "bias_rating": "Least biased",
                "category": "International News Agency"
            },
            "ap": {
                "base_url": "https://apnews.com",
                "search_pattern": "https://apnews.com/search?q={query}",
                "credibility_score": 95,
                "bias_rating": "Least biased",
                "category": "International News Agency"
            },
            "bbc": {
                "base_url": "https://www.bbc.com/news",
                "search_pattern": "https://www.bbc.co.uk/search?q={query}",
                "credibility_score": 93,
                "bias_rating": "Least biased",
                "category": "Public Broadcaster"
            },
            "economist": {
                "base_url": "https://www.economist.com",
                "search_pattern": "https://www.economist.com/search?q={query}",
                "credibility_score": 92,
                "bias_rating": "Lean Center",
                "category": "Economic News"
            },
            "nature": {
                "base_url": "https://www.nature.com",
                "search_pattern": "https://www.nature.com/search?q={query}",
                "credibility_score": 95,
                "bias_rating": "Least biased",
                "category": "Scientific Journal"
            },
            "sciencedaily": {
                "base_url": "https://www.sciencedaily.com",
                "search_pattern": "https://www.sciencedaily.com/search?q={query}",
                "credibility_score": 85,
                "bias_rating": "Scientific",
                "category": "Science News"
            },
            "ft": {
                "base_url": "https://www.ft.com",
                "search_pattern": "https://www.ft.com/search?q={query}",
                "credibility_score": 90,
                "bias_rating": "Center",
                "category": "Financial News"
            },
            "guardian": {
                "base_url": "https://www.theguardian.com",
                "search_pattern": "https://www.theguardian.com/search?q={query}",
                "credibility_score": 88,
                "bias_rating": "Lean Left",
                "category": "Newspaper"
            }
        }
        
        # Configure newspaper
        self.config = Config()
        self.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.config.request_timeout = 10
        self.last_request_time = 0.0
        self.min_request_interval = 0.1  # 10 requests per second max
        
        # Get scraping limits from config
        scraping_config = config.get('scraping', {})
        self.max_total_articles = scraping_config.get('max_total_articles', 15)
        self.min_credibility_score = scraping_config.get('min_credibility_score', 85)

    async def _init_cache(self):
        """Initialize Redis cache connection."""
        if self.cache_enabled and self.redis is None:
            try:
                self.redis = await redis.from_url(self.redis_url)
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.cache_enabled = False

    async def _get_cached_articles(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get articles from cache if available."""
        if not self.cache_enabled:
            return None
            
        try:
            cache_key = f"news:{hashlib.md5(query.encode()).hexdigest()}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                if datetime.fromisoformat(data['timestamp']) > datetime.now() - timedelta(hours=1):
                    return data['articles']
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None

    async def _cache_articles(self, query: str, articles: List[Dict[str, Any]]):
        """Cache articles for future use."""
        if not self.cache_enabled:
            return
            
        try:
            cache_key = f"news:{hashlib.md5(query.encode()).hexdigest()}"
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'articles': articles
            }
            await self.redis.setex(cache_key, 3600, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
        return None

    async def _parse_article(self, url: str, source_info: dict) -> Optional[Dict[str, Any]]:
        """Parse a single article URL."""
        try:
            article = Article(url, config=self.config)
            await asyncio.to_thread(article.download)
            await asyncio.to_thread(article.parse)
            
            if not article.title or not article.text:
                return None
                
            return {
                'id': f"news-{hashlib.md5((article.title + article.text).encode()).hexdigest()}",
                'title': article.title,
                'url': url,
                'content': article.text,
                'source': 'news',
                'source_detail': source_info['base_url'],
                'credibility_info': {
                    'score': source_info['credibility_score'],
                    'bias': source_info['bias_rating'],
                    'category': source_info['category']
                },
                'timestamp': article.publish_date.isoformat() if article.publish_date else None,
                'author': ', '.join(article.authors) if article.authors else 'Unknown',
                'metadata': {
                    'preview': article.text[:500],
                    'language': article.meta_lang,
                    'scraped_at': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.warning(f"Failed to parse article {url}: {e}")
            return None

    async def _search_source(self, source_name: str, source_info: dict, query: str) -> List[Dict[str, Any]]:
        """Search a specific news source for articles."""
        # Skip sources below minimum credibility score
        if source_info['credibility_score'] < self.min_credibility_score:
            logger.warning(f"Skipping {source_name} due to low credibility score")
            return []

        articles = []
        search_url = source_info['search_pattern'].format(query=urllib.parse.quote(query))
        
        content = await self._fetch_url(search_url)
        if not content:
            return articles
            
        soup = BeautifulSoup(content, 'html.parser')
        article_urls = set()
        
        # Find article links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith('http'):
                href = urllib.parse.urljoin(source_info['base_url'], href)
            
            # Check if URL contains query terms and is not already processed
            if (href not in article_urls and 
                any(term.lower() in href.lower() for term in query.split())):
                article_urls.add(href)
        
        # Parse articles concurrently
        tasks = [self._parse_article(url, source_info) 
                for url in article_urls]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        articles.extend([article for article in results if article])
        return articles

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape news articles based on the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of article dictionaries
        """
        logger.info(f"Starting news scrape for query: {query}")
        
        await self._init_cache()
        
        # Check cache first
        cached_articles = await self._get_cached_articles(query)
        if cached_articles:
            logger.info("Returning cached articles")
            return cached_articles[:self.max_total_articles]
            
        # Scrape from all sources concurrently
        tasks = [
            self._search_source(name, info, query)
            for name, info in self.news_sources.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and sort results by credibility score
        all_articles = []
        for articles in results:
            if isinstance(articles, list):
                all_articles.extend(articles)
                
        # Sort by credibility score and timestamp
        all_articles.sort(
            key=lambda x: (
                x['credibility_info']['score'],
                x['timestamp'] if x['timestamp'] else '0'
            ),
            reverse=True
        )
        
        # Limit to max total articles
        all_articles = all_articles[:self.max_total_articles]
        
        # Cache results
        await self._cache_articles(query, all_articles)
        
        logger.info(f"News scraping complete: {len(all_articles)} articles collected")
        return all_articles

    async def validate(self) -> bool:
        """Validate the scraper configuration and dependencies."""
        try:
            # Test connection to one news source
            test_url = "https://www.reuters.com"
            if not self.session:
                self.session = aiohttp.ClientSession()
            async with self.session.get(test_url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return 'news'

    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
        if self.redis:
            await self.redis.close()
