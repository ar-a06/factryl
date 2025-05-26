"""Government and official data scraper for public records and open data."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import json
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class GovernmentDataScraper(WebBasedScraper):
    """Scraper for government websites and open data platforms"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Government data sources configuration
        self.sources = self.config.get('sources', [
            {
                'name': 'Data.gov',
                'domain': 'data.gov',
                'search_url': 'https://catalog.data.gov/dataset?q={query}',
                'type': 'open_data',
                'credibility_base': 95,
                'selectors': {
                    'dataset': '.dataset-item',
                    'title': '.dataset-title a',
                    'description': '.dataset-notes',
                    'organization': '.dataset-publisher',
                    'link': '.dataset-title a'
                }
            },
            {
                'name': 'SEC EDGAR',
                'domain': 'sec.gov',
                'search_url': 'https://www.sec.gov/edgar/search/?r=el#/q={query}',
                'type': 'financial_filings',
                'credibility_base': 98,
                'api_url': 'https://www.sec.gov/files/company_tickers.json'
            },
            {
                'name': 'USA.gov',
                'domain': 'usa.gov',
                'search_url': 'https://search.usa.gov/search?utf8=✓&affiliate=usagov&query={query}',
                'type': 'government_info',
                'credibility_base': 92,
                'selectors': {
                    'result': '.web-result',
                    'title': '.result-title a',
                    'description': '.result-desc',
                    'url': '.result-url',
                    'link': '.result-title a'
                }
            },
            {
                'name': 'FDA',
                'domain': 'fda.gov',
                'search_url': 'https://www.fda.gov/search?s={query}',
                'type': 'health_data',
                'credibility_base': 96,
                'selectors': {
                    'result': '.views-row',
                    'title': '.views-field-title a',
                    'description': '.views-field-body',
                    'date': '.views-field-created',
                    'link': '.views-field-title a'
                }
            }
        ])
        
        self.max_results = self.config.get('max_results', 25)
        self.include_metadata = self.config.get('include_metadata', True)
        self.data_types = self.config.get('data_types', ['datasets', 'reports', 'filings', 'policies'])

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "government"

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            # Test connectivity to USA.gov as a reliable government source
            test_url = "https://www.usa.gov"
            soup = await self.get_soup_async(test_url)
            return soup is not None
        except Exception as e:
            logger.error(f"Government data scraper validation failed: {str(e)}")
            return False

    def _extract_date(self, text: str) -> str:
        """Extract and format date from text."""
        if not text:
            return ""
            
        # Common date patterns
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(\d{4}-\d{2}-\d{2})',      # YYYY-MM-DD
            r'(\w+ \d{1,2}, \d{4})',     # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return text.strip()

    def _calculate_gov_credibility(self, data: Dict[str, Any]) -> float:
        """Calculate credibility score for government data."""
        try:
            base_score = 85.0  # Government sources start with high credibility
            
            source_name = data.get('source_name', '').lower()
            
            # Official government domains get highest scores
            if any(domain in source_name for domain in ['sec.gov', 'fda.gov', 'cdc.gov', 'nih.gov']):
                base_score = 98.0
            elif 'data.gov' in source_name:
                base_score = 95.0
            elif '.gov' in source_name:
                base_score = 92.0
            
            # Data type credibility adjustments
            data_type = data.get('type', '').lower()
            if 'financial_filings' in data_type:
                base_score += 3  # SEC filings are highly regulated
            elif 'health_data' in data_type:
                base_score += 2  # Health data is well-regulated
            elif 'open_data' in data_type:
                base_score += 1  # Open data is transparent
            
            # Recency factor
            date_str = data.get('date', '')
            if date_str:
                try:
                    # Assume recent data is more relevant
                    current_year = datetime.now().year
                    if str(current_year) in date_str or str(current_year - 1) in date_str:
                        base_score += 2
                except:
                    pass
            
            return min(100.0, max(0.0, base_score))
            
        except Exception:
            return 90.0  # Default high score for government sources

    async def _scrape_source(self, source_config: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Scrape individual government data source."""
        try:
            name = source_config['name']
            domain = source_config['domain']
            source_type = source_config['type']
            
            # Special handling for SEC EDGAR (API-based)
            if 'sec.gov' in domain and source_config.get('api_url'):
                return await self._scrape_sec_data(query)
            
            # Web scraping for other sources
            search_url = source_config['search_url'].format(query=query.replace(' ', '+'))
            soup = await self.get_soup_async(search_url)
            
            if not soup:
                return []
            
            results = []
            selectors = source_config.get('selectors', {})
            
            # Find result containers
            result_selector = selectors.get('result', selectors.get('dataset', '.result'))
            result_containers = soup.select(result_selector)
            
            for container in result_containers[:self.max_results]:
                try:
                    # Extract title
                    title_elem = container.select_one(selectors.get('title', 'h2 a'))
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    if not title:
                        continue
                    
                    # Get link
                    link_elem = container.select_one(selectors.get('link', 'a'))
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"https://{domain}{link}"
                    
                    # Get description
                    desc_elem = container.select_one(selectors.get('description', '.description'))
                    description = desc_elem.get_text(strip=True)[:300] + "..." if desc_elem else ''
                    
                    # Get organization/publisher
                    org_elem = container.select_one(selectors.get('organization', '.organization'))
                    organization = org_elem.get_text(strip=True) if org_elem else name
                    
                    # Get date
                    date_elem = container.select_one(selectors.get('date', '.date'))
                    date = self._extract_date(date_elem.get_text(strip=True) if date_elem else '')
                    
                    # Calculate credibility
                    credibility_score = self._calculate_gov_credibility({
                        'title': title,
                        'source_name': name,
                        'type': source_type,
                        'organization': organization,
                        'date': date
                    })
                    
                    result = {
                        'title': title,
                        'link': link,
                        'description': description,
                        'organization': organization,
                        'date': date,
                        'source': source_type,
                        'source_name': name,
                        'type': 'Government Data',
                        'source_detail': f"Government - {name}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Official Government',
                            'bias': 'institutional'
                        },
                        'metadata': {
                            'platform': name,
                            'domain': domain,
                            'data_type': source_type,
                            'organization': organization,
                            'published_date': date,
                            'authority_level': 'federal' if '.gov' in domain else 'institutional'
                        },
                        'scraped_at': time.time()
                    }
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error parsing result from {name}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to scrape government source {source_config['name']}: {e}")
            return []

    async def _scrape_sec_data(self, query: str) -> List[Dict[str, Any]]:
        """Special handling for SEC EDGAR data."""
        try:
            # This is a simplified version - full SEC integration would require
            # parsing XBRL documents and using the full EDGAR API
            results = []
            
            # For demo, create a notice about SEC data availability
            result = {
                'title': f'SEC EDGAR filings available for: {query}',
                'link': f'https://www.sec.gov/edgar/search/#/q={query}',
                'description': 'Access official SEC filings, 10-K reports, proxy statements, and other corporate disclosures through the EDGAR database.',
                'organization': 'U.S. Securities and Exchange Commission',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'financial_filings',
                'source_name': 'SEC EDGAR',
                'type': 'Government Data',
                'source_detail': 'Government - SEC EDGAR',
                'credibility_info': {
                    'score': 98.0,
                    'category': 'Official Government',
                    'bias': 'regulatory'
                },
                'metadata': {
                    'platform': 'SEC EDGAR',
                    'domain': 'sec.gov',
                    'data_type': 'financial_filings',
                    'organization': 'SEC',
                    'authority_level': 'federal',
                    'regulation_type': 'financial'
                },
                'scraped_at': time.time()
            }
            results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping SEC data: {e}")
            return []

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """Scrape government data sources for information matching the query."""
        logger.info(f"Scraping government data sources for: {query}")
        
        all_results = []
        
        for source_config in self.sources:
            results = await self._scrape_source(source_config, query)
            all_results.extend(results)
        
        # Sort by credibility score (government sources are generally high credibility)
        sorted_results = sorted(
            all_results,
            key=lambda x: x['credibility_info']['score'],
            reverse=True
        )
        
        return sorted_results[:self.max_results] 