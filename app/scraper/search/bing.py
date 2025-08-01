"""Bing search scraper for comprehensive web search results."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import urllib.parse
import re
from bs4 import BeautifulSoup
from ..base import WebBasedScraper

class BingScraper(WebBasedScraper):
    """Bing search scraper for any topic."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Bing scraper."""
        super().__init__(config)
        self.source_name = "Bing Search"
        self.credibility_base = 84.0  # Microsoft's search engine
        self.search_url = "https://www.bing.com/search"
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
            logging.error(f"Error in Bing search: {e}")
            return []
        finally:
            # Restore original max_entries
            self.max_entries = original_max
        
    async def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search Bing for the query and extract results."""
        try:
            await self.setup()
            
            # Prepare search parameters
            params = {
                'q': query,
                'count': str(self.max_entries),
                'first': '1',
                'FORM': 'PERE'
            }
            
            search_url = f"{self.search_url}?{urllib.parse.urlencode(params)}"
            
            await self._rate_limit()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    
                    # Extract search results - Bing uses different selectors
                    result_items = soup.find_all('li', class_='b_algo')
                    
                    for item in result_items[:self.max_entries]:
                        try:
                            # Extract title and link
                            title_elem = item.find('h2')
                            if not title_elem:
                                continue
                                
                            title_link = title_elem.find('a')
                            if not title_link:
                                continue
                                
                            title = title_link.get_text(strip=True)
                            link = title_link.get('href', '')
                            
                            # Extract snippet
                            snippet_elem = item.find('div', class_='b_caption')
                            snippet = ""
                            if snippet_elem:
                                snippet_p = snippet_elem.find('p')
                                if snippet_p:
                                    snippet = snippet_p.get_text(strip=True)
                            
                            # Extract displayed URL
                            cite_elem = item.find('cite')
                            display_url = cite_elem.get_text(strip=True) if cite_elem else ""
                            
                            if title and link:
                                # Calculate credibility based on domain
                                credibility_score = self._calculate_search_credibility(link, title, snippet)
                                
                                result = {
                                    'title': title,
                                    'link': link,
                                    'content': snippet,
                                    'published': datetime.now().strftime('%Y-%m-%d'),
                                    'source': display_url or self._extract_domain(link),
                                    'source_type': 'web_search',
                                    'source_detail': f"Search Result via {self.source_name}",
                                    'credibility_info': {
                                        'score': credibility_score,
                                        'category': 'Web Search',
                                        'bias': 'mixed'
                                    },
                                    'metadata': {
                                        'source': 'bing.com',
                                        'source_name': display_url or 'Web Result',
                                        'platform': 'Search Engine',
                                        'content_type': 'web_result',
                                        'search_query': query,
                                        'search_position': len(results) + 1
                                    },
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                results.append(result)
                                
                        except Exception as e:
                            logging.error(f"Error processing Bing result: {e}")
                            continue
                    
                    return results
                    
        except Exception as e:
            logging.error(f"Error searching Bing: {e}")
            
        return []
        
    def _calculate_search_credibility(self, url: str, title: str, snippet: str) -> float:
        """Calculate credibility score for search results."""
        base_score = self.credibility_base
        
        # Domain-based adjustments
        domain = self._extract_domain(url).lower()
        
        # High credibility domains
        high_cred_domains = ['wikipedia.org', 'britannica.com', 'gov', 'edu', 'nature.com', 'science.org', 'bbc.com', 'reuters.com', 'cnn.com', 'nytimes.com']
        if any(hcd in domain for hcd in high_cred_domains):
            base_score += 8
            
        # Medium credibility domains
        med_cred_domains = ['forbes.com', 'bloomberg.com', 'washingtonpost.com', 'guardian.com', 'techcrunch.com', 'wired.com']
        if any(mcd in domain for mcd in med_cred_domains):
            base_score += 5
            
        # Lower credibility indicators
        low_cred_indicators = ['blog', 'forum', 'reddit.com', 'yahoo.answers', 'quora.com']
        if any(lci in domain for lci in low_cred_indicators):
            base_score -= 3
            
        # Content quality indicators
        if len(title) > 20:
            base_score += 2
        if len(snippet) > 100:
            base_score += 3
            
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
        """Main scraping method for Bing search."""
        if not query:
            return []
            
        return await self.search_web(query) 