"""Stack Overflow scraper for technical questions and answers."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging

logger = logging.getLogger(__name__)

class StackOverflowScraper(WebBasedScraper):
    """Scraper for Stack Overflow questions"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = 'https://stackoverflow.com'
        self.config = config or {}
        self.tags = self.config.get('tags', ['python', 'javascript', 'java', 'c#', 'php'])
        self.max_per_tag = self.config.get('max_per_tag', 10)
    
    def scrape_questions(self, tag: str = None, page: int = 1) -> List[Dict[str, Any]]:
        """Scrape questions from Stack Overflow"""
        try:
            if tag:
                url = f"{self.base_url}/questions/tagged/{tag}?page={page}"
            else:
                url = f"{self.base_url}/questions?page={page}"
            
            soup = self.get_soup(url)
            questions = []
            
            # Find question containers
            question_containers = soup.find_all('div', class_='s-post-summary')
            
            for container in question_containers:
                try:
                    # Get title and link
                    title_elem = container.find('h3').find('a')
                    title = title_elem.get_text(strip=True)
                    link = self.base_url + title_elem.get('href', '')
                    
                    # Get stats
                    stats_elem = container.find('div', class_='s-post-summary--stats')
                    votes = stats_elem.find('span', {'title': re.compile('vote')})
                    votes_count = votes.get_text(strip=True) if votes else '0'
                    
                    answers = stats_elem.find('span', {'title': re.compile('answer')})
                    answers_count = answers.get_text(strip=True) if answers else '0'
                    
                    views = stats_elem.find('span', {'title': re.compile('view')})
                    views_count = views.get_text(strip=True) if views else '0'
                    
                    # Get tags
                    tags_container = container.find('div', class_='s-post-summary--meta-tags')
                    tags = []
                    if tags_container:
                        tag_elements = tags_container.find_all('a', class_='post-tag')
                        tags = [tag.get_text(strip=True) for tag in tag_elements]
                    
                    # Get excerpt
                    excerpt_elem = container.find('div', class_='s-post-summary--content-excerpt')
                    excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ''
                    
                    # Add credibility info
                    credibility_score = self._calculate_credibility(votes_count, answers_count, views_count)
                    
                    question = {
                        'title': title,
                        'link': link,
                        'votes': votes_count,
                        'answers': answers_count,
                        'views': views_count,
                        'tags': tags,
                        'excerpt': excerpt,
                        'source': 'Stack Overflow',
                        'source_detail': f"Stack Overflow - {tag}" if tag else "Stack Overflow",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Q&A',
                            'bias': 'technical'
                        },
                        'metadata': {
                            'votes': votes_count,
                            'answers': answers_count,
                            'views': views_count,
                            'tags': tags
                        },
                        'scraped_at': time.time()
                    }
                    questions.append(question)
                    
                except Exception as e:
                    logger.error(f"Error parsing SO question: {e}")
                    continue
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to scrape Stack Overflow: {e}")
            return []
    
    def _calculate_credibility(self, votes: str, answers: str, views: str) -> float:
        """Calculate credibility score based on engagement metrics"""
        try:
            votes = int(str(votes).replace(',', ''))
            answers = int(str(answers).replace(',', ''))
            views = int(str(views).replace(',', '').replace('k', '000'))
            
            # Base score from 0-100
            base_score = min(85 + (votes * 0.5 + answers * 2) / 100, 95)
            
            # Adjust based on views
            view_factor = min(views / 1000, 5) / 5  # Max boost of 5 points from views
            
            return round(base_score + (view_factor * 5), 1)
        except:
            return 85.0  # Default score for SO content
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape popular questions from multiple tags"""
        all_questions = []
        
        for tag in self.tags:
            questions = self.scrape_questions(tag, page=1)
            all_questions.extend(questions[:self.max_per_tag])
            
        return all_questions 