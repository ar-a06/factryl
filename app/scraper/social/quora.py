"""
Quora scraper module with hybrid API and browser-based approaches.
"""

import asyncio
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, List, Any, Optional
from loguru import logger
import redis.asyncio as redis
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
import urllib.parse
import random
import aiohttp

from .plugin_loader import BaseScraper, rate_limited

class QuoraScraper(BaseScraper):
    """Quora scraper implementation with fallback mechanisms."""

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
        self.headless = quora_config.get('headless', True)
        self.max_retries = quora_config.get('max_retries', 3)
        self.retry_delay = quora_config.get('retry_delay', 5)
        
        # Initialize clients
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.http_client = None
        
        # Mobile User Agents for rotation
        self.mobile_user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36'
        ]

    async def _init_browser(self, use_mobile: bool = False):
        """Initialize Playwright browser."""
        if self.browser is None:
            try:
                logger.info("Starting Playwright...")
                self.playwright = await async_playwright().start()
                
                logger.info("Launching browser...")
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless
                )
                
                logger.info("Creating browser context...")
                context_options = {
                    'viewport': {'width': 1920, 'height': 1080},
                    'user_agent': random.choice(self.mobile_user_agents) if use_mobile else
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                if use_mobile:
                    context_options.update({
                        'device_scale_factor': 2,
                        'is_mobile': True,
                        'has_touch': True
                    })
                
                self.context = await self.browser.new_context(**context_options)
                
                # Block unnecessary resources
                await self.context.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf}", lambda route: route.abort())
                
                logger.info("Creating new page...")
                self.page = await self.context.new_page()
                
                logger.info("Browser initialization complete")
                
            except Exception as e:
                logger.error(f"Failed to initialize browser: {e}")
                await self.close()
                raise

    async def _init_http_client(self):
        """Initialize aiohttp client for API requests."""
        if self.http_client is None:
            self.http_client = aiohttp.ClientSession(
                headers={
                    'User-Agent': random.choice(self.mobile_user_agents),
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Origin': 'https://www.quora.com',
                    'Referer': 'https://www.quora.com/'
                }
            )

    async def _handle_login_wall(self) -> bool:
        """Handle Quora login wall if present."""
        try:
            # Check for login modal
            login_modal = await self.page.query_selector('[class*="login_modal"]')
            if login_modal:
                logger.info("Detected login wall, switching to mobile view...")
                await self.close()
                await self._init_browser(use_mobile=True)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error handling login wall: {e}")
            return False

    async def _wait_for_content(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for content to load with retry logic."""
        start_time = datetime.now()
        max_wait_time = timeout
        
        while (datetime.now() - start_time).total_seconds() * 1000 < max_wait_time:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                return True
            except PlaywrightTimeoutError:
                # Check if we need to handle login wall
                if await self._handle_login_wall():
                    # Reset timer after switching to mobile view
                    start_time = datetime.now()
                    continue
                    
                # Try scrolling to trigger lazy loading
                await self.page.evaluate('window.scrollBy(0, 300)')
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error waiting for content: {e}")
                return False
                
        return False

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                    
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

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
                # Cache for 15 minutes for Quora content
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
            # Cache for 15 minutes
            await self.redis.setex(cache_key, 900, json.dumps(cache_data))
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def _fetch_answers_api(self, query: str) -> List[Dict[str, Any]]:
        """Fetch answers using Quora's mobile API."""
        try:
            await self._init_http_client()
            
            # Build API URL
            encoded_query = urllib.parse.quote(query)
            api_url = f"https://www.quora.com/api/mobile/SearchAnswersResult?q={encoded_query}&limit={self.max_answers}"
            
            logger.info(f"Fetching answers from API: {api_url}")
            
            async with self.http_client.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('answers', [])
                else:
                    logger.error(f"API request failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"API request error: {e}")
            return []

    async def _process_api_answer(self, answer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an answer from the API response."""
        try:
            # Extract basic information
            question = answer_data.get('question', {})
            author = answer_data.get('author', {})
            stats = answer_data.get('stats', {})
            
            # Calculate credibility score
            credibility_score = 75.0  # Base score
            
            # Adjust for author credentials
            if author.get('credentials'):
                credibility_score += 5
                expertise_keywords = ['phd', 'professor', 'expert', 'researcher', 'scientist']
                if any(keyword in author.get('description', '').lower() for keyword in expertise_keywords):
                    credibility_score += 5
            
            # Adjust for answer quality
            content = answer_data.get('content', '')
            if len(content.split()) > 100:
                credibility_score += 5
            
            # Adjust for engagement
            upvotes = stats.get('upvotes', 0)
            comments = stats.get('comments', 0)
            credibility_score += min((upvotes / 1000) * 2, 10)
            credibility_score += min((comments / 100), 5)
            
            # Cap the score
            credibility_score = min(max(credibility_score, 0), 95)
            
            # Generate unique ID
            content_hash = hashlib.md5(f"{question.get('url')}{content}".encode()).hexdigest()
            
            return {
                'id': f"quora-{content_hash}",
                'title': question.get('title', '').strip(),
                'url': question.get('url', ''),
                'content': content.strip(),
                'source': 'quora',
                'source_detail': f"Answer by {author.get('name', 'Unknown')}",
                'credibility_info': {
                    'score': credibility_score,
                    'bias': 'Social Media',
                    'category': 'Quora'
                },
                'timestamp': answer_data.get('created_time', datetime.utcnow().isoformat()),
                'author': author.get('name', 'Unknown'),
                'metadata': {
                    'preview': content[:500].strip(),
                    'upvotes': upvotes,
                    'comments': comments,
                    'shares': stats.get('shares', 0),
                    'author_url': author.get('url', ''),
                    'post_type': 'answer',
                    'scraped_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process API answer: {e}")
            return None

    async def _scrape_browser(self, query: str) -> List[Dict[str, Any]]:
        """Scrape answers using browser-based approach."""
        results = []
        try:
            # Build search URL
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.quora.com/search?q={encoded_query}&type=answer"
            
            logger.info(f"Navigating to: {search_url}")
            await self._retry_with_backoff(self.page.goto, search_url)
            
            # Wait for content
            if not await self._wait_for_content('[class*="answer-content"]'):
                logger.warning("Failed to load answers")
                return results
            
            # Process answers
            answers = await self.page.query_selector_all('[class*="answer-container"]')
            logger.info(f"Found {len(answers)} answer containers")
            
            for answer in answers[:self.max_answers]:
                try:
                    # Extract answer data
                    question = await answer.query_selector('[class*="question-title"]')
                    content = await answer.query_selector('[class*="answer-content"]')
                    author = await answer.query_selector('[class*="author-name"]')
                    stats = await answer.query_selector('[class*="stats"]')
                    
                    if not all([question, content, author]):
                        continue
                    
                    # Process answer data
                    result = {
                        'title': (await question.text_content()).strip(),
                        'url': await question.get_attribute('href'),
                        'content': (await content.text_content()).strip(),
                        'author': (await author.text_content()).strip(),
                        'source': 'quora',
                        'timestamp': datetime.utcnow().isoformat(),
                        'metadata': {
                            'upvotes': 0,
                            'comments': 0,
                            'shares': 0
                        }
                    }
                    
                    # Extract stats if available
                    if stats:
                        stats_text = await stats.text_content()
                        if 'upvote' in stats_text.lower():
                            try:
                                result['metadata']['upvotes'] = int(stats_text.split()[0])
                            except (IndexError, ValueError):
                                pass
                    
                    # Calculate credibility
                    credibility_score = 75.0
                    if len(result['content'].split()) > 100:
                        credibility_score += 5
                    if result['metadata']['upvotes'] > 100:
                        credibility_score += 5
                    
                    result['credibility_info'] = {
                        'score': credibility_score,
                        'bias': 'Social Media',
                        'category': 'Quora'
                    }
                    
                    # Apply filters
                    if (result['metadata']['upvotes'] >= self.min_upvotes and 
                        credibility_score >= self.min_credibility):
                        results.append(result)
                    
                    if len(results) >= self.max_answers:
                        break
                    
                except Exception as e:
                    logger.error(f"Failed to process browser answer: {e}")
                    continue
                
                await asyncio.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Browser scraping failed: {e}")
            
        return results

    @rate_limited(2.0)  # Maximum 2 requests per second
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
            
        results = []
        
        try:
            # Try API approach first
            logger.info("Attempting to fetch answers via API...")
            api_answers = await self._fetch_answers_api(query)
            
            if api_answers:
                logger.info(f"Found {len(api_answers)} answers via API")
                
                for answer_data in api_answers:
                    try:
                        result = await self._process_api_answer(answer_data)
                        if not result:
                            continue
                            
                        # Apply filters
                        if (result['metadata']['upvotes'] >= self.min_upvotes and 
                            result['credibility_info']['score'] >= self.min_credibility):
                            results.append(result)
                            
                        if len(results) >= self.max_answers:
                            break
                            
                    except Exception as e:
                        logger.error(f"Failed to process API answer: {e}")
                        continue
                        
                    await asyncio.sleep(0.5)  # Rate limiting
                    
            else:
                logger.warning("API approach failed, falling back to browser scraping...")
                await self._init_browser()
                results = await self._scrape_browser(query)
            
            # Cache results
            if results:
                await self._cache_results(query, results)
            
        except Exception as e:
            logger.error(f"Quora scraping failed: {e}")
            
        logger.info(f"Scraped {len(results)} items from Quora")
        return results

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            # Try API validation first
            await self._init_http_client()
            async with self.http_client.get("https://www.quora.com/api/mobile/check") as response:
                if response.status == 200:
                    return True
                    
            # Fall back to browser validation
            await self._init_browser()
            logger.info("Validating scraper by visiting Quora homepage...")
            await self.page.goto("https://www.quora.com")
            await self.page.wait_for_load_state('networkidle')
            title = await self.page.title()
            logger.info(f"Page title: {title}")
            return "Quora" in title
            
        except Exception as e:
            logger.error(f"Quora scraper validation failed: {e}")
            return False

    async def close(self):
        """Clean up resources."""
        if self.redis:
            await self.redis.close()
            
        if self.http_client:
            await self.http_client.close()
            
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop() 