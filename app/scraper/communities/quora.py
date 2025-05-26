"""Quora scraper for Q&A content and discussions."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class QuoraScraper(WebBasedScraper):
    """Scraper for Quora content using hybrid approach (API + browser)"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        self.topics = self.config.get('topics', [
            'Programming',
            'Software-Engineering',
            'Web-Development',
            'Technology',
            'Startups'
        ])
        self.max_questions = self.config.get('max_questions', 10)
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup(self):
        """Setup browser for scraping"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            )
            self.page = await self.context.new_page()
            
            # Handle login wall
            await self.page.route("**/*", lambda route: route.continue_() if not route.request.resource_type == "image" else route.abort())
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            raise
    
    async def close(self):
        """Cleanup browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape questions and answers from Quora"""
        try:
            await self.setup()
            all_questions = []
            
            for topic in self.topics:
                try:
                    # Navigate to topic page
                    url = f"https://www.quora.com/topic/{topic}"
                    await self.page.goto(url, wait_until='networkidle')
                    
                    # Get questions
                    questions = await self.page.query_selector_all('div[class*="q-box"]')
                    
                    for question in questions[:self.max_questions]:
                        try:
                            # Extract question data
                            title_elem = await question.query_selector('span[class*="q-text"]')
                            title = await title_elem.text_content() if title_elem else ''
                            
                            # Get link
                            link_elem = await question.query_selector('a[class*="q-box"]')
                            link = await link_elem.get_attribute('href') if link_elem else ''
                            if link and not link.startswith('http'):
                                link = f"https://www.quora.com{link}"
                            
                            # Get answer preview
                            answer_elem = await question.query_selector('div[class*="q-text"]')
                            answer = await answer_elem.text_content() if answer_elem else ''
                            
                            # Get engagement metrics
                            upvotes_elem = await question.query_selector('div[class*="q-upvotes"]')
                            upvotes = await upvotes_elem.text_content() if upvotes_elem else '0'
                            
                            comments_elem = await question.query_selector('div[class*="q-comments"]')
                            comments = await comments_elem.text_content() if comments_elem else '0'
                            
                            # Get author if available
                            author_elem = await question.query_selector('a[class*="q-user"]')
                            author = await author_elem.text_content() if author_elem else ''
                            
                            # Calculate credibility
                            credibility_score = self._calculate_credibility(upvotes, comments)
                            
                            question_data = {
                                'title': title,
                                'link': link,
                                'answer_preview': answer,
                                'author': author,
                                'topic': topic,
                                'source': 'Quora',
                                'source_detail': f"Quora - {topic}",
                                'credibility_info': {
                                    'score': credibility_score,
                                    'category': 'Q&A',
                                    'bias': 'expert-community'
                                },
                                'metadata': {
                                    'upvotes': upvotes,
                                    'comments': comments,
                                    'topic': topic,
                                    'author': author
                                },
                                'scraped_at': time.time()
                            }
                            
                            all_questions.append(question_data)
                            
                        except Exception as e:
                            logger.error(f"Error processing Quora question: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error scraping Quora topic {topic}: {e}")
                    continue
            
            return all_questions
            
        except Exception as e:
            logger.error(f"Failed to scrape Quora: {e}")
            return []
        finally:
            await self.close()
    
    def _calculate_credibility(self, upvotes: str, comments: str) -> float:
        """Calculate credibility score based on engagement metrics"""
        try:
            # Convert metrics to numbers
            upvotes = int(re.sub(r'[^\d]', '', str(upvotes)) or 0)
            comments = int(re.sub(r'[^\d]', '', str(comments)) or 0)
            
            # Base score 85-95
            base_score = 85.0
            
            # Factors that increase credibility:
            # 1. High number of upvotes
            upvote_factor = min(upvotes / 100, 5)  # Up to 5 points
            base_score += upvote_factor
            
            # 2. High engagement (comments)
            comment_factor = min(comments / 10, 5)  # Up to 5 points
            base_score += comment_factor
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for Quora content 