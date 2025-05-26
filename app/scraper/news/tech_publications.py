"""Tech publications scraper for specialized technology content and developer resources."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class TechPublicationsScraper(WebBasedScraper):
    """Scraper for specialized tech publications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Tech publications configuration
        self.publications = self.config.get('publications', [
            {
                'name': 'InfoQ',
                'domain': 'infoq.com',
                'base_url': 'https://www.infoq.com',
                'rss_url': 'https://feed.infoq.com',
                'type': 'tech_publication',
                'credibility_base': 92,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article__lead',
                    'author': '.article__author-name'
                }
            },
            {
                'name': 'DZone',
                'domain': 'dzone.com',
                'base_url': 'https://dzone.com',
                'rss_url': 'https://feeds.dzone.com/home',
                'type': 'tech_publication',
                'credibility_base': 90,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-preview',
                    'author': '.article-author'
                }
            },
            {
                'name': 'SD Times',
                'domain': 'sdtimes.com',
                'base_url': 'https://sdtimes.com',
                'rss_url': 'https://sdtimes.com/feed',
                'type': 'tech_publication',
                'credibility_base': 89,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.entry-content p:first-of-type',
                    'author': '.author'
                }
            },
            {
                'name': 'ADT Magazine',
                'domain': 'adtmag.com',
                'base_url': 'https://adtmag.com',
                'rss_url': 'https://adtmag.com/rss-feeds/news.aspx',
                'type': 'tech_publication',
                'credibility_base': 88,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.article-content p:first-of-type',
                    'author': '.author'
                }
            },
            {
                'name': 'The New Stack',
                'domain': 'thenewstack.io',
                'base_url': 'https://thenewstack.io',
                'rss_url': 'https://thenewstack.io/feed',
                'type': 'tech_publication',
                'credibility_base': 91,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.entry-content p:first-of-type',
                    'author': '.author'
                }
            },
            {
                'name': 'JAXenter',
                'domain': 'jaxenter.com',
                'base_url': 'https://jaxenter.com',
                'rss_url': 'https://jaxenter.com/feed',
                'type': 'tech_publication',
                'credibility_base': 88,
                'selectors': {
                    'article': 'article',
                    'title': 'h1',
                    'excerpt': '.entry-content p:first-of-type',
                    'author': '.author'
                }
            }
        ])
        self.max_articles = self.config.get('max_articles', 10)
        
        # Technical topics to focus on
        self.topics = self.config.get('topics', [
            'software development',
            'programming languages',
            'web development',
            'cloud computing',
            'devops',
            'microservices',
            'containers',
            'architecture',
            'apis',
            'testing',
            'security'
        ])
    
    def scrape_publication(self, pub_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape individual tech publication"""
        try:
            name = pub_config['name']
            domain = pub_config['domain']
            base_url = pub_config['base_url']
            
            # Try RSS feed first
            if 'rss_url' in pub_config:
                try:
                    feed = feedparser.parse(pub_config['rss_url'])
                    if feed.entries:
                        articles = []
                        for entry in feed.entries[:self.max_articles]:
                            # Calculate credibility
                            credibility_score = self._calculate_credibility({
                                'title': entry.get('title', ''),
                                'summary': entry.get('summary', ''),
                                'author': entry.get('author', ''),
                                'pub_name': name,
                                'pub_type': pub_config['type']
                            })
                            
                            article = {
                                'title': entry.get('title', ''),
                                'link': entry.get('link', ''),
                                'author': entry.get('author', ''),
                                'summary': entry.get('summary', ''),
                                'published': entry.get('published', ''),
                                'source': domain,
                                'source_name': name,
                                'type': 'Tech Publication',
                                'source_detail': f"Tech Publication - {name}",
                                'credibility_info': {
                                    'score': credibility_score,
                                    'category': 'Technical Content',
                                    'bias': 'developer-focused'
                                },
                                'metadata': {
                                    'source': domain,
                                    'source_name': name,
                                    'source_type': pub_config['type'],
                                    'platform': 'Tech Publication',
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
            selectors = pub_config.get('selectors', {})
            
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
                        'pub_name': name,
                        'pub_type': pub_config['type']
                    })
                    
                    article = {
                        'title': title,
                        'link': link,
                        'summary': excerpt,
                        'author': author,
                        'source': domain,
                        'source_name': name,
                        'type': 'Tech Publication',
                        'source_detail': f"Tech Publication - {name}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Technical Content',
                            'bias': 'developer-focused'
                        },
                        'metadata': {
                            'source': domain,
                            'source_name': name,
                            'source_type': pub_config['type'],
                            'platform': 'Tech Publication',
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
            logger.error(f"Failed to scrape publication {name}: {e}")
            return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape all configured tech publications"""
        all_articles = []
        
        for pub_config in self.publications:
            articles = self.scrape_publication(pub_config)
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
        """Calculate credibility score based on tech publication metrics"""
        try:
            # Get base score from publication configuration
            pub_name = article.get('pub_name', '').lower()
            pub_config = next((pub for pub in self.publications if pub['name'].lower() == pub_name), None)
            base_score = pub_config.get('credibility_base', 85.0) if pub_config else 85.0
            
            # Factors that increase credibility:
            # 1. Has author info
            if article.get('author'):
                base_score += 1
            
            # 2. Has substantial content
            summary = article.get('summary', '')
            if len(summary) > 300:  # Good length summary
                base_score += 1
            
            # 3. Major tech publication bonus
            if any(name.lower() in pub_name for name in ['infoq', 'dzone', 'the new stack']):
                base_score += 2
            
            # 4. Contains relevant technical topics
            title = article.get('title', '').lower()
            summary = article.get('summary', '').lower()
            if any(topic.lower() in title or topic.lower() in summary for topic in self.topics):
                base_score += 1
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for tech publications 