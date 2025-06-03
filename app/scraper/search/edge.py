"""Microsoft Edge search scraper using Bing backend."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import urllib.parse
import re
from bs4 import BeautifulSoup
from ..base import WebBasedScraper

class EdgeScraper(WebBasedScraper):
    """Microsoft Edge search scraper (uses Bing backend)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Edge scraper."""
        super().__init__(config)
        self.source_name = "Microsoft Edge Search"
        self.credibility_base = 86.0  # Edge with enhanced security
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
            logging.error(f"Error in Edge search: {e}")
            return []
        finally:
            # Restore original max_entries
            self.max_entries = original_max
        
    async def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search using Edge's Bing integration."""
        try:
            await self.setup()
            
            # Edge-specific search parameters
            params = {
                'q': query,
                'count': str(self.max_entries),
                'first': '1',
                'FORM': 'PERE',
                'ensearch': '1',  # Enhanced search
                'filters': 'ex1%3a"ez5"'  # Edge filters
            }
            
            search_url = f"{self.search_url}?{urllib.parse.urlencode(params)}"
            
            await self._rate_limit()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    result_items = soup.find_all('li', class_='b_algo')
                    
                    for item in result_items[:self.max_entries]:
                        try:
                            title_elem = item.find('h2')
                            if not title_elem:
                                continue
                                
                            title_link = title_elem.find('a')
                            if not title_link:
                                continue
                                
                            title = title_link.get_text(strip=True)
                            link = title_link.get('href', '')
                            
                            snippet_elem = item.find('div', class_='b_caption')
                            snippet = ""
                            if snippet_elem:
                                snippet_p = snippet_elem.find('p')
                                if snippet_p:
                                    snippet = snippet_p.get_text(strip=True)
                            
                            cite_elem = item.find('cite')
                            display_url = cite_elem.get_text(strip=True) if cite_elem else ""
                            
                            if title and link:
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
                                        'category': 'Web Search (Enhanced Security)',
                                        'bias': 'mixed'
                                    },
                                    'metadata': {
                                        'source': 'edge.microsoft.com',
                                        'source_name': display_url or 'Edge Result',
                                        'platform': 'Microsoft Edge',
                                        'content_type': 'web_result',
                                        'search_query': query,
                                        'search_position': len(results) + 1,
                                        'enhanced_security': True,
                                        'ai_powered': True
                                    },
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                                results.append(result)
                                
                        except Exception as e:
                            logging.error(f"Error processing Edge result: {e}")
                            continue
                    
                    return results
                    
        except Exception as e:
            logging.error(f"Error searching Edge: {e}")
            
        return []
        
    def _calculate_search_credibility(self, url: str, title: str, snippet: str) -> float:
        """Calculate credibility score with Edge's enhanced security."""
        base_score = self.credibility_base
        
        domain = self._extract_domain(url).lower()
        
        # High credibility domains (Edge security standards)
        high_cred_domains = ['microsoft.com', 'windows.com', 'office.com', 'wikipedia.org', 'britannica.com', 'gov', 'edu', 'nature.com', 'science.org', 'bbc.com', 'reuters.com']
        if any(hcd in domain for hcd in high_cred_domains):
            base_score += 8
            
        # Microsoft ecosystem bonus
        ms_domains = ['microsoft.com', 'office.com', 'windows.com', 'xbox.com', 'msn.com', 'outlook.com']
        if any(msd in domain for msd in ms_domains):
            base_score += 5
            
        # Security-verified domains
        secure_indicators = ['https://', 'verified']
        security_score = sum(1 for si in secure_indicators if si in url.lower())
        base_score += security_score * 2
        
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
        """Main scraping method for Edge search."""
        if not query:
            return []
            
        return await self.search_web(query) 