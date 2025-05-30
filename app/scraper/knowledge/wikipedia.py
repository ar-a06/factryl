"""Wikipedia scraper for comprehensive background information."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import urllib.parse
import json
from ..base import WebBasedScraper

class WikipediaScraper(WebBasedScraper):
    """Wikipedia scraper for detailed topic information."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Wikipedia scraper."""
        super().__init__(config)
        self.source_name = "Wikipedia"
        self.credibility_base = 90.0  # High credibility for Wikipedia
        self.search_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
        self.search_url = "https://en.wikipedia.org/w/api.php"
        self.max_entries = self.config.get('max_entries', 3)
        
    async def search_pages(self, query: str) -> List[str]:
        """Search for Wikipedia pages matching the query."""
        try:
            await self._rate_limit()
            
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': 5,
                'srprop': 'title|snippet'
            }
            
            url = self.search_url + '?' + urllib.parse.urlencode(params)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    search_results = data.get('query', {}).get('search', [])
                    return [result['title'] for result in search_results]
                    
        except Exception as e:
            logging.error(f"Error searching Wikipedia: {e}")
            
        return []
        
    async def get_page_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """Get summary for a Wikipedia page."""
        try:
            await self._rate_limit()
            
            # URL encode the title
            encoded_title = urllib.parse.quote(title, safe='')
            url = self.search_api_url.format(encoded_title)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract information
                    title = data.get('title', '')
                    extract = data.get('extract', '')
                    page_url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
                    
                    if not extract or len(extract) < 50:
                        return None
                        
                    # Calculate credibility
                    credibility_score = self._calculate_credibility({
                        'title': title,
                        'summary': extract,
                        'source_credibility': self.credibility_base
                    })
                    
                    return {
                        'title': f"About {title}",
                        'link': page_url,
                        'content': extract,
                        'published': datetime.now().strftime('%Y-%m-%d'),
                        'source': self.source_name,
                        'source_type': 'encyclopedia',
                        'source_detail': f"{self.source_name} - Encyclopedia",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Encyclopedia',
                            'bias': 'neutral'
                        },
                        'metadata': {
                            'source': 'wikipedia.org',
                            'source_name': self.source_name,
                            'platform': 'Encyclopedia',
                            'content_type': 'encyclopedia_article',
                            'topic': title
                        },
                        'scraped_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logging.error(f"Error getting Wikipedia page summary for {title}: {e}")
            
        return None
        
    async def scrape(self, query: str = None) -> List[Dict[str, Any]]:
        """Scrape Wikipedia content for the query."""
        if not query:
            return []
            
        await self.setup()
        results = []
        
        try:
            # Search for relevant pages
            page_titles = await self.search_pages(query)
            
            # Get summaries for found pages
            for title in page_titles[:self.max_entries]:
                summary = await self.get_page_summary(title)
                if summary:
                    results.append(summary)
                    
        except Exception as e:
            logging.error(f"Error scraping Wikipedia: {e}")
            
        return results 