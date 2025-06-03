"""Base scraper class for web-based scrapers."""

from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
import time
import feedparser
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class WebBasedScraper(ABC):
    """Base class for all web-based scrapers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the scraper with configuration."""
        self.config = config or {}
        self.session = None
        self.rate_limit = self.config.get('rate_limit', 1.0)  # Default 1 second between requests
        self.last_request_time = 0
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def setup(self):
        """Set up the scraper session."""
        try:
            # Check if session exists and is not closed
            if not self.session or self.session.closed:
                if self.session and self.session.closed:
                    self.session = None
                self.session = aiohttp.ClientSession()
        except Exception as e:
            logger.error(f"Error setting up session: {e}")
            # Force create a new session
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """Close the scraper session."""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def _rate_limit(self):
        """Implement rate limiting between requests."""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
        
    async def get_soup(self, url: str) -> BeautifulSoup:
        """Get BeautifulSoup object from URL."""
        await self._rate_limit()
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return BeautifulSoup("", 'html.parser')
            
    def _extract_text(self, container: BeautifulSoup, selector: str) -> str:
        """Extract text from element using selector."""
        try:
            element = container.select_one(selector)
            return element.get_text(strip=True) if element else ""
        except Exception as e:
            logger.error(f"Error extracting text with selector {selector}: {e}")
            return ""
            
    def _calculate_credibility(self, article: Dict[str, Any]) -> float:
        """Calculate credibility score for an article."""
        try:
            # Base score from source
            base_score = article.get('source_credibility', 85.0)
            
            # Adjust based on content quality
            title = article.get('title', '')
            summary = article.get('summary', '')
            author = article.get('author', '')
            
            # Title quality
            if len(title) > 10:
                base_score += 2
                
            # Summary quality
            if len(summary) > 100:
                base_score += 3
                
            # Author presence
            if author:
                base_score += 2
                
            # Cap at 100
            return min(base_score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating credibility: {e}")
            return 85.0  # Default score
            
    @abstractmethod
    async def scrape(self, query: str = None) -> List[Dict[str, Any]]:
        """Scrape content. Must be implemented by subclasses."""
        pass
        
    async def validate(self) -> bool:
        """Validate scraper configuration."""
        try:
            # Basic validation
            if not self.config:
                return False
                
            # Test connection
            await self.setup()
            if not self.session:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


class RSSBasedScraper(WebBasedScraper):
    """Base class for RSS-based scrapers."""
    
    def __init__(self, rss_urls: List[str], config: Optional[Dict[str, Any]] = None):
        """Initialize RSS scraper with feed URLs."""
        super().__init__(config)
        self.rss_urls = rss_urls if isinstance(rss_urls, list) else [rss_urls]
        self.max_entries = self.config.get('max_entries', 20)
        
    async def scrape(self, query: str = None) -> List[Dict[str, Any]]:
        """Scrape content from RSS feeds."""
        results = []
        
        for rss_url in self.rss_urls:
            try:
                await self._rate_limit()
                
                # Parse RSS feed
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:self.max_entries]:
                    processed_entry = self.process_entry(entry)
                    if processed_entry:
                        # Filter by query if provided
                        if not query or self._matches_query(processed_entry, query, len(results)):
                            results.append(processed_entry)
                            
            except Exception as e:
                logger.error(f"Error parsing RSS feed {rss_url}: {e}")
                
        return results
        
    def process_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Process a single RSS entry. Should be overridden by subclasses."""
        try:
            return {
                'title': getattr(entry, 'title', ''),
                'link': getattr(entry, 'link', ''),
                'summary': getattr(entry, 'summary', ''),
                'published': getattr(entry, 'published', ''),
                'author': getattr(entry, 'author', ''),
                'source': self.__class__.__name__.replace('Scraper', ''),
                'scraped_at': time.time()
            }
        except Exception as e:
            logger.error(f"Error processing RSS entry: {e}")
            return None
            
    def _matches_query(self, entry: Dict[str, Any], query: str, current_results_count: int = 0) -> bool:
        """Check if entry matches the query with relaxed matching."""
        if not query:
            return True
            
        query_lower = query.lower()
        searchable_text = f"{entry.get('title', '')} {entry.get('content', '')} {entry.get('summary', '')}".lower()
        
        # Relaxed matching - check for any word in the query
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 2 and word in searchable_text:
                return True
                
        # If no individual words match, still include some content for diversity
        # This ensures we get recent news even if not directly related
        return current_results_count < 3  # Include first few articles regardless
