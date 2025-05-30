"""TikTok scraper for trending content and hashtags."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import urllib.parse
import re
import json
from bs4 import BeautifulSoup
from ..base import WebBasedScraper

class TikTokScraper(WebBasedScraper):
    """TikTok scraper for public content and hashtags."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize TikTok scraper."""
        super().__init__(config)
        self.source_name = "TikTok"
        self.credibility_base = 62.0  # Social media baseline
        self.base_url = "https://www.tiktok.com"
        self.max_entries = self.config.get('max_entries', 20)
        
    async def search_hashtags(self, query: str) -> List[Dict[str, Any]]:
        """Search TikTok hashtags for content."""
        try:
            await self.setup()
            
            # Convert query to hashtag format
            hashtag = re.sub(r'\s+', '', query.lower())
            hashtag_url = f"{self.base_url}/tag/{hashtag}"
            
            await self._rate_limit()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Referer': 'https://www.tiktok.com/',
                'Upgrade-Insecure-Requests': '1'
            }
            
            async with self.session.get(hashtag_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract JSON data from TikTok's page
                    results = []
                    
                    # Look for JSON data in script tags
                    soup = BeautifulSoup(html, 'html.parser')
                    script_tags = soup.find_all('script', type='application/json')
                    
                    for script in script_tags:
                        try:
                            script_content = script.get_text()
                            if script_content:
                                data = json.loads(script_content)
                                
                                # Navigate through TikTok's data structure
                                if 'props' in data and 'pageProps' in data['props']:
                                    page_props = data['props']['pageProps']
                                    
                                    # Look for video data
                                    if 'videoData' in page_props:
                                        video_data = page_props['videoData']
                                        if isinstance(video_data, list):
                                            videos = video_data
                                        else:
                                            videos = [video_data]
                                        
                                        for video in videos[:self.max_entries]:
                                            if isinstance(video, dict):
                                                video_id = video.get('id', '')
                                                desc = video.get('desc', '')
                                                author = video.get('author', {})
                                                username = author.get('uniqueId', '') if author else ''
                                                
                                                stats = video.get('stats', {})
                                                like_count = stats.get('diggCount', 0)
                                                comment_count = stats.get('commentCount', 0)
                                                share_count = stats.get('shareCount', 0)
                                                play_count = stats.get('playCount', 0)
                                                
                                                create_time = video.get('createTime', 0)
                                                published_date = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d') if create_time else datetime.now().strftime('%Y-%m-%d')
                                                
                                                if video_id:
                                                    video_url = f"{self.base_url}/@{username}/video/{video_id}" if username else f"{self.base_url}/video/{video_id}"
                                                    
                                                    result = {
                                                        'title': f"TikTok: {desc[:100]}..." if len(desc) > 100 else f"TikTok: {desc}",
                                                        'link': video_url,
                                                        'content': desc,
                                                        'published': published_date,
                                                        'source': 'tiktok.com',
                                                        'source_type': 'social_media',
                                                        'source_detail': f"TikTok Video via {self.source_name}",
                                                        'credibility_info': {
                                                            'score': self._calculate_viral_credibility(like_count, comment_count, play_count),
                                                            'category': 'Social Media Video',
                                                            'bias': 'user_generated'
                                                        },
                                                        'metadata': {
                                                            'source': 'tiktok.com',
                                                            'source_name': 'TikTok',
                                                            'platform': 'TikTok',
                                                            'content_type': 'video',
                                                            'hashtag': hashtag,
                                                            'author': username,
                                                            'likes': like_count,
                                                            'comments': comment_count,
                                                            'shares': share_count,
                                                            'plays': play_count,
                                                            'video_id': video_id,
                                                            'engagement_score': like_count + comment_count + share_count,
                                                            'viral_score': play_count
                                                        },
                                                        'scraped_at': datetime.now().isoformat()
                                                    }
                                                    
                                                    results.append(result)
                                                    
                        except Exception as e:
                            logging.error(f"Error parsing TikTok JSON: {e}")
                            continue
                    
                    # Fallback: Basic HTML parsing if JSON fails
                    if not results:
                        results = await self._parse_html_fallback(soup, hashtag, query)
                    
                    return results
                    
        except Exception as e:
            logging.error(f"Error searching TikTok: {e}")
            
        return []
    
    async def _parse_html_fallback(self, soup: BeautifulSoup, hashtag: str, query: str) -> List[Dict[str, Any]]:
        """Fallback HTML parsing when JSON extraction fails."""
        results = []
        
        try:
            # Look for meta tags and basic content
            meta_description = soup.find('meta', attrs={'name': 'description'})
            og_description = soup.find('meta', attrs={'property': 'og:description'})
            
            description = ""
            if meta_description:
                description = meta_description.get('content', '')
            elif og_description:
                description = og_description.get('content', '')
            
            if description:
                # Create a basic result from meta information
                result = {
                    'title': f"TikTok #{hashtag} Content",
                    'link': f"{self.base_url}/tag/{hashtag}",
                    'content': description,
                    'published': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'tiktok.com',
                    'source_type': 'social_media',
                    'source_detail': f"TikTok Hashtag via {self.source_name}",
                    'credibility_info': {
                        'score': self.credibility_base,
                        'category': 'Social Media Hashtag',
                        'bias': 'user_generated'
                    },
                    'metadata': {
                        'source': 'tiktok.com',
                        'source_name': 'TikTok',
                        'platform': 'TikTok',
                        'content_type': 'hashtag_page',
                        'hashtag': hashtag,
                        'search_query': query,
                        'parsing_method': 'html_fallback'
                    },
                    'scraped_at': datetime.now().isoformat()
                }
                
                results.append(result)
        
        except Exception as e:
            logging.error(f"Error in TikTok HTML fallback parsing: {e}")
        
        return results
    
    async def search_trending(self) -> List[Dict[str, Any]]:
        """Get trending TikTok content."""
        try:
            await self.setup()
            
            trending_url = f"{self.base_url}/trending"
            
            await self._rate_limit()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.tiktok.com/'
            }
            
            async with self.session.get(trending_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Create a trending summary result
                    result = {
                        'title': 'TikTok Trending Content',
                        'link': trending_url,
                        'content': 'Latest trending videos and hashtags on TikTok',
                        'published': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'tiktok.com',
                        'source_type': 'social_media',
                        'source_detail': f"TikTok Trending via {self.source_name}",
                        'credibility_info': {
                            'score': self.credibility_base + 10,  # Trending content bonus
                            'category': 'Trending Social Media',
                            'bias': 'algorithmic'
                        },
                        'metadata': {
                            'source': 'tiktok.com',
                            'source_name': 'TikTok',
                            'platform': 'TikTok',
                            'content_type': 'trending_page',
                            'is_trending': True
                        },
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    return [result]
                    
        except Exception as e:
            logging.error(f"Error getting TikTok trending: {e}")
            
        return []
    
    def _calculate_viral_credibility(self, likes: int, comments: int, plays: int) -> float:
        """Calculate credibility based on viral metrics."""
        base_score = self.credibility_base
        
        # Viral engagement scoring
        total_engagement = likes + comments
        
        # High viral content gets credibility boost
        if plays > 1000000:  # 1M+ views
            base_score += 20
        elif plays > 100000:  # 100K+ views
            base_score += 15
        elif plays > 10000:   # 10K+ views
            base_score += 10
        
        # Engagement ratio (engagement vs views)
        if plays > 0:
            engagement_ratio = total_engagement / plays
            if engagement_ratio > 0.05:  # 5%+ engagement rate
                base_score += 10
            elif engagement_ratio > 0.02:  # 2%+ engagement rate
                base_score += 5
        
        # Comment to like ratio
        if likes > 0:
            comment_ratio = comments / likes
            if 0.01 <= comment_ratio <= 0.3:  # Healthy discussion
                base_score += 5
        
        return min(base_score, 100.0)
    
    async def scrape(self, query: str = None) -> List[Dict[str, Any]]:
        """Main scraping method for TikTok."""
        if not query:
            # Return trending content if no specific query
            return await self.search_trending()
        
        return await self.search_hashtags(query) 