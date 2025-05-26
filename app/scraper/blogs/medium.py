"""Medium scraper for articles and publications."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging

logger = logging.getLogger(__name__)

class MediumScraper(WebBasedScraper):
    """Scraper for Medium articles"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        self.base_url = 'https://medium.com'
        self.tags = self.config.get('tags', [
            'artificial-intelligence',
            'machine-learning',
            'programming',
            'technology',
            'startup',
            'data-science',
            'web-development',
            'python',
            'javascript'
        ])
        self.publications = self.config.get('publications', [
            'towards-data-science',
            'the-startup',
            'hackernoon',
            'freecodecamp'
        ])
        self.max_articles_per_source = self.config.get('max_articles_per_source', 5)
    
    def scrape_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Scrape Medium articles by tag using RSS"""
        try:
            rss_url = f"https://medium.com/feed/tag/{tag}"
            articles = self.parse_rss(rss_url)
            
            for article in articles:
                # Calculate credibility
                credibility_score = self._calculate_credibility(article)
                
                article.update({
                    'tag': tag,
                    'source': 'Medium',
                    'source_detail': f"Medium - {tag}",
                    'credibility_info': {
                        'score': credibility_score,
                        'category': 'Technical Blog',
                        'bias': 'community-curated'
                    },
                    'metadata': {
                        'tag': tag,
                        'platform': 'Medium',
                        'published_date': article.get('published'),
                        'author': article.get('author')
                    },
                    'scraped_at': time.time()
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape Medium tag {tag}: {e}")
            return []
    
    def scrape_user(self, username: str) -> List[Dict[str, Any]]:
        """Scrape Medium articles by user using RSS"""
        try:
            # Remove @ if present
            username = username.lstrip('@')
            rss_url = f"https://medium.com/feed/@{username}"
            articles = self.parse_rss(rss_url)
            
            for article in articles:
                # Calculate credibility
                credibility_score = self._calculate_credibility(article)
                
                article.update({
                    'username': username,
                    'source': 'Medium',
                    'source_detail': f"Medium - @{username}",
                    'credibility_info': {
                        'score': credibility_score,
                        'category': 'Technical Blog',
                        'bias': 'individual-author'
                    },
                    'metadata': {
                        'username': username,
                        'platform': 'Medium',
                        'published_date': article.get('published'),
                        'author': article.get('author')
                    },
                    'scraped_at': time.time()
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape Medium user {username}: {e}")
            return []
    
    def scrape_publication(self, publication: str) -> List[Dict[str, Any]]:
        """Scrape Medium publication using RSS"""
        try:
            rss_url = f"https://medium.com/feed/{publication}"
            articles = self.parse_rss(rss_url)
            
            for article in articles:
                # Calculate credibility
                credibility_score = self._calculate_credibility(article)
                
                article.update({
                    'publication': publication,
                    'source': 'Medium',
                    'source_detail': f"Medium - {publication}",
                    'credibility_info': {
                        'score': credibility_score,
                        'category': 'Technical Blog',
                        'bias': 'publication-reviewed'
                    },
                    'metadata': {
                        'publication': publication,
                        'platform': 'Medium',
                        'published_date': article.get('published'),
                        'author': article.get('author')
                    },
                    'scraped_at': time.time()
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape Medium publication {publication}: {e}")
            return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape popular Medium content"""
        all_articles = []
        
        # Scrape by tags
        for tag in self.tags:
            articles = self.scrape_by_tag(tag)
            all_articles.extend(articles[:self.max_articles_per_source])
        
        # Scrape publications
        for pub in self.publications:
            articles = self.scrape_publication(pub)
            all_articles.extend(articles[:self.max_articles_per_source])
        
        return all_articles
    
    def _calculate_credibility(self, article: Dict[str, Any]) -> float:
        """Calculate credibility score based on Medium metrics"""
        try:
            # Base score 85-95
            base_score = 85.0
            
            # Factors that increase credibility:
            # 1. Publication article (more editorial oversight)
            if 'publication' in article:
                base_score += 3
            
            # 2. Author has bio/description
            if article.get('author_bio'):
                base_score += 2
            
            # 3. Article has tags
            if article.get('tags'):
                tag_factor = min(len(article['tags']), 3)  # Up to 3 points
                base_score += tag_factor
            
            # 4. Article length/depth
            content = article.get('content', '')
            if len(content) > 3000:  # Long-form content
                base_score += 2
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for Medium content 