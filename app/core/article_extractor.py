"""
Advanced article content extractor for Factryl LLM integration.
Handles Google News redirects and extracts full article content.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, unquote
import re
import time
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Result of article extraction."""
    success: bool
    content: str
    title: str = ""
    author: str = ""
    publish_date: str = ""
    extraction_method: str = ""
    processing_time: float = 0.0
    error: str = ""

class ArticleExtractor:
    """Smart article content extractor with Google News support."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.session = None
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1 hour
        self.max_content_length = self.config.get('max_content_length', 3000)
        self.extraction_timeout = self.config.get('extraction_timeout', 10)
        self.enable_caching = self.config.get('enable_caching', True)
        
        # User agents for different extraction methods
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
    async def setup(self):
        """Initialize the extractor."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.extraction_timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': self.user_agents[0]}
            )
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        if not self.enable_caching:
            return False
        return (time.time() - cache_entry['timestamp']) < self.cache_ttl
    
    def _resolve_google_news_url(self, google_news_url: str) -> str:
        """Attempt to extract the actual article URL from Google News redirect."""
        try:
            # Google News URLs often contain the actual URL encoded
            if 'news.google.com/rss/articles/' in google_news_url:
                # Try to extract from the encoded URL
                # This is a simplified approach - Google's encoding is complex
                return google_news_url  # For now, return as-is and let extraction handle it
            
            return google_news_url
            
        except Exception as e:
            logger.debug(f"URL resolution failed: {e}")
            return google_news_url
    
    async def _extract_with_newspaper(self, url: str) -> ExtractionResult:
        """Extract article content using newspaper3k."""
        try:
            from newspaper import Article
            
            # Resolve Google News URLs
            resolved_url = self._resolve_google_news_url(url)
            
            article = Article(resolved_url)
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 100:
                content = article.text[:self.max_content_length]
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=article.title or "",
                    author=", ".join(article.authors) if article.authors else "",
                    publish_date=article.publish_date.isoformat() if article.publish_date else "",
                    extraction_method="newspaper3k"
                )
            
            return ExtractionResult(
                success=False,
                content="",
                error="No substantial content found"
            )
            
        except Exception as e:
            logger.debug(f"Newspaper extraction failed for {url}: {e}")
            return ExtractionResult(
                success=False,
                content="",
                error=f"Newspaper extraction failed: {str(e)}"
            )
    
    async def _extract_with_requests(self, url: str) -> ExtractionResult:
        """Extract article content using direct HTTP requests and BeautifulSoup."""
        try:
            await self.setup()
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return ExtractionResult(
                        success=False,
                        content="",
                        error=f"HTTP {response.status}"
                    )
                
                html = await response.text()
                
                # Use BeautifulSoup to extract content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Try to find article content using common selectors
                content_selectors = [
                    'article',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    '.story-body',
                    '.content',
                    'main',
                    '#main-content'
                ]
                
                content = ""
                title = ""
                
                # Extract title
                title_elem = soup.find('h1') or soup.find('title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                
                # Extract content
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        # Get all paragraph text
                        paragraphs = content_elem.find_all('p')
                        if paragraphs:
                            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                            break
                
                if not content:
                    # Fallback: get all paragraph text
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs[:10]])  # First 10 paragraphs
                
                if len(content) > 100:
                    content = content[:self.max_content_length]
                    return ExtractionResult(
                        success=True,
                        content=content,
                        title=title,
                        extraction_method="requests+beautifulsoup"
                    )
                
                return ExtractionResult(
                    success=False,
                    content="",
                    error="Insufficient content extracted"
                )
                
        except Exception as e:
            logger.debug(f"Requests extraction failed for {url}: {e}")
            return ExtractionResult(
                success=False,
                content="",
                error=f"Requests extraction failed: {str(e)}"
            )
    
    async def extract_article_content(self, url: str) -> ExtractionResult:
        """Extract full article content from URL with multiple fallback methods."""
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(url)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            result = self.cache[cache_key]['result']
            result.processing_time = time.time() - start_time
            logger.debug(f"Cache hit for {url}")
            return result
        
        # Skip extraction for obviously problematic URLs
        if self._should_skip_extraction(url):
            result = ExtractionResult(
                success=False,
                content="",
                error="URL type not supported for extraction",
                processing_time=time.time() - start_time
            )
            return result
        
        # Try extraction methods in order of preference
        extraction_methods = [
            self._extract_with_newspaper,
            self._extract_with_requests
        ]
        
        for method in extraction_methods:
            try:
                result = await method(url)
                result.processing_time = time.time() - start_time
                
                if result.success:
                    # Cache successful results
                    if self.enable_caching:
                        self.cache[cache_key] = {
                            'result': result,
                            'timestamp': time.time()
                        }
                    
                    logger.info(f"Successfully extracted {len(result.content)} chars from {url} using {result.extraction_method}")
                    return result
                    
            except Exception as e:
                logger.debug(f"Extraction method {method.__name__} failed for {url}: {e}")
                continue
        
        # All methods failed
        result = ExtractionResult(
            success=False,
            content="",
            error="All extraction methods failed",
            processing_time=time.time() - start_time
        )
        
        return result
    
    def _should_skip_extraction(self, url: str) -> bool:
        """Determine if URL should be skipped for extraction."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Skip known problematic domains
            skip_domains = [
                'facebook.com',
                'twitter.com',
                'instagram.com',
                'youtube.com',
                'linkedin.com'
            ]
            
            return any(skip_domain in domain for skip_domain in skip_domains)
            
        except Exception:
            return False
    
    async def enhance_articles_batch(self, articles: List[Dict[str, Any]], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """Enhance multiple articles with extracted content in batches."""
        if not articles:
            return articles
        
        await self.setup()
        enhanced_articles = []
        
        # Process articles in batches
        for i in range(0, len(articles), max_concurrent):
            batch = articles[i:i + max_concurrent]
            
            # Create extraction tasks
            tasks = []
            for article in batch:
                url = article.get('link', '')
                if url and self._should_extract_for_article(article):
                    task = self.extract_article_content(url)
                    tasks.append((article, task))
                else:
                    enhanced_articles.append(article)
            
            # Execute batch
            if tasks:
                try:
                    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                    
                    for (article, _), extraction_result in zip(tasks, results):
                        if isinstance(extraction_result, ExtractionResult) and extraction_result.success:
                            # Enhance article with extracted content
                            article['content'] = extraction_result.content
                            article['metadata'] = article.get('metadata', {})
                            article['metadata'].update({
                                'content_enhanced': True,
                                'extraction_method': extraction_result.extraction_method,
                                'extraction_time': extraction_result.processing_time,
                                'original_content_length': len(article.get('content', '')),
                                'enhanced_content_length': len(extraction_result.content)
                            })
                            
                            # Update title if extracted title is better
                            if extraction_result.title and len(extraction_result.title) > len(article.get('title', '')):
                                article['title'] = extraction_result.title
                        
                        enhanced_articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Batch extraction failed: {e}")
                    # Add articles without enhancement
                    for article, _ in tasks:
                        enhanced_articles.append(article)
            
            # Small delay between batches
            if i + max_concurrent < len(articles):
                await asyncio.sleep(0.5)
        
        return enhanced_articles
    
    def _should_extract_for_article(self, article: Dict[str, Any]) -> bool:
        """Determine if article should have content extracted."""
        # Skip if already has substantial content
        current_content = article.get('content', '')
        if len(current_content) > 500:  # Already has good content
            return False
        
        # Extract for Google News articles
        link = article.get('link', '')
        if 'news.google.com' in link:
            return True
        
        # Extract for articles with minimal content
        if len(current_content) < 200:
            return True
        
        return False 