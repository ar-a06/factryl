"""Safari search scraper using DuckDuckGo backend."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import urllib.parse
import re
from bs4 import BeautifulSoup
from ..base import WebBasedScraper

class SafariScraper(WebBasedScraper):
    """Safari search scraper (uses DuckDuckGo backend)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Safari scraper."""
        super().__init__(config)
        self.source_name = "Safari Search"
        self.credibility_base = 85.0  # Safari with privacy focus
        self.search_url = "https://duckduckgo.com/html/"
        self.max_entries = self.config.get('max_entries', 15)
        
    async def search(self, query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """Search method expected by the engine."""
        if not query:
            return []
        
        # Update max_entries based on max_results parameter
        original_max = self.max_entries
        self.max_entries = max_results
        
        try:
            # Ensure we have a fresh session
            await self.setup()
            results = await self.search_web(query)
            return results[:max_results]  # Ensure we don't exceed the limit
        except Exception as e:
            logging.error(f"Error in Safari search: {e}")
            return []
        finally:
            # Restore original max_entries
            self.max_entries = original_max
        
    async def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search using Safari's default search engine."""
        try:
            await self.setup()
            
            # Prepare search parameters with Safari-like preferences
            params = {
                'q': query,
                'kl': 'us-en',
                's': '0',
                'df': '',
                'safe': 'moderate',  # Safari's default safety
                'ia': 'web'
            }
            
            search_url = f"{self.search_url}?{urllib.parse.urlencode(params)}"
            
            await self._rate_limit()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
            
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    result_divs = soup.find_all('div', class_='result')
                    
                    for div in result_divs[:self.max_entries]:
                        try:
                            title_link = div.find('a', class_='result__a')
                            if not title_link:
                                continue
                                
                            title = title_link.get_text(strip=True)
                            link = title_link.get('href', '')
                            
                            snippet_elem = div.find('a', class_='result__snippet')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                            
                            url_elem = div.find('span', class_='result__url')
                            source_domain = url_elem.get_text(strip=True) if url_elem else ""
                            
                            if title and link:
                                credibility_score = self._calculate_search_credibility(link, title, snippet)
                                
                                result = {
                                    'title': title,
                                    'link': link,
                                    'content': snippet,
                                    'published': datetime.now().strftime('%Y-%m-%d'),
                                    'source': source_domain or self._extract_domain(link),
                                    'source_type': 'web_search',
                                    'source_detail': f"Search Result via {self.source_name}",
                                    'credibility_info': {
                                        'score': credibility_score,
                                        'category': 'Web Search (Privacy-Focused)',
                                        'bias': 'mixed'
                                    },
                                    'metadata': {
                                        'source': 'safari.com',
                                        'source_name': source_domain or 'Safari Result',
                                        'platform': 'Safari Browser',
                                        'content_type': 'web_result',
                                        'search_query': query,
                                        'search_position': len(results) + 1,
                                        'privacy_focused': True
                                    },
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                results.append(result)
                                
                        except Exception as e:
                            logging.error(f"Error processing Safari result: {e}")
                            continue
                    
                    return results
                    
        except Exception as e:
            logging.error(f"Error searching Safari: {e}")
            
        return []
        
    def _calculate_search_credibility(self, url: str, title: str, snippet: str) -> float:
        """Calculate credibility score with Safari's privacy standards."""
        base_score = self.credibility_base
        
        domain = self._extract_domain(url).lower()
        
        # High credibility domains (Safari prioritizes these)
        high_cred_domains = ['wikipedia.org', 'britannica.com', 'gov', 'edu', 'nature.com', 'science.org', 'bbc.com', 'reuters.com', 'cnn.com', 'nytimes.com', 'apple.com']
        if any(hcd in domain for hcd in high_cred_domains):
            base_score += 10
            
        # Privacy-respecting domains get bonus
        privacy_domains = ['duckduckgo.com', 'startpage.com', 'searx.org']
        if any(pd in domain for pd in privacy_domains):
            base_score += 5
            
        # Content quality indicators
        if len(title) > 20:
            base_score += 3
        if len(snippet) > 100:
            base_score += 4
            
        return min(base_score, 100.0)
        
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
            
    async def scrape(self, query: str = None) -> List[Dict[str, Any]]:
        """Main scraping method for Safari search."""
        if not query:
            return []
            
        return await self.search_web(query) 