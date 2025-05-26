"""
Quora scraper module using optimized API approach.
"""

import asyncio
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, List, Any, Optional
from loguru import logger
import redis.asyncio as redis
import urllib.parse
import random
import aiohttp
import re

from .plugin_loader import BaseScraper, rate_limited

class QuoraScraper(BaseScraper):
    """Quora scraper implementation using API."""

    def __init__(self, config: dict):
        """Initialize the Quora scraper."""
        super().__init__(config)
        
        # Get cache settings from config
        cache_config = config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', False)
        self.redis_url = f"redis://{cache_config.get('host', 'localhost')}:{cache_config.get('port', 6379)}"
        self.redis = None
        
        # Get Quora-specific settings
        quora_config = config.get('quora', {})
        self.max_answers = quora_config.get('max_answers', 30)
        self.min_upvotes = quora_config.get('min_upvotes', 10)
        self.time_filter = quora_config.get('time_filter', 'week')
        self.min_credibility = quora_config.get('min_credibility', 70)
        self.max_retries = quora_config.get('max_retries', 5)
        self.retry_delay = quora_config.get('retry_delay', 2)
        
        # Initialize client
        self.http_client = None
        
        # API endpoints
        self.api_base = 'https://www.quora.com'
        self.search_endpoint = f"{self.api_base}/api/questions_and_answers"
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "quora"

    async def _init_http_client(self):
        """Initialize aiohttp client with optimized settings."""
        if self.http_client is None:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            
            # Common headers for Quora API requests
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': self.api_base,
                'Referer': f"{self.api_base}/search?q=test",
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            self.http_client = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )

    async def _init_cache(self):
        """Initialize Redis cache connection."""
        if self.cache_enabled and self.redis is None:
            try:
                self.redis = await redis.from_url(self.redis_url)
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.cache_enabled = False

    async def _get_cached_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get results from cache if available."""
        if not self.cache_enabled:
            return None
            
        try:
            cache_key = f"quora:{hashlib.md5(query.encode()).hexdigest()}"
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                if datetime.fromisoformat(data['timestamp']) > datetime.now() - timedelta(minutes=15):
                    return data['results']
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None

    async def _cache_results(self, query: str, results: List[Dict[str, Any]]):
        """Cache results for future use."""
        if not self.cache_enabled:
            return
            
        try:
            cache_key = f"quora:{hashlib.md5(query.encode()).hexdigest()}"
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            await self.redis.setex(cache_key, 900, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            await self._init_http_client()
            
            # Try a simple search request to validate
            params = {
                'query': 'test',
                'limit': 1,
                'timestamp': int(datetime.now().timestamp())
            }
            
            async with self.http_client.get(self.search_endpoint, params=params) as response:
                logger.debug(f"Validation response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Response data: {data}")
                    
                    # Check if we got any kind of valid response
                    if isinstance(data, dict) and not data.get('error'):
                        return True
                        
                    logger.error(f"Invalid response format: {data.get('error', 'Unknown error')}")
                    return False
                    
                logger.error(f"Validation failed with status {response.status}")
                response_text = await response.text()
                logger.error(f"Response text: {response_text[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Quora scraper validation failed: {str(e)}")
            return False

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape Quora answers matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing answer data
        """
        logger.info(f"Scraping Quora for: {query}")
        
        # Initialize cache
        await self._init_cache()
        
        # Check cache first
        cached_results = await self._get_cached_results(query)
        if cached_results:
            logger.info("Returning cached Quora results")
            return cached_results
            
        try:
            await self._init_http_client()
            
            # Search parameters
            params = {
                'query': query,
                'limit': self.max_answers,
                'timestamp': int(datetime.now().timestamp()),
                'time_filter': self.time_filter,
                'min_upvotes': self.min_upvotes
            }
            
            results = []
            
            logger.info("Sending search request...")
            async with self.http_client.get(self.search_endpoint, params=params) as response:
                logger.debug(f"Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Response data structure: {list(data.keys()) if data else 'empty'}")
                    
                    if data.get('error'):
                        logger.error(f"API error: {data['error']}")
                        return []
                    
                    # Extract answers from response
                    answers = data.get('answers', [])
                    logger.info(f"Found {len(answers)} answers in response")
                    
                    for answer in answers:
                        try:
                            # Extract answer data
                            answer_id = answer.get('id', '')
                            question = answer.get('question', {})
                            author = answer.get('author', {})
                            content = answer.get('content', '')
                            upvotes = answer.get('upvotes', 0)
                            
                            if not all([answer_id, question, author, content]):
                                continue
                                
                            # Calculate credibility score
                            credibility_score = self._calculate_credibility(answer)
                            
                            if credibility_score >= self.min_credibility:
                                results.append({
                                    'id': f"quora-{answer_id}",
                                    'title': question.get('title', ''),
                                    'url': self.api_base + answer.get('url', ''),
                                    'content': content,
                                    'source': 'quora',
                                    'source_detail': f"Answer by {author.get('name', 'Unknown')}",
                                    'credibility_info': {
                                        'score': credibility_score,
                                        'bias': 'Social Media',
                                        'category': 'Quora'
                                    },
                                    'timestamp': answer.get('created_time', datetime.utcnow().isoformat()),
                                    'author': author.get('name', 'Unknown'),
                                    'metadata': {
                                        'upvotes': upvotes,
                                        'author_url': self.api_base + author.get('url', ''),
                                        'author_credentials': author.get('credentials', []),
                                        'question_url': self.api_base + question.get('url', '')
                                    }
                                })
                                
                        except Exception as e:
                            logger.error(f"Error processing answer: {str(e)}")
                            continue
                            
                    logger.info(f"Found {len(results)} valid answers")
                    
                    # Cache results
                    if results:
                        await self._cache_results(query, results)
                        
                elif response.status == 429:  # Rate limited
                    wait_time = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    return await self.scrape(query)
                    
                else:
                    logger.error(f"API request failed: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response text: {response_text[:500]}")
                    
            return results
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return []

    def _calculate_credibility(self, answer_data: Dict[str, Any]) -> float:
        """Calculate credibility score for an answer."""
        credibility_score = 75.0  # Base score
        
        # Adjust for author credentials
        if answer_data.get('author', {}).get('credentials'):
            credibility_score += 5
            expertise_keywords = ['phd', 'professor', 'expert', 'researcher', 'scientist']
            if any(keyword in ' '.join(answer_data['author']['credentials']).lower() for keyword in expertise_keywords):
                credibility_score += 5
        
        # Adjust for answer quality
        content = answer_data.get('content', '')
        if len(content.split()) > 100:
            credibility_score += 5
        
        # Adjust for engagement
        upvotes = answer_data.get('upvotes', 0)
        credibility_score += min((upvotes / 1000) * 2, 10)
        
        # Cap the score
        return min(max(credibility_score, 0), 95)

    async def close(self):
        """Clean up resources."""
        if self.redis:
            await self.redis.close()
            
        if self.http_client:
            await self.http_client.close() 