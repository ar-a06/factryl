"""Business news scraper for major financial and business news sites."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class BusinessNewsScraper(WebBasedScraper):
    """Scraper for business news sites"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Business news sources configuration
        self.news_sources = self.config.get('sources', [
            {
                'name': 'Financial Times',
                'domain': 'ft.com',
                'base_url': 'https://www.ft.com',
                'rss_url': 'https://www.ft.com/rss/home',
                'type': 'business_news',
                'credibility_base': 95,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-body p:first-of-type',
                    'author': '.author-name'
                }
            },
            {
                'name': 'Bloomberg',
                'domain': 'bloomberg.com',
                'base_url': 'https://www.bloomberg.com',
                'rss_url': 'https://feeds.bloomberg.com/markets/news.rss',
                'type': 'business_news',
                'credibility_base': 94,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.body-content p:first-of-type',
                    'author': '.author-name'
                }
            },
            {
                'name': 'Reuters Business',
                'domain': 'reuters.com',
                'base_url': 'https://www.reuters.com/business',
                'rss_url': 'https://www.reuters.com/business/rss',
                'type': 'business_news',
                'credibility_base': 95,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-body p:first-of-type',
                    'author': '.author-name'
                }
            },
            {
                'name': 'Wall Street Journal',
                'domain': 'wsj.com',
                'base_url': 'https://www.wsj.com',
                'rss_url': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
                'type': 'business_news',
                'credibility_base': 93,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-content p:first-of-type',
                    'author': '.author'
                }
            },
            {
                'name': 'CNBC',
                'domain': 'cnbc.com',
                'base_url': 'https://www.cnbc.com',
                'rss_url': 'https://www.cnbc.com/id/10000664/device/rss/rss.html',
                'type': 'business_news',
                'credibility_base': 88,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.group p:first-of-type',
                    'author': '.Author-authorName'
                }
            },
            {
                'name': 'The Economist',
                'domain': 'economist.com',
                'base_url': 'https://www.economist.com',
                'rss_url': 'https://www.economist.com/business/rss.xml',
                'type': 'business_news',
                'credibility_base': 94,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article__body p:first-of-type',
                    'author': '.author'
                }
            }
        ])
        self.max_articles = self.config.get('max_articles', 10)
        
        # Categories to focus on
        self.categories = self.config.get('categories', [
            'technology sector',
            'startups',
            'venture capital',
            'tech companies',
            'digital economy',
            'innovation',
            'entrepreneurship',
            'tech industry'
        ])
    
    def scrape_source(self, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape individual news source"""
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
                                'type': 'Business News',
                                'source_detail': f"Business News - {name}",
                                'credibility_info': {
                                    'score': credibility_score,
                                    'category': 'Business News',
                                    'bias': 'business-focused'
                                },
                                'metadata': {
                                    'source': domain,
                                    'source_name': name,
                                    'source_type': source_config['type'],
                                    'platform': 'Business News',
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
                        'type': 'Business News',
                        'source_detail': f"Business News - {name}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Business News',
                            'bias': 'business-focused'
                        },
                        'metadata': {
                            'source': domain,
                            'source_name': name,
                            'source_type': source_config['type'],
                            'platform': 'Business News',
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
        """Scrape all configured business news sources"""
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
        """Calculate credibility score based on business news metrics"""
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
            
            # 3. Major publication bonus
            if any(name.lower() in source_name for name in ['financial times', 'bloomberg', 'reuters', 'wall street journal']):
                base_score += 2
            
            # 4. Contains relevant tech business categories
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            if any(cat.lower() in title or cat.lower() in summary for cat in self.categories):
                base_score += 1
            
            return min(base_score, 98.0)  # Cap at 98
            
        except:
            return 85.0  # Default score for business news 