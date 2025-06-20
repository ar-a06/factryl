"""Reddit scraper for community discussions and content."""

from ..base import WebBasedScraper
from typing import List, Dict, Any, Optional
import re
import time
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from urllib.parse import quote

logger = logging.getLogger(__name__)

class RedditScraper(WebBasedScraper):
    """Scraper for Reddit content using public JSON API"""
    
    def __init__(self, search_query: str = None, subreddits: List[str] = None, max_posts: int = 15):
        """
        Initialize Reddit scraper with dynamic parameters
        
        Args:
            search_query (str): Search keyword from website's search box
            subreddits (List[str]): List of subreddits to search in. If None, searches across all subreddits
            max_posts (int): Maximum number of posts to return
        """
        super().__init__({})
        self.search_query = search_query
        self.subreddits = subreddits
        self.max_posts = max_posts
        self.session = None

    async def _init_session(self):
        """Initialize aiohttp session"""
        if self.session is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Cache-Control': 'no-cache'
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def _search_reddit(self, query: str, subreddit: str = None) -> List[Dict]:
        """
        Search Reddit posts either in specific subreddit or across all of Reddit
        
        Args:
            query (str): Search keyword
            subreddit (str, optional): Specific subreddit to search in
        """
        try:
            if not self.session:
                await self._init_session()
            
            encoded_query = quote(query)
            search_posts = []
            
            # Search URL construction
            base_url = "https://www.reddit.com"
            if subreddit:
                search_url = f"{base_url}/r/{subreddit}/search.json"
                restrict_sr = "1"  # Restrict to subreddit
                logger.info(f"Searching in subreddit: r/{subreddit}")
            else:
                search_url = f"{base_url}/search.json"
                restrict_sr = "0"  # Search all of Reddit
                logger.info("Searching across all of Reddit")
            
            # Different sort options for comprehensive results
            sort_options = ['relevance', 'hot', 'top', 'new']
            
            for sort in sort_options:
                if len(search_posts) >= self.max_posts:
                    logger.info(f"Reached max posts limit ({self.max_posts})")
                    break
                
                params = {
                    'q': encoded_query,
                    'restrict_sr': restrict_sr,
                    'sort': sort,
                    'limit': self.max_posts,
                    't': 'all',  # Include results from all time
                    'raw_json': '1'  # Get raw JSON response
                }
                
                url = f"{search_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
                logger.info(f"Making request to: {url}")
                
                try:
                    # Add delay between requests to respect rate limits
                    await asyncio.sleep(2)  # Increased delay to avoid rate limiting
                    
                    async with self.session.get(url, timeout=30) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            try:
                                data = json.loads(response_text)
                                posts = data.get('data', {}).get('children', [])
                                source = f"r/{subreddit}" if subreddit else "Reddit (All)"
                                logger.info(f"Found {len(posts)} posts in {source} for query '{query}' sorted by {sort}")
                                
                                if not posts:
                                    logger.warning(f"No posts found for sort option: {sort}")
                                else:
                                    search_posts.extend(posts)
                                    
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON response: {e}")
                                logger.error(f"Response text: {response_text[:200]}...")
                                
                        elif response.status == 429:  # Too Many Requests
                            logger.warning("Rate limited by Reddit. Waiting longer between requests...")
                            await asyncio.sleep(5)  # Wait longer before next request
                            continue
                        else:
                            logger.warning(f"Error searching Reddit: Status {response.status}")
                            logger.warning(f"Response: {response_text[:200]}...")
                            
                except asyncio.TimeoutError:
                    logger.error("Request timed out")
                    continue
                except Exception as e:
                    logger.error(f"Error during Reddit search request: {e}")
                    continue
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_posts = []
            for post in search_posts:
                post_id = post.get('data', {}).get('id')
                if post_id and post_id not in seen_ids:
                    seen_ids.add(post_id)
                    unique_posts.append(post)
            
            logger.info(f"Found {len(unique_posts)} unique posts after deduplication")
            return unique_posts[:self.max_posts]
            
        except Exception as e:
            logger.error(f"Error in _search_reddit: {e}")
            return []

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Reddit posts based on search query"""
        if not self.search_query:
            logger.warning("No search query provided")
            return []
            
        all_posts = []
        logger.info(f"Starting Reddit search for query: {self.search_query}")
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # If specific subreddits are provided, search in each one
            if self.subreddits:
                tasks = [self._search_reddit(self.search_query, subreddit) 
                        for subreddit in self.subreddits]
                logger.info(f"Searching in specific subreddits: {', '.join(self.subreddits)}")
            else:
                # Search across all of Reddit
                tasks = [self._search_reddit(self.search_query)]
                logger.info("Searching across all of Reddit")
            
            search_results = loop.run_until_complete(asyncio.gather(*tasks))
            logger.info(f"Received {len(search_results)} result sets")
            
            # Process results
            for result_set in search_results:
                logger.info(f"Processing result set with {len(result_set)} posts")
                for post in result_set:
                    try:
                        post_data = post.get('data', {})
                        
                        # Skip unwanted posts
                        if (post_data.get('stickied', False) or 
                            post_data.get('removed', False) or 
                            post_data.get('deleted', False) or
                            not post_data.get('title')):
                            logger.debug(f"Skipping post: {post_data.get('title', 'No title')} (unwanted post type)")
                            continue
                        
                        # Calculate credibility
                        credibility_score = self._calculate_credibility(post_data)
                        
                        processed_post = {
                            'title': post_data.get('title', ''),
                            'link': f"https://reddit.com{post_data.get('permalink', '')}",
                            'author': post_data.get('author', '[deleted]'),
                            'content': post_data.get('selftext', '')[:500] + '...' if len(post_data.get('selftext', '')) > 500 else post_data.get('selftext', ''),
                            'subreddit': post_data.get('subreddit', ''),
                            'source': 'Reddit',
                            'source_detail': f"Reddit - r/{post_data.get('subreddit', '')}",
                            'credibility_info': {
                                'score': credibility_score,
                                'category': 'Community Discussion',
                                'bias': 'community-voted'
                            },
                            'metadata': {
                                'score': post_data.get('score', 0),
                                'upvote_ratio': post_data.get('upvote_ratio', 1.0),
                                'num_comments': post_data.get('num_comments', 0),
                                'is_original_content': post_data.get('is_original_content', False),
                                'created_utc': post_data.get('created_utc', time.time())
                            },
                            'scraped_at': time.time()
                        }
                        
                        # Add flair if available
                        if post_data.get('link_flair_text'):
                            processed_post['metadata']['flair'] = post_data['link_flair_text']
                        
                        # Add URL if it's a link post
                        if post_data.get('url'):
                            processed_post['metadata']['external_url'] = post_data['url']
                        
                        all_posts.append(processed_post)
                        logger.info(f"Added post: {processed_post['title'][:50]}...")
                        
                    except Exception as e:
                        logger.error(f"Error processing Reddit post: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Error in Reddit scraping: {e}")
        finally:
            # Clean up
            if self.session:
                loop.run_until_complete(self.session.close())
            loop.close()
        
        logger.info(f"Total posts found: {len(all_posts)}")
        return all_posts
        
    def _calculate_credibility(self, post_data: Dict) -> float:
        """Calculate credibility score based on Reddit metrics"""
        try:
            # Base score 85-95
            base_score = 85.0
            
            # Factors that increase credibility:
            # 1. High upvote ratio (>0.8)
            if post_data.get('upvote_ratio', 0) > 0.8:
                base_score += 2
            
            # 2. High number of comments (engagement)
            comment_factor = min(post_data.get('num_comments', 0) / 100, 3)  # Up to 3 points
            base_score += comment_factor
            
            # 3. High score (upvotes - downvotes)
            score_factor = min(post_data.get('score', 0) / 1000, 3)  # Up to 3 points
            base_score += score_factor
            
            # 4. Original content
            if post_data.get('is_original_content', False):
                base_score += 2
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for Reddit content 