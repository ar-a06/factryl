"""Dev.to scraper for developer articles and discussions."""

from ..base import RSSBasedScraper
from typing import List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)

class DevToScraper(RSSBasedScraper):
    """Scraper for Dev.to articles"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.tags = self.config.get('tags', ['javascript', 'python', 'webdev', 'programming'])
        
        # Build RSS URLs for each tag
        rss_urls = ['https://dev.to/feed']  # Main feed
        rss_urls.extend([f'https://dev.to/feed/tag/{tag}' for tag in self.tags])
        
        super().__init__(rss_urls, config)
    
    def process_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single RSS entry"""
        try:
            # Extract tags if available
            tags = []
            if 'tags' in entry:
                if isinstance(entry['tags'], list):
                    tags = entry['tags']
                elif isinstance(entry['tags'], str):
                    tags = [tag.strip() for tag in entry['tags'].split(',')]
            
            # Calculate credibility based on available metrics
            credibility_score = self._calculate_credibility(entry)
            
            return {
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'author': entry.get('author', ''),
                'content': entry.get('summary', ''),
                'published': entry.get('published', ''),
                'tags': tags,
                'source': 'Dev.to',
                'source_detail': f"Dev.to - {', '.join(tags)}" if tags else "Dev.to",
                'credibility_info': {
                    'score': credibility_score,
                    'category': 'Technical Blog',
                    'bias': 'community-driven'
                },
                'metadata': {
                    'author': entry.get('author', ''),
                    'tags': tags,
                    'published': entry.get('published', '')
                },
                'scraped_at': time.time()
            }
        except Exception as e:
            logger.error(f"Error processing Dev.to entry: {e}")
            return None
    
    def _calculate_credibility(self, entry: Dict[str, Any]) -> float:
        """Calculate credibility score based on available metrics"""
        try:
            # Base score for Dev.to content
            base_score = 85.0
            
            # Adjust based on available metrics
            if 'author' in entry and entry['author']:
                base_score += 2  # Verified author
            
            if 'tags' in entry:
                if isinstance(entry['tags'], (list, str)):
                    # More tags usually indicate better categorized content
                    tag_count = len(entry['tags']) if isinstance(entry['tags'], list) else len(entry['tags'].split(','))
                    base_score += min(tag_count, 3)  # Up to 3 points for tags
            
            return min(base_score, 95.0)  # Cap at 95
        except:
            return 85.0  # Default score for Dev.to content 