"""Google News scraper for real-time news data with search capability."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import urllib.parse
from ..base import RSSBasedScraper

class GoogleNewsScraper(RSSBasedScraper):
    """Google News scraper that can search for specific topics."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Google News scraper."""
        # Base URLs - we'll dynamically generate search URLs
        rss_urls = []
        super().__init__(rss_urls, config)
        self.source_name = "Google News"
        self.credibility_base = 85.0  # Aggregated news
        self.base_search_url = "https://news.google.com/rss/search?q={}&hl=en&gl=US&ceid=US:en"
        
    def get_search_urls(self, query: str) -> List[str]:
        """Generate Google News search URLs for the query."""
        if not query:
            # Default topics if no query
            default_queries = [
                "technology",
                "business",
                "science", 
                "entertainment",
                "world news"
            ]
            return [self.base_search_url.format(urllib.parse.quote(q)) for q in default_queries]
        
        # Search specific query
        encoded_query = urllib.parse.quote(query)
        return [self.base_search_url.format(encoded_query)]
        
    def process_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Process Google News RSS entry into standardized format."""
        try:
            # Extract content
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            summary = getattr(entry, 'summary', '')
            published = getattr(entry, 'published', '')
            source = getattr(entry, 'source', {}).get('title', 'Unknown Source')
            
            # Skip if no title
            if not title:
                return None
                
            # Clean up title (Google News sometimes includes source)
            if ' - ' in title:
                title_parts = title.split(' - ')
                if len(title_parts) > 1:
                    title = ' - '.join(title_parts[:-1])  # Remove last part (usually source)
                    if not source or source == 'Unknown Source':
                        source = title_parts[-1]
                        
            # Calculate credibility based on source
            credibility_score = self._calculate_credibility({
                'title': title,
                'summary': summary,
                'source': source,
                'source_credibility': self.credibility_base
            })
            
            return {
                'title': title,
                'link': link,
                'content': summary,
                'published': published,
                'source': source,
                'source_type': 'news',
                'source_detail': f"{source} via Google News",
                'credibility_info': {
                    'score': credibility_score,
                    'category': 'Aggregated News',
                    'bias': 'mixed'
                },
                'metadata': {
                    'source': 'news.google.com',
                    'source_name': source,
                    'platform': 'Google News',
                    'published_date': published,
                    'content_type': 'news_article',
                    'aggregator': 'Google News'
                },
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error processing Google News entry: {e}")
            return None
            
    async def scrape(self, query: str = None, max_results: int = None) -> List[Dict[str, Any]]:
        """Scrape Google News with specific query search."""
        await self.setup()
        
        # Update RSS URLs based on query
        self.rss_urls = self.get_search_urls(query)
        
        results = []
        for rss_url in self.rss_urls:
            try:
                await self._rate_limit()
                
                # Parse RSS feed
                import feedparser
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[: (max_results or self.max_entries)]:
                    processed_entry = self.process_entry(entry)
                    if processed_entry:
                        results.append(processed_entry)
                        
            except Exception as e:
                logging.error(f"Error parsing Google News RSS feed {rss_url}: {e}")
        
        # Sort by publication date (newest first)
        try:
            results.sort(key=lambda x: x.get('published', ''), reverse=True)
        except:
            pass
            
        return results[: (max_results or self.max_entries)]

    search = scrape 