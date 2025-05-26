"""Ghost blog scraper for technical blogs and publications."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging

logger = logging.getLogger(__name__)

class GhostBlogScraper(WebBasedScraper):
    """Scraper for Ghost-powered blogs"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        self.ghost_blogs = self.config.get('blogs', [
            'blog.ghost.org',
            'www.troyhunt.com',
            'kentcdodds.com/blog',
            'overreacted.io'
        ])
        self.max_posts = self.config.get('max_posts', 10)
    
    def scrape_ghost_blog(self, domain: str) -> List[Dict[str, Any]]:
        """Scrape individual Ghost blog"""
        try:
            # Try RSS feed first
            rss_urls = [
                f"https://{domain}/rss/",
                f"https://{domain}/feed/",
                f"https://{domain}/rss.xml"
            ]
            
            for rss_url in rss_urls:
                try:
                    articles = self.parse_rss(rss_url)
                    if articles:
                        for article in articles:
                            # Calculate credibility
                            credibility_score = self._calculate_credibility(article)
                            
                            article.update({
                                'blog': domain,
                                'source': 'Ghost Blog',
                                'source_detail': f"Ghost Blog - {domain}",
                                'credibility_info': {
                                    'score': credibility_score,
                                    'category': 'Technical Blog',
                                    'bias': 'expert-authored'
                                },
                                'metadata': {
                                    'blog': domain,
                                    'platform': 'Ghost',
                                    'published_date': article.get('published'),
                                    'author': article.get('author')
                                },
                                'scraped_at': time.time()
                            })
                        return articles
                except:
                    continue
            
            # Fallback to web scraping
            url = f"https://{domain}"
            soup = self.get_soup(url)
            articles = []
            
            # Common Ghost selectors
            post_selectors = [
                'article.post',
                '.post-card',
                '.gh-card',
                'article'
            ]
            
            post_containers = []
            for selector in post_selectors:
                containers = soup.select(selector)
                if containers:
                    post_containers = containers
                    break
            
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
                    
                    # Get tags/categories
                    tags = []
                    tags_container = container.find(class_=lambda x: x and ('tags' in x.lower() or 'categories' in x.lower()))
                    if tags_container:
                        tag_elements = tags_container.find_all('a')
                        tags = [tag.get_text(strip=True) for tag in tag_elements]
                    
                    # Calculate credibility
                    credibility_score = self._calculate_credibility({
                        'title': title,
                        'summary': excerpt,
                        'author': author,
                        'tags': tags
                    })
                    
                    article = {
                        'title': title,
                        'link': link,
                        'summary': excerpt,
                        'author': author,
                        'tags': tags,
                        'blog': domain,
                        'source': 'Ghost Blog',
                        'source_detail': f"Ghost Blog - {domain}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Technical Blog',
                            'bias': 'expert-authored'
                        },
                        'metadata': {
                            'blog': domain,
                            'platform': 'Ghost',
                            'author': author,
                            'tags': tags
                        },
                        'scraped_at': time.time()
                    }
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error parsing Ghost blog post: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to scrape Ghost blog {domain}: {e}")
            return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape multiple Ghost blogs"""
        all_articles = []
        
        for blog in self.ghost_blogs:
            articles = self.scrape_ghost_blog(blog)
            all_articles.extend(articles[:self.max_posts])
        
        return all_articles
    
    def _calculate_credibility(self, article: Dict[str, Any]) -> float:
        """Calculate credibility score based on Ghost blog metrics"""
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
            
            # 3. Has tags/categories
            tags = article.get('tags', [])
            if tags:
                tag_factor = min(len(tags), 3)  # Up to 3 points
                base_score += tag_factor
            
            # 4. From established blog
            domain = article.get('blog', '')
            if any(established in domain for established in ['ghost.org', 'troyhunt.com', 'kentcdodds.com']):
                base_score += 3
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for Ghost blog content 