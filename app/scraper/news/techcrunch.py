"""TechCrunch scraper for real-time tech news."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
from ..base import RSSBasedScraper

class TechCrunchScraper(RSSBasedScraper):
    """Real TechCrunch scraper using RSS feeds."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize TechCrunch scraper."""
        rss_urls = [
            "https://techcrunch.com/feed/",  # Main feed
            "https://techcrunch.com/category/startups/feed/",  # Startups
            "https://techcrunch.com/category/artificial-intelligence/feed/",  # AI
            "https://techcrunch.com/category/apps/feed/"  # Apps
        ]
        super().__init__(rss_urls, config)
        self.source_name = "TechCrunch"
        self.credibility_base = 88.0  # High credibility for tech news
        
    def process_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Process TechCrunch RSS entry into standardized format."""
        try:
            # Extract content
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            summary = getattr(entry, 'summary', '')
            published = getattr(entry, 'published', '')
            author = getattr(entry, 'author', '')
            
            # Skip if no title
            if not title:
                return None
                
            # Clean up summary (remove HTML tags)
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary.replace('&#8230;', '...').replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
            
            # Calculate credibility
            credibility_score = self._calculate_credibility({
                'title': title,
                'summary': summary,
                'author': author,
                'source_credibility': self.credibility_base
            })
            
            return {
                'title': title,
                'link': link,
                'content': summary,
                'published': published,
                'author': author,
                'source': self.source_name,
                'source_type': 'tech_news',
                'source_detail': f"{self.source_name} - Tech News",
                'credibility_info': {
                    'score': credibility_score,
                    'category': 'Technology Media',
                    'bias': 'tech-focused'
                },
                'metadata': {
                    'source': 'techcrunch.com',
                    'source_name': self.source_name,
                    'platform': 'Tech News',
                    'published_date': published,
                    'author': author,
                    'content_type': 'tech_article'
                },
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error processing TechCrunch entry: {e}")
            return None
            
    async def scrape(self, query: str = None, max_results: int = None) -> List[Dict[str, Any]]:
        """Scrape TechCrunch with optional query filtering."""
        await self.setup()
        results = await super().scrape(query)
        
        # Sort by publication date (newest first)
        try:
            results.sort(key=lambda x: x.get('published', ''), reverse=True)
        except:
            pass
            
        return results[:max_results or self.max_entries]

    search = scrape 