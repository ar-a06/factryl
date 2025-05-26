"""E-commerce and shopping platform scraper for product information and reviews."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import json
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class EcommerceScraper(WebBasedScraper):
    """Scraper for e-commerce platforms and product reviews"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # E-commerce platforms configuration
        self.platforms = self.config.get('platforms', [
            {
                'name': 'Amazon Reviews',
                'domain': 'amazon.com',
                'search_url': 'https://www.amazon.com/s?k={query}',
                'type': 'product_reviews',
                'credibility_base': 80,
                'selectors': {
                    'product': '[data-component-type="s-search-result"]',
                    'title': 'h2 a span',
                    'price': '.a-price-whole',
                    'rating': '.a-icon-alt',
                    'review_count': '.a-size-base',
                    'link': 'h2 a'
                }
            },
            {
                'name': 'Product Hunt',
                'domain': 'producthunt.com',
                'search_url': 'https://www.producthunt.com/search?q={query}',
                'type': 'product_discovery',
                'credibility_base': 85,
                'selectors': {
                    'product': '[data-test="post-item"]',
                    'title': '[data-test="post-name"]',
                    'description': '[data-test="post-tagline"]',
                    'upvotes': '[data-test="vote-count"]',
                    'link': '[data-test="post-url"]'
                }
            },
            {
                'name': 'Hacker News',
                'domain': 'news.ycombinator.com',
                'search_url': 'https://hn.algolia.com/api/v1/search?query={query}&tags=story',
                'type': 'tech_products',
                'credibility_base': 90,
                'api_based': True
            }
        ])
        
        self.max_products = self.config.get('max_products', 30)
        self.min_rating = self.config.get('min_rating', 3.0)
        self.include_reviews = self.config.get('include_reviews', True)

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "ecommerce"

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            # Test basic connectivity to one platform
            if self.platforms:
                test_platform = self.platforms[0]
                if not test_platform.get('api_based', False):
                    test_url = test_platform['search_url'].format(query='test')
                    soup = await self.get_soup_async(test_url)
                    return soup is not None
            return True
        except Exception as e:
            logger.error(f"E-commerce scraper validation failed: {str(e)}")
            return False

    def _extract_rating(self, text: str) -> float:
        """Extract numeric rating from text."""
        if not text:
            return 0.0
            
        # Look for patterns like "4.5 out of 5 stars"
        rating_match = re.search(r'(\d+\.?\d*)\s*out of\s*\d+', text.lower())
        if rating_match:
            return float(rating_match.group(1))
        
        # Look for just numbers
        number_match = re.search(r'(\d+\.?\d*)', text)
        if number_match:
            rating = float(number_match.group(1))
            # Assume 5-star scale if number is reasonable
            return rating if rating <= 5.0 else rating / 20.0  # Convert from 100-point scale
        
        return 0.0

    def _extract_price(self, text: str) -> str:
        """Extract price from text."""
        if not text:
            return ""
            
        # Look for currency symbols and numbers
        price_match = re.search(r'[\$£€¥][\d,]+\.?\d*', text)
        if price_match:
            return price_match.group(0)
        
        return text.strip()

    async def _scrape_hn_api(self, query: str) -> List[Dict[str, Any]]:
        """Scrape Hacker News via API."""
        try:
            url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage={self.max_products}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    products = []
                    
                    for hit in data.get('hits', []):
                        # Calculate credibility
                        credibility_score = self._calculate_credibility({
                            'title': hit.get('title', ''),
                            'author': hit.get('author', ''),
                            'points': hit.get('points', 0),
                            'num_comments': hit.get('num_comments', 0),
                            'source_name': 'Hacker News'
                        })
                        
                        product = {
                            'title': hit.get('title', ''),
                            'link': hit.get('url', '') or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                            'description': hit.get('story_text', '')[:200] + "...",
                            'author': hit.get('author', ''),
                            'points': hit.get('points', 0),
                            'comments': hit.get('num_comments', 0),
                            'created_at': hit.get('created_at', ''),
                            'source': 'hacker_news',
                            'source_name': 'Hacker News',
                            'type': 'Tech Product Discussion',
                            'source_detail': 'Hacker News - Tech Community',
                            'credibility_info': {
                                'score': credibility_score,
                                'category': 'Tech Community',
                                'bias': 'tech-focused'
                            },
                            'metadata': {
                                'platform': 'Hacker News',
                                'author': hit.get('author', ''),
                                'points': hit.get('points', 0),
                                'comments': hit.get('num_comments', 0),
                                'discussion_type': 'tech_product'
                            },
                            'scraped_at': time.time()
                        }
                        products.append(product)
                    
                    return products
        except Exception as e:
            logger.error(f"Error scraping Hacker News API: {e}")
            return []

    async def _scrape_platform(self, platform_config: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Scrape individual e-commerce platform."""
        try:
            name = platform_config['name']
            domain = platform_config['domain']
            
            # Handle API-based platforms
            if platform_config.get('api_based', False):
                if 'news.ycombinator.com' in domain:
                    return await self._scrape_hn_api(query)
                else:
                    logger.warning(f"API-based platform {name} not implemented")
                    return []
            
            # Web scraping for other platforms
            search_url = platform_config['search_url'].format(query=query.replace(' ', '+'))
            soup = await self.get_soup_async(search_url)
            
            if not soup:
                return []
            
            products = []
            selectors = platform_config.get('selectors', {})
            
            # Find product containers
            product_selector = selectors.get('product', '.product')
            product_containers = soup.select(product_selector)
            
            for container in product_containers[:self.max_products]:
                try:
                    # Extract product information
                    title_elem = container.select_one(selectors.get('title', 'h2'))
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    if not title:
                        continue
                    
                    # Get link
                    link_elem = container.select_one(selectors.get('link', 'a'))
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"https://{domain}{link}"
                    
                    # Get price
                    price_elem = container.select_one(selectors.get('price', '.price'))
                    price = self._extract_price(price_elem.get_text(strip=True) if price_elem else '')
                    
                    # Get rating
                    rating_elem = container.select_one(selectors.get('rating', '.rating'))
                    rating = self._extract_rating(rating_elem.get_text(strip=True) if rating_elem else '')
                    
                    # Skip low-rated products
                    if rating > 0 and rating < self.min_rating:
                        continue
                    
                    # Get review count
                    review_elem = container.select_one(selectors.get('review_count', '.reviews'))
                    review_count = review_elem.get_text(strip=True) if review_elem else ''
                    
                    # Get description
                    desc_elem = container.select_one(selectors.get('description', '.description'))
                    description = desc_elem.get_text(strip=True)[:200] + "..." if desc_elem else ''
                    
                    # Calculate credibility
                    credibility_score = self._calculate_credibility({
                        'title': title,
                        'rating': rating,
                        'price': price,
                        'review_count': review_count,
                        'source_name': name,
                        'platform_type': platform_config['type']
                    })
                    
                    product = {
                        'title': title,
                        'link': link,
                        'description': description,
                        'price': price,
                        'rating': rating,
                        'review_count': review_count,
                        'source': platform_config['type'],
                        'source_name': name,
                        'type': 'Product',
                        'source_detail': f"{name} - Product Listing",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'E-commerce',
                            'bias': 'commercial'
                        },
                        'metadata': {
                            'platform': name,
                            'domain': domain,
                            'platform_type': platform_config['type'],
                            'price': price,
                            'rating': rating,
                            'review_count': review_count
                        },
                        'scraped_at': time.time()
                    }
                    products.append(product)
                    
                except Exception as e:
                    logger.error(f"Error parsing product from {name}: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to scrape platform {platform_config['name']}: {e}")
            return []

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """Scrape e-commerce platforms for products matching the query."""
        logger.info(f"Scraping e-commerce platforms for: {query}")
        
        all_products = []
        
        for platform_config in self.platforms:
            products = await self._scrape_platform(platform_config, query)
            all_products.extend(products)
        
        # Sort by credibility and rating
        sorted_products = sorted(
            all_products,
            key=lambda x: (x['credibility_info']['score'], x.get('rating', 0)),
            reverse=True
        )
        
        return sorted_products[:self.max_products] 