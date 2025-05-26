"""Product Hunt scraper for tech product launches."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging

logger = logging.getLogger(__name__)

class ProductHuntScraper(WebBasedScraper):
    """Scraper for Product Hunt"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = 'https://www.producthunt.com'
        self.config = config or {}
        self.max_results = self.config.get('max_results', 20)
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape today's products from Product Hunt"""
        try:
            soup = self.get_soup(self.base_url)
            products = []
            
            # Find product containers
            product_containers = soup.find_all('div', {'data-test': 'homepage-section'}) or soup.find_all('article')
            
            for container in product_containers[:self.max_results]:
                try:
                    # Get product name
                    name_elem = container.find('h3') or container.find('h2')
                    if not name_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    
                    # Get link
                    link_elem = container.find('a')
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = self.base_url + link
                    
                    # Get description/tagline
                    desc_elem = container.find('p') or container.find('span')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    # Get upvotes if available
                    votes_elem = container.find(text=re.compile(r'\d+'))
                    votes = votes_elem.strip() if votes_elem else '0'
                    
                    # Get topics/tags if available
                    topics = []
                    topics_container = container.find('div', class_=lambda x: x and 'topics' in x.lower())
                    if topics_container:
                        topic_elements = topics_container.find_all('a')
                        topics = [topic.get_text(strip=True) for topic in topic_elements]
                    
                    # Calculate credibility
                    credibility_score = self._calculate_credibility(votes)
                    
                    product = {
                        'title': name,
                        'link': link,
                        'description': description,
                        'topics': topics,
                        'source': 'Product Hunt',
                        'source_detail': 'Product Hunt - Today',
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Product Launch',
                            'bias': 'community-curated'
                        },
                        'metadata': {
                            'votes': votes,
                            'description': description,
                            'topics': topics
                        },
                        'scraped_at': time.time()
                    }
                    products.append(product)
                    
                except Exception as e:
                    logger.error(f"Error parsing PH product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to scrape Product Hunt: {e}")
            return []
    
    def _calculate_credibility(self, votes: str) -> float:
        """Calculate credibility score based on community engagement"""
        try:
            votes = int(str(votes).replace(',', ''))
            # Base score 85-95 based on votes
            # More votes indicate higher community validation
            base_score = 85 + min((votes / 100), 10)  # Up to 10 points for votes
            return min(base_score, 95)
        except:
            return 85.0  # Default score for PH content 