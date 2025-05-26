"""Research blog scraper for major research labs and institutions."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ResearchBlogScraper(WebBasedScraper):
    """Scraper for research lab blogs"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Research lab blogs configuration
        self.research_blogs = self.config.get('blogs', [
            {
                'name': 'DeepMind',
                'domain': 'deepmind.com',
                'base_url': 'https://deepmind.com/blog',
                'rss_url': 'https://deepmind.com/blog/feed/basic/',
                'type': 'company',
                'credibility_base': 95,
                'selectors': {
                    'post': 'article',
                    'title': 'h1',
                    'excerpt': '.excerpt',
                    'author': '.author'
                }
            },
            {
                'name': 'OpenAI',
                'domain': 'openai.com',
                'base_url': 'https://openai.com/blog',
                'rss_url': 'https://openai.com/blog/rss.xml',
                'type': 'company',
                'credibility_base': 95,
                'selectors': {
                    'post': 'article',
                    'title': 'h1',
                    'excerpt': '.post-excerpt',
                    'author': '.author'
                }
            },
            {
                'name': 'Google Research',
                'domain': 'ai.googleblog.com',
                'base_url': 'https://ai.googleblog.com/',
                'rss_url': 'https://ai.googleblog.com/feeds/posts/default',
                'type': 'company',
                'credibility_base': 95,
                'selectors': {
                    'post': '.post',
                    'title': 'h2.title',
                    'excerpt': '.post-excerpt',
                    'author': '.author'
                }
            },
            {
                'name': 'Microsoft Research',
                'domain': 'microsoft.com',
                'base_url': 'https://www.microsoft.com/en-us/research/blog/',
                'rss_url': 'https://www.microsoft.com/en-us/research/feed/',
                'type': 'company',
                'credibility_base': 95,
                'selectors': {
                    'post': 'article',
                    'title': 'h1',
                    'excerpt': '.entry-summary',
                    'author': '.author'
                }
            },
            {
                'name': 'Meta AI Research',
                'domain': 'ai.meta.com',
                'base_url': 'https://ai.meta.com/blog/',
                'rss_url': 'https://ai.meta.com/blog/rss/',
                'type': 'company',
                'credibility_base': 95,
                'selectors': {
                    'post': 'article',
                    'title': 'h1',
                    'excerpt': '.excerpt',
                    'author': '.author'
                }
            }
        ])
        self.max_posts = self.config.get('max_posts', 10)
    
    def scrape_blog(self, blog_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape individual research blog"""
        try:
            name = blog_config['name']
            domain = blog_config['domain']
            base_url = blog_config['base_url']
            
            # Try RSS feed first
            if 'rss_url' in blog_config:
                try:
                    feed = feedparser.parse(blog_config['rss_url'])
                    if feed.entries:
                        articles = []
                        for entry in feed.entries[:self.max_posts]:
                            # Calculate credibility
                            credibility_score = self._calculate_credibility({
                                'title': entry.get('title', ''),
                                'summary': entry.get('summary', ''),
                                'author': entry.get('author', ''),
                                'blog_name': name,
                                'blog_type': blog_config['type']
                            })
                            
                            article = {
                                'title': entry.get('title', ''),
                                'link': entry.get('link', ''),
                                'author': entry.get('author', ''),
                                'summary': entry.get('summary', ''),
                                'published': entry.get('published', ''),
                                'blog': domain,
                                'blog_name': name,
                                'source': 'Research Blog',
                                'source_detail': f"Research Blog - {name}",
                                'credibility_info': {
                                    'score': credibility_score,
                                    'category': 'Research Publication',
                                    'bias': f"{blog_config['type']}-research"
                                },
                                'metadata': {
                                    'blog': domain,
                                    'blog_name': name,
                                    'blog_type': blog_config['type'],
                                    'platform': 'Research Blog',
                                    'published_date': entry.get('published', ''),
                                    'author': entry.get('author', '')
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
            selectors = blog_config.get('selectors', {})
            
            # Find post containers
            post_selector = selectors.get('post', 'article')
            post_containers = soup.select(post_selector)
            
            for container in post_containers[:self.max_posts]:
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
                    excerpt = self._extract_text(container, selectors.get('excerpt', '.excerpt'))
                    
                    # Get author
                    author = self._extract_text(container, selectors.get('author', '.author'))
                    
                    # Calculate credibility
                    credibility_score = self._calculate_credibility({
                        'title': title,
                        'summary': excerpt,
                        'author': author,
                        'blog_name': name,
                        'blog_type': blog_config['type']
                    })
                    
                    article = {
                        'title': title,
                        'link': link,
                        'summary': excerpt,
                        'author': author,
                        'blog': domain,
                        'blog_name': name,
                        'source': 'Research Blog',
                        'source_detail': f"Research Blog - {name}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Research Publication',
                            'bias': f"{blog_config['type']}-research"
                        },
                        'metadata': {
                            'blog': domain,
                            'blog_name': name,
                            'blog_type': blog_config['type'],
                            'platform': 'Research Blog',
                            'author': author
                        },
                        'scraped_at': time.time()
                    }
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error parsing blog post from {name}: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape blog {name}: {e}")
            return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape all configured research blogs"""
        all_articles = []
        
        for blog_config in self.research_blogs:
            articles = self.scrape_blog(blog_config)
            all_articles.extend(articles[:self.max_posts])
        
        return all_articles
    
    def _extract_text(self, container: BeautifulSoup, selector: str) -> str:
        """Extract text using CSS selector"""
        try:
            element = container.select_one(selector)
            return element.get_text(strip=True) if element else ''
        except:
            return ''
    
    def _calculate_credibility(self, article: Dict[str, Any]) -> float:
        """Calculate credibility score based on research blog metrics"""
        try:
            # Get base score from blog configuration
            blog_name = article.get('blog_name', '').lower()
            blog_config = next((blog for blog in self.research_blogs if blog['name'].lower() == blog_name), None)
            base_score = blog_config.get('credibility_base', 90.0) if blog_config else 90.0
            
            # Factors that increase credibility:
            # 1. Has author info
            if article.get('author'):
                base_score += 1
            
            # 2. Has substantial content
            summary = article.get('summary', '')
            if len(summary) > 500:  # Long summary/preview
                base_score += 1
            
            # 3. Major research lab bonus
            if any(name.lower() in blog_name for name in ['deepmind', 'openai', 'google', 'microsoft', 'meta']):
                base_score += 2
            
            return min(base_score, 98.0)  # Cap at 98
            
        except:
            return 90.0  # Default score for research blog content 