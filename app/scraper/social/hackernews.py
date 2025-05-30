"""Hacker News scraper for real-time tech community content."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
from ..base import WebBasedScraper
import logging

class HackerNewsScraper(WebBasedScraper):
    """Real Hacker News scraper using their API."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Hacker News scraper."""
        super().__init__(config)
        self.source_name = "Hacker News"
        self.credibility_base = 85.0  # Community-driven content
        self.max_stories = self.config.get('max_stories', 20)
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        
    async def scrape(self, query: str = None) -> List[Dict[str, Any]]:
        """Scrape Hacker News top stories."""
        await self.setup()
        results = []
        
        try:
            # Get top story IDs
            async with self.session.get(f"{self.base_url}/topstories.json") as response:
                if response.status == 200:
                    story_ids = await response.json()
                    
                    # Fetch details for each story
                    for story_id in story_ids[:self.max_stories]:
                        story_data = await self._fetch_story(story_id)
                        if story_data:
                            # Filter by query if provided
                            if not query or self._matches_query(story_data, query):
                                results.append(story_data)
                                
        except Exception as e:
            logging.error(f"Error scraping Hacker News: {e}")
            
        return results
        
    async def _fetch_story(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Fetch individual story details."""
        try:
            await self._rate_limit()
            
            async with self.session.get(f"{self.base_url}/item/{story_id}.json") as response:
                if response.status == 200:
                    story = await response.json()
                    
                    # Skip if not a story or no title
                    if story.get('type') != 'story' or not story.get('title'):
                        return None
                        
                    title = story.get('title', '')
                    url = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                    text = story.get('text', '')
                    score = story.get('score', 0)
                    timestamp = story.get('time', 0)
                    author = story.get('by', '')
                    
                    # Calculate credibility based on score and community engagement
                    credibility_score = self._calculate_story_credibility(score, story.get('descendants', 0))
                    
                    return {
                        'title': title,
                        'link': url,
                        'content': text[:200] + '...' if text else '',
                        'published': datetime.fromtimestamp(timestamp).isoformat(),
                        'author': author,
                        'source': self.source_name,
                        'source_type': 'tech_community',
                        'source_detail': f"{self.source_name} - Community",
                        'score': score,
                        'comments': story.get('descendants', 0),
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Tech Community',
                            'bias': 'tech-focused'
                        },
                        'metadata': {
                            'source': 'news.ycombinator.com',
                            'source_name': self.source_name,
                            'platform': 'Tech Community',
                            'published_date': datetime.fromtimestamp(timestamp).isoformat(),
                            'author': author,
                            'story_id': story_id,
                            'upvotes': score,
                            'comment_count': story.get('descendants', 0),
                            'content_type': 'community_post'
                        },
                        'scraped_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logging.error(f"Error fetching story {story_id}: {e}")
            return None
            
    def _calculate_story_credibility(self, score: int, comments: int) -> float:
        """Calculate credibility based on community engagement."""
        try:
            base_score = self.credibility_base
            
            # Higher score = higher credibility
            if score > 100:
                base_score += 5
            elif score > 50:
                base_score += 3
            elif score > 20:
                base_score += 1
                
            # More comments = more engagement
            if comments > 50:
                base_score += 3
            elif comments > 20:
                base_score += 2
            elif comments > 10:
                base_score += 1
                
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return self.credibility_base
            
    def _matches_query(self, story: Dict[str, Any], query: str) -> bool:
        """Check if story matches the query."""
        query_lower = query.lower()
        searchable_text = f"{story.get('title', '')} {story.get('content', '')}".lower()
        return query_lower in searchable_text 