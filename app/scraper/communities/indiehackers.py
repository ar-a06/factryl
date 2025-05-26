"""IndieHackers scraper for entrepreneurial discussions and experiences."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging

logger = logging.getLogger(__name__)

class IndieHackersScraper(WebBasedScraper):
    """Scraper for IndieHackers posts"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = 'https://www.indiehackers.com'
        self.config = config or {}
        self.max_results = self.config.get('max_results', 20)
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape recent posts from IndieHackers"""
        try:
            url = f"{self.base_url}/posts"
            soup = self.get_soup(url)
            posts = []
            
            # Find post containers
            post_containers = soup.find_all('div', class_='feed-item') or soup.find_all('article')
            
            for container in post_containers[:self.max_results]:
                try:
                    # Get title
                    title_elem = container.find('h2') or container.find('h3') or container.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    # Get link
                    link_elem = container.find('a')
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = self.base_url + link
                    
                    # Get author
                    author_elem = container.find(class_=lambda x: x and 'author' in x.lower())
                    author = author_elem.get_text(strip=True) if author_elem else ''
                    
                    # Get engagement metrics
                    comments_elem = container.find(text=re.compile(r'\d+.*comment'))
                    comments = comments_elem.strip() if comments_elem else '0'
                    
                    # Get content preview
                    preview_elem = container.find('div', class_=lambda x: x and 'content' in x.lower())
                    preview = preview_elem.get_text(strip=True) if preview_elem else ''
                    
                    # Get topics/tags if available
                    topics = []
                    topics_container = container.find('div', class_=lambda x: x and 'topics' in x.lower())
                    if topics_container:
                        topic_elements = topics_container.find_all('a')
                        topics = [topic.get_text(strip=True) for topic in topic_elements]
                    
                    # Calculate credibility
                    credibility_score = self._calculate_credibility(comments)
                    
                    post = {
                        'title': title,
                        'link': link,
                        'author': author,
                        'preview': preview,
                        'topics': topics,
                        'source': 'IndieHackers',
                        'source_detail': 'IndieHackers - Community',
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Community Discussion',
                            'bias': 'indie-focused'
                        },
                        'metadata': {
                            'author': author,
                            'comments': comments,
                            'topics': topics
                        },
                        'scraped_at': time.time()
                    }
                    posts.append(post)
                    
                except Exception as e:
                    logger.error(f"Error parsing IH post: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            logger.error(f"Failed to scrape IndieHackers: {e}")
            return []
    
    def _calculate_credibility(self, comments: str) -> float:
        """Calculate credibility score based on community engagement"""
        try:
            # Extract number from comments string (e.g., "5 comments" -> 5)
            comments_count = int(re.search(r'\d+', str(comments)).group())
            
            # Base score 85-95 based on community engagement
            # More comments indicate higher community interest and validation
            base_score = 85 + min((comments_count / 5), 10)  # Up to 10 points for comments
            return min(base_score, 95)
        except:
            return 85.0  # Default score for IH content 