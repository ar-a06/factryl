"""Podcast scraper for various podcast platforms and RSS feeds."""

from ..base import RSSBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class PodcastScraper(RSSBasedScraper):
    """Scraper for podcast platforms and RSS feeds"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Podcast sources configuration
        self.podcast_sources = self.config.get('sources', [
            {
                'name': 'This Week in Tech',
                'rss_url': 'https://feeds.twit.tv/twit.xml',
                'category': 'Technology',
                'credibility_base': 85
            },
            {
                'name': 'The Tim Ferriss Show',
                'rss_url': 'https://rss.art19.com/tim-ferriss-show',
                'category': 'Business',
                'credibility_base': 88
            },
            {
                'name': 'Lex Fridman Podcast',
                'rss_url': 'https://lexfridman.com/feed/podcast/',
                'category': 'AI/Tech',
                'credibility_base': 90
            },
            {
                'name': 'a16z Podcast',
                'rss_url': 'https://feeds.feedburner.com/venturedesk',
                'category': 'Venture Capital',
                'credibility_base': 87
            }
        ])
        
        self.max_episodes = self.config.get('max_episodes', 20)
        self.min_duration = self.config.get('min_duration_minutes', 10)
        self.search_fields = ['title', 'description', 'author']

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "podcasts"

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            # Test RSS parsing for first source
            if self.podcast_sources:
                test_url = self.podcast_sources[0]['rss_url']
                feed = feedparser.parse(test_url)
                return len(feed.entries) > 0
            return True
        except Exception as e:
            logger.error(f"Podcast scraper validation failed: {str(e)}")
            return False

    def _extract_duration(self, entry: Dict) -> int:
        """Extract episode duration in minutes."""
        try:
            # Try different duration formats
            duration_str = entry.get('itunes_duration', '') or entry.get('duration', '')
            if not duration_str:
                return 0
                
            # Parse HH:MM:SS or MM:SS format
            parts = duration_str.split(':')
            if len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 2:  # MM:SS
                return int(parts[0])
            else:  # Just minutes
                return int(duration_str) if duration_str.isdigit() else 0
        except:
            return 0

    def _extract_transcript_preview(self, description: str) -> str:
        """Extract a clean preview from podcast description."""
        if not description:
            return ""
            
        # Remove HTML tags
        soup = BeautifulSoup(description, 'html.parser')
        text = soup.get_text()
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Return first 300 characters
        return text[:300] + "..." if len(text) > 300 else text

    async def scrape_podcast_feed(self, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape individual podcast RSS feed."""
        try:
            rss_url = source_config['rss_url']
            name = source_config['name']
            category = source_config['category']
            
            feed = feedparser.parse(rss_url)
            episodes = []
            
            for entry in feed.entries[:self.max_episodes]:
                # Extract episode details
                title = entry.get('title', '')
                description = entry.get('description', '') or entry.get('summary', '')
                published = entry.get('published', '')
                author = entry.get('author', '') or feed.feed.get('title', name)
                link = entry.get('link', '')
                
                # Extract duration
                duration_minutes = self._extract_duration(entry)
                
                # Skip short episodes
                if duration_minutes < self.min_duration:
                    continue
                
                # Extract clean transcript preview
                transcript_preview = self._extract_transcript_preview(description)
                
                # Calculate credibility
                credibility_score = self._calculate_credibility({
                    'title': title,
                    'description': transcript_preview,
                    'author': author,
                    'source_name': name,
                    'category': category,
                    'duration': duration_minutes
                })
                
                episode = {
                    'title': title,
                    'link': link,
                    'description': transcript_preview,
                    'author': author,
                    'published': published,
                    'duration_minutes': duration_minutes,
                    'podcast_name': name,
                    'category': category,
                    'source': 'podcasts',
                    'source_name': name,
                    'type': 'Podcast Episode',
                    'source_detail': f"Podcast - {name}",
                    'credibility_info': {
                        'score': credibility_score,
                        'category': f'Podcast - {category}',
                        'bias': 'audio-content'
                    },
                    'metadata': {
                        'podcast': name,
                        'category': category,
                        'duration_minutes': duration_minutes,
                        'platform': 'Podcast',
                        'published_date': published,
                        'author': author,
                        'episode_type': 'audio'
                    },
                    'scraped_at': time.time()
                }
                episodes.append(episode)
            
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to scrape podcast feed {source_config['name']}: {e}")
            return []

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """Scrape podcast episodes matching the query."""
        logger.info(f"Scraping podcasts for: {query}")
        
        all_episodes = []
        
        for source_config in self.podcast_sources:
            episodes = await self.scrape_podcast_feed(source_config)
            
            # Filter episodes by query
            filtered_episodes = []
            query_lower = query.lower()
            
            for episode in episodes:
                # Check if query matches title, description, or author
                matches = (
                    query_lower in episode['title'].lower() or
                    query_lower in episode['description'].lower() or
                    query_lower in episode['author'].lower() or
                    query_lower in episode['category'].lower()
                )
                
                if matches:
                    filtered_episodes.append(episode)
            
            all_episodes.extend(filtered_episodes)
        
        # Sort by credibility and publish date
        sorted_episodes = sorted(
            all_episodes,
            key=lambda x: (x['credibility_info']['score'], x.get('published', '')),
            reverse=True
        )
        
        return sorted_episodes[:self.max_episodes] 