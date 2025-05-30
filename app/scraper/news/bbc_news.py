"""BBC News scraper for real-time news data."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
from ..base import RSSBasedScraper

class BBCNewsScraper(RSSBasedScraper):
    """Real BBC News scraper using RSS feeds."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize BBC News scraper."""
        rss_urls = [
            "http://feeds.bbci.co.uk/news/rss.xml",  # Main news
            "http://feeds.bbci.co.uk/news/technology/rss.xml",  # Tech news
            "http://feeds.bbci.co.uk/news/business/rss.xml",  # Business
            "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"  # Science
        ]
        super().__init__(rss_urls, config)
        self.source_name = "BBC News"
        self.credibility_base = 92.0  # High credibility for BBC
        
    def process_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Process BBC RSS entry into standardized format."""
        try:
            # Extract content
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            summary = getattr(entry, 'summary', '')
            published = getattr(entry, 'published', '')
            
            # Skip if no title
            if not title:
                return None
                
            # Calculate credibility
            credibility_score = self._calculate_credibility({
                'title': title,
                'summary': summary,
                'source_credibility': self.credibility_base
            })
            
            return {
                'title': title,
                'link': link,
                'content': summary,
                'published': published,
                'source': self.source_name,
                'source_type': 'news',
                'source_detail': f"{self.source_name} - News",
                'credibility_info': {
                    'score': credibility_score,
                    'category': 'Mainstream Media',
                    'bias': 'center-left'
                },
                'metadata': {
                    'source': 'bbc.com',
                    'source_name': self.source_name,
                    'platform': 'News',
                    'published_date': published,
                    'content_type': 'news_article'
                },
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error processing BBC entry: {e}")
            return None
            
    async def scrape(self, query: str = None, max_results: int = None) -> List[Dict[str, Any]]:
        """Scrape BBC News with optional query filtering."""
        await self.setup()
        results = await super().scrape(query)
        
        # Sort by publication date (newest first)
        try:
            results.sort(key=lambda x: x.get('published', ''), reverse=True)
        except:
            pass
            
        return results[: (max_results or self.max_entries)]

    search = scrape 