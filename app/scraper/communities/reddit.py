"""Reddit scraper for community discussions and content."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import praw

logger = logging.getLogger(__name__)

class RedditScraper(WebBasedScraper):
    """Scraper for Reddit content"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        self.subreddits = self.config.get('subreddits', [
            'programming',
            'technology',
            'webdev',
            'Python',
            'javascript'
        ])
        self.max_posts = self.config.get('max_posts', 10)
        self.time_filter = self.config.get('time_filter', 'week')
        self.sort_by = self.config.get('sort_by', 'hot')
        
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=self.config.get('client_id'),
            client_secret=self.config.get('client_secret'),
            user_agent=self.config.get('user_agent', 'Factryl Scraper v1.0')
        )
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape posts from specified subreddits"""
        all_posts = []
        
        for subreddit_name in self.subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get posts based on sort method
                if self.sort_by == 'hot':
                    posts = subreddit.hot(limit=self.max_posts)
                elif self.sort_by == 'top':
                    posts = subreddit.top(time_filter=self.time_filter, limit=self.max_posts)
                else:
                    posts = subreddit.new(limit=self.max_posts)
                
                for post in posts:
                    try:
                        # Calculate credibility
                        credibility_score = self._calculate_credibility(post)
                        
                        post_data = {
                            'title': post.title,
                            'link': f"https://reddit.com{post.permalink}",
                            'author': str(post.author) if post.author else '[deleted]',
                            'content': post.selftext,
                            'subreddit': post.subreddit.display_name,
                            'source': 'Reddit',
                            'source_detail': f"Reddit - r/{post.subreddit.display_name}",
                            'credibility_info': {
                                'score': credibility_score,
                                'category': 'Community Discussion',
                                'bias': 'community-voted'
                            },
                            'metadata': {
                                'score': post.score,
                                'upvote_ratio': post.upvote_ratio,
                                'num_comments': post.num_comments,
                                'is_original_content': post.is_original_content,
                                'created_utc': post.created_utc
                            },
                            'scraped_at': time.time()
                        }
                        
                        # Add flair if available
                        if hasattr(post, 'link_flair_text') and post.link_flair_text:
                            post_data['metadata']['flair'] = post.link_flair_text
                        
                        all_posts.append(post_data)
                        
                    except Exception as e:
                        logger.error(f"Error processing Reddit post: {e}")
                        continue
                    
            except Exception as e:
                logger.error(f"Error scraping subreddit {subreddit_name}: {e}")
                continue
        
        return all_posts
    
    def _calculate_credibility(self, post) -> float:
        """Calculate credibility score based on Reddit metrics"""
        try:
            # Base score 85-95
            base_score = 85.0
            
            # Factors that increase credibility:
            # 1. High upvote ratio (>0.8)
            if post.upvote_ratio > 0.8:
                base_score += 2
            
            # 2. High number of comments (engagement)
            comment_factor = min(post.num_comments / 100, 3)  # Up to 3 points
            base_score += comment_factor
            
            # 3. High score (upvotes - downvotes)
            score_factor = min(post.score / 1000, 3)  # Up to 3 points
            base_score += score_factor
            
            # 4. Original content
            if post.is_original_content:
                base_score += 2
            
            return min(base_score, 95.0)  # Cap at 95
            
        except:
            return 85.0  # Default score for Reddit content 