"""Substack scraper for newsletter content."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging

logger = logging.getLogger(__name__)

class SubstackScraper(WebBasedScraper):
    """Scraper for Substack newsletters"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        self.popular_substacks = self.config.get('substacks', [
            'stratechery.com',
            'themargins.substack.com',
            'platformer.news',
            'morningbrew.com',
            'axios.com'
        ])
        self.max_posts = self.config.get('max_posts', 10)
    
    def scrape_substack(self, domain: str) -> List[Dict[str, Any]]:
        """Scrape individual Substack"""
        try:
            # Try RSS feed first
            rss_url = f"https://{domain}/feed"
            articles = self.parse_rss(rss_url)
            
            if articles:
                for article in articles:
                    # Calculate credibility
                    credibility_score = self._calculate_credibility(article)
                    
                    article.update({
                        'substack': domain,
                        'source': 'Substack',
                        'source_detail': f"Substack - {domain}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Newsletter',
                            'bias': 'expert-curated'
                        },
                        'metadata': {
                            'substack': domain,
                            'platform': 'Substack',
                            'published_date': article.get('published'),
                            'author': article.get('author')
                        },
                        'scraped_at': time.time()
                    })
                return articles
            
            # Fallback to web scraping
            url = f"https://{domain}"
            soup = self.get_soup(url)
            articles = []
            
            # Find post containers
            post_containers = soup.find_all('div', class_=lambda x: x and 'post' in x.lower())
            
            for container in post_containers[:self.max_posts]:
                try:
                    title_elem = container.find('h1') or container.find('h2') or container.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    link_elem = container.find('a')
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"https://{domain}{link}"
                    
                    # Get excerpt
                    excerpt_elem = container.find('p')
                    excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ''
                    
                    # Get author if available
                    author_elem = container.find(class_=lambda x: x and 'author' in x.lower())
                    author = author_elem.get_text(strip=True) if author_elem else ''
                    
                    # Calculate credibility
                    credibility_score = self._calculate_credibility({
                        'title': title,
                        'summary': excerpt,
                        'author': author
                    })
                    
                    article = {
                        'title': title,
                        'link': link,
                        'summary': excerpt,
                        'author': author,
                        'substack': domain,
                        'source': 'Substack',
                        'source_detail': f"Substack - {domain}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Newsletter',
                            'bias': 'expert-curated'
                        },
                        'metadata': {
                            'substack': domain,
                            'platform': 'Substack',
                            'author': author
                        },
                        'scraped_at': time.time()
                    }
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error parsing Substack post: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape Substack {domain}: {e}")
            return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape multiple popular Substacks"""
        all_articles = []
        
        for substack in self.popular_substacks:
            articles = self.scrape_substack(substack)
            all_articles.extend(articles[:self.max_posts])
        
        return all_articles
    
    def _calculate_credibility(self, article: Dict[str, Any]) -> float:
        """Calculate credibility score based on Substack metrics"""
        try:
            # Base score 85-95
            base_score = 85.0
            
            # Factors that increase credibility:
            # 1. Has author info
            if article.get('author'):
                base_score += 2
            
            # 2. Has substantial content
            summary = article.get('summary', '')
            if len(summary) > 500:  # Long summary/preview
                base_score += 2
            
            # 3. From established Substack
            domain = article.get('substack', '')
            if any(established in domain for established in ['stratechery', 'axios', 'morningbrew']):
                base_score += 3
            
            # 4. Has comments/engagement (if available)
            if article.get('comment_count', 0) > 10:
                base_score += 3
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for Substack content 