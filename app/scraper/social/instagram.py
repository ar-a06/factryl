"""Instagram scraper for trending content and hashtags."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging
import urllib.parse
import re
import json
from bs4 import BeautifulSoup
from ..base import WebBasedScraper

class InstagramScraper(WebBasedScraper):
    """Instagram scraper for public content and hashtags."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Instagram scraper."""
        super().__init__(config)
        self.source_name = "Instagram"
        self.credibility_base = 65.0  # Social media baseline
        self.base_url = "https://www.instagram.com"
        self.max_entries = self.config.get('max_entries', 20)
        
    async def search_hashtags(self, query: str) -> List[Dict[str, Any]]:
        """Search Instagram hashtags for content."""
        try:
            await self.setup()
            
            # Convert query to hashtag format
            hashtag = re.sub(r'\s+', '', query.lower())
            hashtag_url = f"{self.base_url}/explore/tags/{hashtag}/"
            
            await self._rate_limit()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            async with self.session.get(hashtag_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract JSON data from Instagram's page
                    results = []
                    
                    # Look for JSON data in script tags
                    soup = BeautifulSoup(html, 'html.parser')
                    script_tags = soup.find_all('script', type='text/javascript')
                    
                    for script in script_tags:
                        script_content = script.get_text()
                        if 'window._sharedData' in script_content:
                            try:
                                # Extract shared data
                                json_start = script_content.find('{')
                                json_end = script_content.rfind('}') + 1
                                if json_start != -1 and json_end != -1:
                                    shared_data = json.loads(script_content[json_start:json_end])
                                    
                                    # Navigate to hashtag data
                                    entry_data = shared_data.get('entry_data', {})
                                    tag_page = entry_data.get('TagPage', [])
                                    
                                    if tag_page:
                                        hashtag_data = tag_page[0].get('graphql', {}).get('hashtag', {})
                                        edge_hashtag_media = hashtag_data.get('edge_hashtag_to_media', {})
                                        edges = edge_hashtag_media.get('edges', [])
                                        
                                        for edge in edges[:self.max_entries]:
                                            node = edge.get('node', {})
                                            
                                            post_id = node.get('id', '')
                                            shortcode = node.get('shortcode', '')
                                            caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
                                            caption = caption_edges[0].get('node', {}).get('text', '') if caption_edges else ''
                                            
                                            like_count = node.get('edge_liked_by', {}).get('count', 0)
                                            comment_count = node.get('edge_media_to_comment', {}).get('count', 0)
                                            
                                            media_url = node.get('display_url', '')
                                            is_video = node.get('is_video', False)
                                            
                                            timestamp = node.get('taken_at_timestamp', 0)
                                            published_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d') if timestamp else datetime.now().strftime('%Y-%m-%d')
                                            
                                            if shortcode:
                                                post_url = f"{self.base_url}/p/{shortcode}/"
                                                
                                                result = {
                                                    'title': f"Instagram Post about #{hashtag}",
                                                    'link': post_url,
                                                    'content': caption[:500] + '...' if len(caption) > 500 else caption,
                                                    'published': published_date,
                                                    'source': 'instagram.com',
                                                    'source_type': 'social_media',
                                                    'source_detail': f"Instagram Post via {self.source_name}",
                                                    'credibility_info': {
                                                        'score': self._calculate_social_credibility(like_count, comment_count),
                                                        'category': 'Social Media',
                                                        'bias': 'user_generated'
                                                    },
                                                    'metadata': {
                                                        'source': 'instagram.com',
                                                        'source_name': 'Instagram',
                                                        'platform': 'Instagram',
                                                        'content_type': 'video' if is_video else 'image',
                                                        'hashtag': hashtag,
                                                        'likes': like_count,
                                                        'comments': comment_count,
                                                        'media_url': media_url,
                                                        'post_id': post_id,
                                                        'engagement_score': like_count + comment_count
                                                    },
                                                    'scraped_at': datetime.now().isoformat()
                                                }
                                                
                                                results.append(result)
                                                
                            except Exception as e:
                                logging.error(f"Error parsing Instagram JSON: {e}")
                                continue
                    
                    # Fallback: Basic HTML parsing if JSON fails
                    if not results:
                        results = await self._parse_html_fallback(soup, hashtag, query)
                    
                    return results
                    
        except Exception as e:
            logging.error(f"Error searching Instagram: {e}")
            
        return []
    
    async def _parse_html_fallback(self, soup: BeautifulSoup, hashtag: str, query: str) -> List[Dict[str, Any]]:
        """Fallback HTML parsing when JSON extraction fails."""
        results = []
        
        try:
            # Look for meta tags and basic content
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                description = meta_description.get('content', '')
                
                # Create a basic result from meta information
                result = {
                    'title': f"Instagram #{hashtag} Content",
                    'link': f"{self.base_url}/explore/tags/{hashtag}/",
                    'content': description,
                    'published': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'instagram.com',
                    'source_type': 'social_media',
                    'source_detail': f"Instagram Hashtag via {self.source_name}",
                    'credibility_info': {
                        'score': self.credibility_base,
                        'category': 'Social Media Hashtag',
                        'bias': 'user_generated'
                    },
                    'metadata': {
                        'source': 'instagram.com',
                        'source_name': 'Instagram',
                        'platform': 'Instagram',
                        'content_type': 'hashtag_page',
                        'hashtag': hashtag,
                        'search_query': query,
                        'parsing_method': 'html_fallback'
                    },
                    'scraped_at': datetime.now().isoformat()
                }
                
                results.append(result)
        
        except Exception as e:
            logging.error(f"Error in HTML fallback parsing: {e}")
        
        return results
    
    def _calculate_social_credibility(self, likes: int, comments: int) -> float:
        """Calculate credibility based on engagement metrics."""
        base_score = self.credibility_base
        
        # Engagement-based scoring
        total_engagement = likes + comments
        
        if total_engagement > 10000:
            base_score += 15
        elif total_engagement > 1000:
            base_score += 10
        elif total_engagement > 100:
            base_score += 5
        
        # Comment to like ratio (indicates genuine engagement)
        if likes > 0:
            comment_ratio = comments / likes
            if 0.02 <= comment_ratio <= 0.15:  # Healthy engagement ratio
                base_score += 5
        
        return min(base_score, 100.0)
    
    async def scrape(self, query: str = None) -> List[Dict[str, Any]]:
        """Main scraping method for Instagram."""
        if not query:
            return []
        
        return await self.search_hashtags(query) 