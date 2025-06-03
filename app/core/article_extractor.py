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
    """Result of article content extraction."""
    success: bool
    content: str
    title: str = ""
    author: str = ""
    publish_date: str = ""
    extraction_method: str = ""
    processing_time: float = 0.0
    error: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

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
    
    async def _resolve_google_news_url(self, google_news_url: str) -> str:
        """Resolve Google News redirect URL to actual article URL."""
        try:
            # If it's not a Google News URL, return as-is
            if 'news.google.com' not in google_news_url:
                return google_news_url
            
            logger.info(f"Attempting to resolve Google News URL: {google_news_url}")
            
            # Method 1: Try using Google's redirect service directly
            try:
                # Extract the article ID from the URL
                import re
                
                # Look for the article ID pattern in Google News URLs
                article_match = re.search(r'/articles/([^?]+)', google_news_url)
                if article_match:
                    article_id = article_match.group(1)
                    logger.info(f"Found article ID: {article_id[:50]}...")
                    
                    # Try different Google redirect endpoints
                    redirect_urls = [
                        f"https://news.google.com/articles/{article_id}",
                        f"https://news.google.com/rss/articles/{article_id}",
                        f"https://www.google.com/url?rct=j&sa=t&url={article_id}",
                        f"https://news.google.com/topstories/article/{article_id}"
                    ]
                    
                    for redirect_url in redirect_urls:
                        try:
                            logger.info(f"Trying redirect URL: {redirect_url[:100]}...")
                            
                            timeout = aiohttp.ClientTimeout(total=15)
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                'Accept-Language': 'en-US,en;q=0.5',
                                'Accept-Encoding': 'gzip, deflate',
                                'Connection': 'keep-alive',
                                'Upgrade-Insecure-Requests': '1',
                                'Cache-Control': 'no-cache'
                            }
                            
                            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                                async with session.get(redirect_url, allow_redirects=True, max_redirects=10) as response:
                                    final_url = str(response.url)
                                    logger.info(f"Response: {response.status}, Final URL: {final_url}")
                                    
                                    # Check if we got a real article URL
                                    if (response.status == 200 and 
                                        'news.google.com' not in final_url and
                                        len(final_url) > 20 and
                                        any(domain in final_url for domain in ['.com', '.org', '.net', '.co.uk', '.au'])):
                                        
                                        logger.info(f"Successfully resolved via redirect: {final_url}")
                                        return final_url
                        
                        except Exception as redirect_error:
                            logger.info(f"Redirect attempt failed: {redirect_error}")
                            continue
                            
            except Exception as redirect_method_error:
                logger.warning(f"Redirect method failed: {redirect_method_error}")
            
            # Method 2: Try to decode using URL structure analysis
            try:
                # Google News URLs sometimes contain encoded data
                # Let's try to extract potential URLs from the structure
                
                # Split the URL into parts
                parts = google_news_url.split('/')
                
                for part in parts:
                    if len(part) > 50:  # Long encoded parts
                        # Try different decoding approaches
                        try:
                            # Check if it contains URL-like patterns
                            import urllib.parse
                            
                            # Try URL decoding first
                            decoded = urllib.parse.unquote(part)
                            if 'http' in decoded:
                                # Extract URLs from decoded content
                                url_pattern = r'https?://[^\s<>"\']+\.[a-z]{2,}[^\s<>"\']*'
                                urls = re.findall(url_pattern, decoded)
                                for url in urls:
                                    if 'google.com' not in url:
                                        logger.info(f"Found URL in decoded part: {url}")
                                        return url
                            
                            # Try base64 decoding with different padding
                            import base64
                            
                            for padding in ['', '=', '==', '===']:
                                try:
                                    padded_part = part + padding
                                    decoded_bytes = base64.b64decode(padded_part, validate=True)
                                    decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                                    
                                    # Look for URLs in decoded text
                                    url_pattern = r'https?://[^\s<>"\']+\.[a-z]{2,}[^\s<>"\']*'
                                    urls = re.findall(url_pattern, decoded_text)
                                    for url in urls:
                                        if 'google.com' not in url and len(url) > 20:
                                            logger.info(f"Found URL in base64 decoded content: {url}")
                                            return url
                                            
                                except Exception:
                                    continue
                                    
                        except Exception as decode_error:
                            continue
                            
            except Exception as decode_method_error:
                logger.warning(f"Decode method failed: {decode_method_error}")
            
            # Method 3: Try alternative Google services
            try:
                # Sometimes we can use Google's search to find the actual article
                search_query = None
                
                # Try to extract a search query from the URL parameters
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(google_news_url)
                query_params = parse_qs(parsed_url.query)
                
                # Look for potential search terms in the URL itself
                if 'q=' in google_news_url:
                    search_query = google_news_url.split('q=')[1].split('&')[0]
                    search_query = urllib.parse.unquote(search_query)
                    logger.info(f"Found search query in URL: {search_query}")
                
                # If we found a search query, try to find the article through search
                if search_query and len(search_query) > 5:
                    # This would require implementing a search-based fallback
                    # For now, just log it
                    logger.info(f"Could implement search fallback for: {search_query}")
                    
            except Exception as search_method_error:
                logger.warning(f"Search method failed: {search_method_error}")
            
            # Method 4: Try mobile or AMP versions
            try:
                # Sometimes mobile versions are more accessible
                mobile_variants = [
                    google_news_url.replace('news.google.com', 'm.google.com'),
                    google_news_url.replace('news.google.com', 'news.google.com/m'),
                    google_news_url + '&hl=en&gl=US&ceid=US:en'
                ]
                
                for mobile_url in mobile_variants:
                    try:
                        timeout = aiohttp.ClientTimeout(total=10)
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                        }
                        
                        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                            async with session.get(mobile_url, allow_redirects=True, max_redirects=5) as response:
                                final_url = str(response.url)
                                
                                if (response.status == 200 and 
                                    'google.com' not in final_url and
                                    len(final_url) > 20):
                                    
                                    logger.info(f"Mobile variant resolved: {final_url}")
                                    return final_url
                                    
                    except Exception:
                        continue
                        
            except Exception as mobile_method_error:
                logger.warning(f"Mobile method failed: {mobile_method_error}")
            
            # If all methods fail, log the failure and return original URL
            logger.warning(f"All Google News URL resolution methods failed for: {google_news_url}")
            
            # As a last resort, try to extract any domain information we can find
            try:
                # Look for any domain patterns in the URL itself
                domain_pattern = r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
                domains = re.findall(domain_pattern, google_news_url)
                
                for domain in domains:
                    if domain != 'google.com' and domain != 'news.google.com':
                        # Try to construct a reasonable URL
                        constructed_url = f"https://{domain}"
                        logger.info(f"Attempting constructed URL from domain: {constructed_url}")
                        
                        # Quick test if this domain exists
                        try:
                            timeout = aiohttp.ClientTimeout(total=5)
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                async with session.head(constructed_url) as response:
                                    if response.status < 400:
                                        logger.info(f"Domain-based URL works: {constructed_url}")
                                        return constructed_url
                        except Exception:
                            continue
                            
            except Exception as domain_method_error:
                logger.warning(f"Domain extraction failed: {domain_method_error}")
            
            return google_news_url
            
        except Exception as e:
            logger.error(f"Google News URL resolution completely failed: {e}")
            return google_news_url
    
    async def _extract_with_newspaper(self, url: str) -> ExtractionResult:
        """Extract article content using newspaper3k."""
        try:
            from newspaper import Article
            
            # Resolve Google News URLs first
            resolved_url = await self._resolve_google_news_url(url)
            
            article = Article(resolved_url)
            article.download()
            article.parse()
            
            # Also extract natural language processing features and images
            try:
                article.nlp()
            except Exception as e:
                logger.debug(f"NLP extraction failed for {resolved_url}: {e}")
            
            if article.text and len(article.text) > 100:
                content = article.text[:self.max_content_length]
                
                # Extract additional metadata including images
                metadata = {
                    'top_image': article.top_image or "",
                    'images': list(article.images) if article.images else [],
                    'keywords': list(article.keywords) if hasattr(article, 'keywords') and article.keywords else [],
                    'summary': article.summary if hasattr(article, 'summary') and article.summary else "",
                    'meta_description': article.meta_description or "",
                    'meta_keywords': article.meta_keywords or "",
                    'canonical_link': article.canonical_link or "",
                    'meta_favicon': article.meta_favicon or "",
                    'resolved_url': resolved_url  # Include the resolved URL for debugging
                }
                
                return ExtractionResult(
                    success=True,
                    content=content,
                    title=article.title or "",
                    author=", ".join(article.authors) if article.authors else "",
                    publish_date=article.publish_date.isoformat() if article.publish_date else "",
                    extraction_method="newspaper3k",
                    metadata=metadata
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
            
            # Resolve Google News URLs first
            resolved_url = await self._resolve_google_news_url(url)
            
            async with self.session.get(resolved_url) as response:
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
                    
                    # Extract images from the article
                    images = []
                    top_image = ""
                    
                    # Look for Open Graph image first (often the best quality)
                    og_image = soup.find('meta', attrs={'property': 'og:image'})
                    if og_image and og_image.get('content'):
                        top_image = og_image.get('content')
                        images.append(top_image)
                    
                    # Find other images in the article content
                    img_tags = soup.find_all('img')
                    for img in img_tags:
                        src = img.get('src') or img.get('data-src')  # Handle lazy loading
                        if src and src not in images:
                            # Make relative URLs absolute
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                from urllib.parse import urljoin
                                src = urljoin(resolved_url, src)
                            
                            # Filter out small/icon images
                            width = img.get('width')
                            height = img.get('height')
                            if width and height:
                                try:
                                    if int(width) < 100 or int(height) < 100:
                                        continue
                                except ValueError:
                                    pass
                            
                            # Skip if it looks like an icon or logo
                            alt_text = img.get('alt', '').lower()
                            if any(skip_word in alt_text for skip_word in ['logo', 'icon', 'avatar', 'profile']):
                                continue
                            
                            images.append(src)
                    
                    # If we don't have a top image yet, use the first good image
                    if not top_image and images:
                        top_image = images[0]
                    
                    # Extract meta tags for additional info
                    meta_description = ""
                    meta_keywords = ""
                    
                    meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
                    if meta_desc:
                        meta_description = meta_desc.get('content', '')
                    
                    meta_kw = soup.find('meta', attrs={'name': 'keywords'})
                    if meta_kw:
                        meta_keywords = meta_kw.get('content', '')
                    
                    metadata = {
                        'top_image': top_image,
                        'images': images[:10],  # Limit to first 10 images
                        'meta_description': meta_description,
                        'meta_keywords': meta_keywords,
                        'keywords': [],
                        'summary': "",
                        'canonical_link': "",
                        'meta_favicon': "",
                        'resolved_url': resolved_url  # Include the resolved URL for debugging
                    }
                    
                    return ExtractionResult(
                        success=True,
                        content=content,
                        title=title,
                        extraction_method="requests+beautifulsoup",
                        metadata=metadata
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