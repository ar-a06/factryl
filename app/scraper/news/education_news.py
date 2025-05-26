"""Education news scraper for education news and academic publications."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class EducationNewsScraper(WebBasedScraper):
    """Scraper for education news sites"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Education news sources configuration
        self.news_sources = self.config.get('sources', [
            {
                'name': 'Inside Higher Ed',
                'domain': 'insidehighered.com',
                'base_url': 'https://www.insidehighered.com',
                'rss_url': 'https://www.insidehighered.com/feed/news',
                'type': 'education_news',
                'credibility_base': 92,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-body p:first-of-type',
                    'author': '.author-name'
                }
            },
            {
                'name': 'Chronicle of Higher Education',
                'domain': 'chronicle.com',
                'base_url': 'https://www.chronicle.com',
                'rss_url': 'https://www.chronicle.com/rss',
                'type': 'education_news',
                'credibility_base': 93,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-content p:first-of-type',
                    'author': '.author-name'
                }
            },
            {
                'name': 'Education Week',
                'domain': 'edweek.org',
                'base_url': 'https://www.edweek.org',
                'rss_url': 'https://www.edweek.org/feed',
                'type': 'education_news',
                'credibility_base': 91,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.content p:first-of-type',
                    'author': '.author'
                }
            },
            {
                'name': 'Times Higher Education',
                'domain': 'timeshighereducation.com',
                'base_url': 'https://www.timeshighereducation.com',
                'rss_url': 'https://www.timeshighereducation.com/feed',
                'type': 'education_news',
                'credibility_base': 92,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article__content p:first-of-type',
                    'author': '.article__author'
                }
            },
            {
                'name': 'EdSurge',
                'domain': 'edsurge.com',
                'base_url': 'https://www.edsurge.com',
                'rss_url': 'https://www.edsurge.com/feed',
                'type': 'education_news',
                'credibility_base': 88,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-body p:first-of-type',
                    'author': '.author-name'
                }
            },
            {
                'name': 'Campus Technology',
                'domain': 'campustechnology.com',
                'base_url': 'https://campustechnology.com',
                'rss_url': 'https://campustechnology.com/rss-feeds/news.aspx',
                'type': 'education_news',
                'credibility_base': 87,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-content p:first-of-type',
                    'author': '.author'
                }
            }
        ])
        self.max_articles = self.config.get('max_articles', 10)
        
        # Education topics to focus on
        self.categories = self.config.get('categories', [
            'higher education',
            'edtech',
            'online learning',
            'stem education',
            'computer science education',
            'digital learning',
            'educational technology',
            'academic research',
            'teaching methods',
            'education policy'
        ])
    
    def scrape_source(self, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape individual education news source"""
        try:
            name = source_config['name']
            domain = source_config['domain']
            base_url = source_config['base_url']
            
            # Try RSS feed first
            if 'rss_url' in source_config:
                try:
                    feed = feedparser.parse(source_config['rss_url'])
                    if feed.entries:
                        articles = []
                        for entry in feed.entries[:self.max_articles]:
                            # Calculate credibility
                            credibility_score = self._calculate_credibility({
                                'title': entry.get('title', ''),
                                'summary': entry.get('summary', ''),
                                'author': entry.get('author', ''),
                                'source_name': name,
                                'source_type': source_config['type']
                            })
                            
                            article = {
                                'title': entry.get('title', ''),
                                'link': entry.get('link', ''),
                                'author': entry.get('author', ''),
                                'summary': entry.get('summary', ''),
                                'published': entry.get('published', ''),
                                'source': domain,
                                'source_name': name,
                                'type': 'Education News',
                                'source_detail': f"Education News - {name}",
                                'credibility_info': {
                                    'score': credibility_score,
                                    'category': 'Education News',
                                    'bias': 'education-focused'
                                },
                                'metadata': {
                                    'source': domain,
                                    'source_name': name,
                                    'source_type': source_config['type'],
                                    'platform': 'Education News',
                                    'published_date': entry.get('published', ''),
                                    'author': entry.get('author', ''),
                                    'categories': [tag.get('term', '') for tag in entry.get('tags', [])]
                                },
                                'scraped_at': time.time()
                            }
                            articles.append(article)
                        return articles
                except Exception as e:
                    logger.error(f"Failed to parse RSS feed for {name}: {e}")
            
            # Fallback to web scraping
            soup = self.get_soup(base_url)
            articles = []
            
            # Get selectors
            selectors = source_config.get('selectors', {})
            
            # Find article containers
            article_selector = selectors.get('article', 'article')
            article_containers = soup.select(article_selector)
            
            for container in article_containers[:self.max_articles]:
                try:
                    # Get title
                    title = self._extract_text(container, selectors.get('title', 'h1'))
                    if not title:
                        continue
                    
                    # Get link
                    link_elem = container.find('a')
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"https://{domain}{link}"
                    
                    # Get excerpt
                    excerpt = self._extract_text(container, selectors.get('excerpt', 'p'))
                    
                    # Get author
                    author = self._extract_text(container, selectors.get('author', '.author'))
                    
                    # Calculate credibility
                    credibility_score = self._calculate_credibility({
                        'title': title,
                        'summary': excerpt,
                        'author': author,
                        'source_name': name,
                        'source_type': source_config['type']
                    })
                    
                    article = {
                        'title': title,
                        'link': link,
                        'summary': excerpt,
                        'author': author,
                        'source': domain,
                        'source_name': name,
                        'type': 'Education News',
                        'source_detail': f"Education News - {name}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Education News',
                            'bias': 'education-focused'
                        },
                        'metadata': {
                            'source': domain,
                            'source_name': name,
                            'source_type': source_config['type'],
                            'platform': 'Education News',
                            'author': author
                        },
                        'scraped_at': time.time()
                    }
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error parsing article from {name}: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape source {name}: {e}")
            return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape all configured education news sources"""
        all_articles = []
        
        for source_config in self.news_sources:
            articles = self.scrape_source(source_config)
            all_articles.extend(articles[:self.max_articles])
        
        return all_articles
    
    def _extract_text(self, container: BeautifulSoup, selector: str) -> str:
        """Extract text using CSS selector"""
        try:
            element = container.select_one(selector)
            return element.get_text(strip=True) if element else ''
        except:
            return ''
    
    def _calculate_credibility(self, article: Dict[str, Any]) -> float:
        """Calculate credibility score based on education news metrics"""
        try:
            # Get base score from source configuration
            source_name = article.get('source_name', '').lower()
            source_config = next((src for src in self.news_sources if src['name'].lower() == source_name), None)
            base_score = source_config.get('credibility_base', 85.0) if source_config else 85.0
            
            # Factors that increase credibility:
            # 1. Has author info
            if article.get('author'):
                base_score += 1
            
            # 2. Has substantial content
            summary = article.get('summary', '')
            if len(summary) > 300:  # Good length summary
                base_score += 1
            
            # 3. Major education publication bonus
            if any(name.lower() in source_name for name in ['chronicle', 'inside higher ed', 'times higher education']):
                base_score += 2
            
            # 4. Contains relevant education topics
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            if any(cat.lower() in title or cat.lower() in summary for cat in self.categories):
                base_score += 1
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for education news 