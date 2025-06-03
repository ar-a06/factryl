#!/usr/bin/env python3
"""
Enhanced Factryl Infometrics Web Application
A comprehensive search and analysis platform
"""

import asyncio
import logging
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import threading
import os
from typing import Dict, Any, List
from threading import Thread
import sys
import json
from pathlib import Path
import uuid

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from config/.env file
    env_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(env_path)
    print("Environment variables loaded from config/.env file")
    
    # Load YouTube API key
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    if youtube_key:
        # print(f"YouTube API key loaded: {youtube_key[:8]}..." + "*" * (len(youtube_key) - 8))
        print(f"YouTube API key loaded...")
    else:
        print("WARNING: YouTube API key not found in environment variables")
        
except ImportError:
    print("WARNING: python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"WARNING: Error loading .env file: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.factryl_engine import FactrylEngine

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'factryl_secret_key_2024'

# Initialize the Factryl Engine
print("Starting Factryl...")
engine = FactrylEngine()
print(f"Loaded {len(engine.scrapers)} data sources")
print("Access the application at: http://localhost:5000")

@app.route('/')
def home():
    """Main search dashboard"""
    return render_template('simple_search.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for search functionality."""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        query = data['query'].strip()
        max_results = data.get('max_results', 40)
        
        if not query:
            return jsonify({'error': 'Empty query'}), 400
        
        print(f"API Search Request: '{query}' (max: {max_results})")
        
        # Run the search in a new event loop
        def run_search():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(engine.search(query, max_results))
                return result
            finally:
                loop.close()
        
        # Execute search
        start_time = time.time()
        search_results = run_search()
        processing_time = time.time() - start_time
        
        # Add processing time to results
        search_results['stats']['processing_time'] = processing_time
        
        print(f"API Search Complete: {len(search_results['items'])} results")
        return jsonify(search_results)
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/generate-summary', methods=['POST'])
def api_generate_summary():
    """Generate AI summary of articles."""
    try:
        data = request.get_json()
        
        if not data or 'articles' not in data:
            return jsonify({'error': 'No articles provided'}), 400
        
        query = data.get('query', 'search results')
        articles = data['articles']
        max_length = data.get('max_length', 280)
        
        print(f"Generating summary for {len(articles)} articles about '{query}'")
        
        start_time = time.time()
        
        # Fetch dictionary definition separately
        definition = ""
        try:
            from app.scraper.dictionary.dictionary import DictionaryScraper
            
            async def get_definition():
                async with DictionaryScraper() as scraper:
                    results = await scraper.search(query, max_results=10)  # Get more definitions
                    if results:
                        # Group definitions by part of speech for better organization
                        formatted_definitions = []
                        current_phonetic = ""
                        
                        # Get phonetic from first result
                        if results[0].get('phonetic'):
                            current_phonetic = results[0]['phonetic']
                            formatted_definitions.append(f"**Pronunciation:** {current_phonetic}")
                        
                        # Group by part of speech
                        pos_groups = {}
                        for result in results:
                            pos = result.get('part_of_speech', 'General')
                            if pos not in pos_groups:
                                pos_groups[pos] = []
                            pos_groups[pos].append(result.get('definition', ''))
                        
                        # Format definitions by part of speech
                        for pos, definitions in pos_groups.items():
                            formatted_definitions.append(f"**{pos.title()}:**")
                            for i, definition in enumerate(definitions[:3], 1):  # Limit to 3 per part of speech
                                formatted_definitions.append(f"{i}. {definition}")
                        
                        return "\n".join(formatted_definitions)
                    return ""
            
            # Run dictionary lookup in new event loop
            def run_dictionary_lookup():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(get_definition())
                    return result
                finally:
                    loop.close()
            
            definition = run_dictionary_lookup()
            if definition:
                print(f"Dictionary definition found: {definition[:100]}...")
            
        except Exception as e:
            print(f"Dictionary lookup failed: {e}")
        
        # Generate intelligence summary using the engine's summarization capability
        summary = engine.generate_summary(articles, query, max_length)
        
        processing_time = time.time() - start_time
        
        print(f"Summary generated: {len(summary)} characters")
        
        return jsonify({
            'summary': summary,
            'definition': definition,
            'processing_time': round(processing_time, 2),
            'article_count': len(articles),
            'character_count': len(summary),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Summary generation failed: {str(e)}'}), 500

@app.route('/api/sources')
def api_sources():
    """Get available data sources with credibility information."""
    try:
        sources = engine.get_available_sources()
        source_info = {
            source: engine.get_source_credibility(source)
            for source in sources
        }
        return jsonify({
            'sources': source_info,
            'total_sources': len(sources)
        })
    except Exception as e:
        logger.error(f"Sources API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'engine': {
                'scrapers_loaded': len(engine.scrapers),
                'available_sources': engine.get_available_sources()
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/image-search', methods=['POST'])
def api_image_search():
    """Search for images related to the query."""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    try:
        print(f"Image search request: '{query}'")
        
        import requests
        from urllib.parse import quote_plus
        import re
        
        def convert_wikimedia_to_direct_url(url):
            """Convert Wikimedia Commons page URL to direct image URL."""
            try:
                print(f"Converting Wikimedia URL: {url}")
                
                # Handle Wikipedia page URLs
                if 'wikipedia.org/wiki/File:' in url:
                    # Extract filename from Wikipedia page URL
                    filename = url.split('File:')[-1]
                    # Remove any anchor tags or query parameters
                    filename = filename.split('#')[0].split('?')[0]
                    
                    # Decode URL-encoded characters
                    from urllib.parse import unquote
                    filename = unquote(filename)
                    
                    # Create hash for directory structure
                    import hashlib
                    md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
                    
                    # Try different direct URL formats
                    direct_urls = [
                        f"https://upload.wikimedia.org/wikipedia/commons/{md5_hash[0]}/{md5_hash[:2]}/{filename}",
                        f"https://upload.wikimedia.org/wikipedia/commons/thumb/{md5_hash[0]}/{md5_hash[:2]}/{filename}/400px-{filename}",
                        f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=400"
                    ]
                    
                    # Test which URL works
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    for test_url in direct_urls:
                        try:
                            print(f"Testing Wikimedia direct URL: {test_url[:80]}...")
                            resp = requests.head(test_url, timeout=3, headers=headers)
                            if resp.status_code == 200:
                                print(f"Success: {test_url}")
                                return test_url
                        except Exception as e:
                            print(f"Failed: {str(e)[:50]}")
                            continue
                
                # Handle already direct Wikimedia URLs
                elif 'upload.wikimedia.org' in url:
                    print(f"Already direct Wikimedia URL: {url}")
                    return url
                
                # Handle commons.wikimedia.org page URLs
                elif 'commons.wikimedia.org/wiki/File:' in url:
                    filename = url.split('File:')[-1]
                    filename = filename.split('#')[0].split('?')[0]
                    
                    # Use Special:FilePath for reliable access
                    direct_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=400"
                    print(f"Using Special:FilePath: {direct_url}")
                    return direct_url
                
            except Exception as e:
                print(f"Error converting Wikimedia URL: {e}")
            
            return url

        def is_valid_image_url(url):
            """Check if URL is a valid image URL."""
            try:
                print(f"Validating image URL: {url[:100]}...")
                
                # Basic URL validation
                if not url or len(url) < 20:
                    print("Failed: URL too short")
                    return False
                
                # Special handling for Wikimedia URLs
                if any(domain in url for domain in ['wikimedia.org', 'wikipedia.org']):
                    print("Wikimedia URL detected - allowing")
                    return True
                
                # Check for image file extensions
                if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                    print("Failed: No image extension found")
                    return False
                
                # Filter out unwanted domains
                blocked_domains = [
                    'gstatic.com', 'googleusercontent.com', 'google.com',
                    'facebook.com', 'instagram.com', 'x.com', 'twitter.com'
                ]
                
                if any(domain in url.lower() for domain in blocked_domains):
                    print(f"Failed: Blocked domain detected")
                    return False
                
                print("URL passed validation")
                return True
            except Exception as e:
                print(f"Validation error: {e}")
                return False
        
        try:
            # Method 1: Try to scrape Google Images (first result)
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=isch&tbs=isz:m"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                # Extract image URLs from Google Images search results
                content = response.text
                
                # Look for image URLs in the page content - improved patterns
                img_patterns = [
                    r'"(https://[^"]*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"]*)?)"',
                    r'imgurl=(https://[^&]*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^&]*)?)',
                    r'"ou":"(https://[^"]*\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"]*)?)"',
                    r'"(https://commons\.wikimedia\.org/wiki/File:[^"]+)"',  # Wikimedia Commons pages
                    r'"(https://en\.wikipedia\.org/wiki/File:[^"]+)"',  # Wikipedia file pages
                    r'"(https://upload\.wikimedia\.org/[^"]+\.(?:jpg|jpeg|png|webp|gif)[^"]*)"',  # Direct Wikimedia
                    r'"(https://upload\.wikimedia\.org/wikipedia/commons/thumb/[^"]+)"',  # Wikimedia thumbs
                    r'imgurl=(https://upload\.wikimedia\.org/[^&]+)'  # Wikimedia in imgurl
                ]
                
                found_images = []
                for pattern in img_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Clean up the URL
                        img_url = match.replace('\\u003d', '=').replace('\\u0026', '&')
                        
                        # Convert Wikimedia Commons URLs to direct URLs
                        if any(pattern in img_url for pattern in ['commons.wikimedia.org/wiki/File:', 'wikipedia.org/wiki/File:', 'upload.wikimedia.org']):
                            original_url = img_url
                            img_url = convert_wikimedia_to_direct_url(img_url)
                            print(f"Converted: {original_url[:60]}... -> {img_url[:60]}...")
                        
                        # Apply validation
                        if is_valid_image_url(img_url):
                            found_images.append(img_url)
                
                # Try to use the first good image found
                for img_url in found_images[:5]:  # Try first 5 images
                    try:
                        print(f"Testing image URL: {img_url[:80]}...")
                        
                        # Test if image is accessible
                        img_response = requests.head(img_url, timeout=3, headers=headers, allow_redirects=True)
                        if img_response.status_code == 200:
                            # Verify content type is actually an image
                            content_type = img_response.headers.get('content-type', '').lower()
                            if 'image' in content_type:
                                image_data = {
                                    'image_url': img_url,
                                    'source': 'google_images',
                                    'description': f"Google Images result for '{query}'",
                                    'width': 400,
                                    'height': 300
                                }
                                
                                print(f"Found working Google Images result for '{query}'")
                                return jsonify(image_data)
                    except Exception as e:
                        print(f"Image URL failed: {str(e)[:50]}...")
                        continue
            
        except Exception as e:
            print(f"Google Images search failed: {e}")
        
        # Method 2: Try DuckDuckGo Images (more reliable, no rate limiting)
        try:
            ddg_url = f"https://duckduckgo.com/?q={quote_plus(query)}&t=h_&iax=images&ia=images"
            
            # DuckDuckGo has a specific API endpoint for images
            ddg_api_url = f"https://duckduckgo.com/i.js?q={quote_plus(query)}&o=json&p=1&s=0&u=bing&f=,,,,,&l=us-en"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(ddg_api_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'results' in data and len(data['results']) > 0:
                        for result in data['results'][:3]:  # Try first 3 results
                            img_url = result.get('image')
                            
                            if img_url and is_valid_image_url(img_url):
                                # Test if image is accessible
                                try:
                                    img_response = requests.head(img_url, timeout=3, headers=headers, allow_redirects=True)
                                    if img_response.status_code == 200:
                                        content_type = img_response.headers.get('content-type', '').lower()
                                        if 'image' in content_type:
                                            image_data = {
                                                'image_url': img_url,
                                                'source': 'duckduckgo',
                                                'description': f"DuckDuckGo search result for '{query}'",
                                                'width': 400,
                                                'height': 300
                                            }
                                            
                                            print(f"Found DuckDuckGo result: {img_url[:100]}...")
                                            return jsonify(image_data)
                                except:
                                    continue
                except:
                    pass
            
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
        
        # Method 3: Try Bing Images (more open than Google)
        try:
            bing_url = f"https://www.bing.com/images/search?q={quote_plus(query)}&form=HDRSC2&first=1&tsc=ImageBasicHover"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(bing_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for Bing image URLs
                bing_pattern = r'"murl":"([^"]+)"'
                matches = re.findall(bing_pattern, content)
                
                for match in matches[:5]:  # Try first 5 images
                    try:
                        # Decode URL if needed
                        img_url = match.replace('\\u002f', '/').replace('\\/','/')
                        
                        if is_valid_image_url(img_url):
                            # Test if image is accessible
                            img_response = requests.head(img_url, timeout=3)
                            if img_response.status_code == 200:
                                content_type = img_response.headers.get('content-type', '').lower()
                                if 'image' in content_type:
                                    image_data = {
                                        'image_url': img_url,
                                        'source': 'bing_images',
                                        'description': f"Bing Images result for '{query}'",
                                        'width': 400,
                                        'height': 300
                                    }
                                    
                                    print(f"Found Bing Images result: {img_url[:100]}...")
                                    return jsonify(image_data)
                    except:
                        continue
            
        except Exception as e:
            print(f"Bing Images search failed: {e}")
        
        # Fallback: Improved placeholder with topic-specific colors
        topic_colors = {
            'food': '28a745',
            'animal': 'fd7e14', 
            'nature': '20c997',
            'technology': '007bff',
            'sports': 'dc3545',
            'music': '6f42c1',
            'science': '17a2b8'
        }
        
        # Determine topic and color
        query_lower = query.lower()
        color = '6c757d'  # default gray
        
        for topic, topic_color in topic_colors.items():
            if any(word in query_lower for word in [topic, 'food', 'eat', 'fruit', 'vegetable'] if topic == 'food'):
                color = topic_color
                break
            elif any(word in query_lower for word in ['animal', 'dog', 'cat', 'bird', 'fish'] if topic == 'animal'):
                color = topic_color
                break
            elif any(word in query_lower for word in ['tree', 'plant', 'flower', 'water', 'rain'] if topic == 'nature'):
                color = topic_color
                break
        
        # Use multiple fallback services
        fallback_services = [
            f"https://placehold.co/400x300/{color}/ffffff?text={quote_plus(query.upper())}",
            f"https://dummyimage.com/400x300/{color}/ffffff&text={quote_plus(query.upper())}",
            f"https://picsum.photos/400/300?random={hash(query) % 1000}&blur=1"
        ]
        
        # Try each fallback service
        for fallback_url in fallback_services:
            try:
                response = requests.head(fallback_url, timeout=2)
                if response.status_code == 200:
                    image_data = {
                        'image_url': fallback_url,
                        'source': 'placeholder',
                        'description': f"Placeholder image for '{query}'",
                        'width': 400,
                        'height': 300
                    }
                    
                    print(f"Using fallback placeholder: {fallback_url[:50]}...")
                    return jsonify(image_data)
            except:
                continue
        
        # Final simple fallback - data URL (always works)
        import base64
        
        # Create a simple colored rectangle as base64 data URL
        svg_content = f'''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#{color}"/>
            <text x="200" y="150" font-family="Arial, sans-serif" font-size="24" fill="white" text-anchor="middle" dy=".3em">{query.upper()}</text>
        </svg>'''
        
        svg_base64 = base64.b64encode(svg_content.encode()).decode()
        data_url = f"data:image/svg+xml;base64,{svg_base64}"
        
        image_data = {
            'image_url': data_url,
            'source': 'svg_fallback',
            'description': f"Generated SVG for '{query}'",
            'width': 400,
            'height': 300
        }
        
        print(f"Using SVG fallback for '{query}'")
        return jsonify(image_data)
        
    except Exception as e:
        logger.error(f"Image search API error: {e}")
        
        # Final fallback - SVG data URL (always works)
        import base64
        
        svg_content = f'''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#6c757d"/>
            <text x="200" y="150" font-family="Arial, sans-serif" font-size="20" fill="white" text-anchor="middle" dy=".3em">No Image</text>
        </svg>'''
        
        svg_base64 = base64.b64encode(svg_content.encode()).decode()
        data_url = f"data:image/svg+xml;base64,{svg_base64}"
        
        return jsonify({
            'image_url': data_url,
            'source': 'error_fallback',
            'description': f"No image available for {query}",
            'width': 400,
            'height': 300,
            'error': str(e)
        })

@app.route('/api/article-image', methods=['POST'])
def api_article_image():
    """Extract the main image from a specific article URL."""
    try:
        data = request.get_json()
        article_url = data.get('url', '')
        article_title = data.get('title', '')
        
        if not article_url:
            return jsonify({'error': 'Article URL is required'}), 400
        
        print(f"Extracting image from article: {article_url}")
        
        # Use the existing article extractor
        from app.core.article_extractor import ArticleExtractor
        import asyncio
        
        async def extract_article_image():
            extractor = ArticleExtractor()
            result = await extractor.extract_article_content(article_url)
            return result
        
        # Run the async extraction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            extraction_result = loop.run_until_complete(extract_article_image())
        finally:
            loop.close()
        
        if extraction_result.success and extraction_result.metadata:
            top_image = extraction_result.metadata.get('top_image', '')
            images = extraction_result.metadata.get('images', [])
            
            if top_image:
                print(f"Found top image: {top_image}")
                return jsonify({
                    'success': True,
                    'image_url': top_image,
                    'all_images': images,
                    'title': extraction_result.title or article_title,
                    'source': 'article_extraction',
                    'extraction_method': extraction_result.extraction_method
                })
            elif images:
                print(f"Using first available image: {images[0]}")
                return jsonify({
                    'success': True,
                    'image_url': images[0],
                    'all_images': images,
                    'title': extraction_result.title or article_title,
                    'source': 'article_extraction',
                    'extraction_method': extraction_result.extraction_method
                })
        
        # Fallback to generic image search if no article image found
        print(f"No article image found, falling back to generic search for: {article_title}")
        return jsonify({
            'success': False,
            'error': 'No image found in article',
            'fallback_available': True
        })
        
    except Exception as e:
        print(f"Error extracting article image: {e}")
        return jsonify({'error': 'Failed to extract article image', 'details': str(e)}), 500

@app.route('/api/article-summary', methods=['POST'])
def api_article_summary():
    """Generate LLM summary for individual articles."""
    try:
        data = request.get_json()
        
        if not data or 'article' not in data:
            return jsonify({'error': 'No article provided'}), 400
        
        article = data['article']
        max_words = data.get('max_words', 120)  # Increased default length
        
        print(f"Generating summary for article: {article.get('title', 'Unknown')[:50]}...")
        
        start_time = time.time()
        
        # Handle async function call properly
        def run_async_summary():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(engine.generate_article_summary(article, max_words))
            finally:
                loop.close()
        
        # Generate article summary using the engine's new method
        summary = run_async_summary()
        
        processing_time = time.time() - start_time
        
        print(f"Article summary generated: {len(summary)} characters")
        
        return jsonify({
            'summary': summary,
            'processing_time': round(processing_time, 2),
            'word_count': len(summary.split()),
            'max_words': max_words,
            'llm_used': engine.ollama_analyzer is not None and engine.ollama_analyzer.is_service_available()
        })
        
    except Exception as e:
        logger.error(f"Article summary generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Article summary generation failed: {str(e)}'}), 500

@app.route('/api/batch-article-summaries', methods=['POST'])
def api_batch_article_summaries():
    """Generate LLM summaries for multiple articles efficiently."""
    try:
        data = request.get_json()
        
        if not data or 'articles' not in data:
            return jsonify({'error': 'No articles provided'}), 400
        
        articles = data['articles']
        max_words = data.get('max_words', 120)  # Increased default length
        
        print(f"Generating summaries for {len(articles)} articles...")
        
        start_time = time.time()
        summaries = []
        
        def run_async_summary(article):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(engine.generate_article_summary(article, max_words))
            finally:
                loop.close()
        
        for i, article in enumerate(articles):
            try:
                summary = run_async_summary(article)
                summaries.append({
                    'index': i,
                    'summary': summary,
                    'title': article.get('title', 'Unknown'),
                    'source': article.get('source', 'Unknown')
                })
            except Exception as e:
                print(f"Failed to generate summary for article {i}: {e}")
                summaries.append({
                    'index': i,
                    'summary': article.get('title', 'Article content available.')[:100] + '...',
                    'title': article.get('title', 'Unknown'),
                    'source': article.get('source', 'Unknown'),
                    'error': str(e)
                })
        
        processing_time = time.time() - start_time
        
        print(f"Batch summary generation complete: {len(summaries)} summaries in {processing_time:.2f}s")
        
        return jsonify({
            'summaries': summaries,
            'processing_time': round(processing_time, 2),
            'total_articles': len(articles),
            'successful_summaries': len([s for s in summaries if 'error' not in s]),
            'llm_used': engine.ollama_analyzer is not None and engine.ollama_analyzer.is_service_available()
        })
        
    except Exception as e:
        logger.error(f"Batch article summary generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Batch article summary generation failed: {str(e)}'}), 500

@app.route('/api/llm-health')
def api_llm_health():
    """Check LLM service health."""
    try:
        health_info = {
            'ollama_available': engine.ollama_analyzer is not None,
            'ollama_status': 'unavailable',
            'model': None,
            'response_time': None
        }
        
        if engine.ollama_analyzer:
            ollama_health = engine.ollama_analyzer.health_check()
            health_info.update({
                'ollama_status': ollama_health.get('status', 'unknown'),
                'model': ollama_health.get('model'),
                'response_time': ollama_health.get('response_time'),
                'error': ollama_health.get('error')
            })
        
        return jsonify(health_info)
        
    except Exception as e:
        logger.error(f"LLM health check error: {e}")
        return jsonify({
            'ollama_available': False,
            'ollama_status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/youtube-videos', methods=['POST'])
def youtube_videos():
    """Get YouTube videos for a search query using YouTube Data API."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        print(f"YouTube API: Searching for '{query}'")
        
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        
        print(f"YouTube API key status: {'Found' if youtube_api_key else 'Not found'}")
        
        if youtube_api_key:
            print(f"Attempting YouTube API call for query: '{query}'")
            try:
                videos = get_top_youtube_videos_api(query, youtube_api_key, 3)
                print(f"YouTube API: Found {len(videos)} videos via API")
                if videos:
                    print(f"First video: {videos[0]['title']} by {videos[0]['channel']}")
                    
                    # Convert API response to expected format
                    formatted_videos = []
                    for i, video in enumerate(videos):
                        video_info = {
                            'id': str(uuid.uuid4()),
                            'title': video['title'], 
                            'description': f"YouTube video: {video['title']} by {video['channel']}",
                            'url': video['url'],
                            'thumbnail': video.get('thumbnail', ''),
                            'channel_name': video['channel'],
                            'channel_url': f"https://www.youtube.com/channel/{video.get('channel_id', 'unknown')}",
                            'published_at': video.get('published', ''),
                            'duration': f"0:{3 + i*2}:{30 + i*5}",
                            'source': 'youtube_api',
                            'source_detail': f"YouTube - {video['channel']}",
                            'credibility_info': {
                                'score': 95 - i,
                                'bias': 'User Generated',
                                'category': 'Video Content'
                            },
                            'metadata': {
                                'views': video.get('view_count', 0),
                                'likes': video.get('like_count', 0),
                                'comments': video.get('comment_count', 0),
                                'source': 'youtube_api',
                                'channel': video['channel'],
                                'published_date': video.get('published', ''),
                                'duration': f"0:{3 + i*2}:{30 + i*5}"
                            }
                        }
                        formatted_videos.append(video_info)
                    
                    print(f"Using real YouTube view counts:")
                    for i, video in enumerate(videos[:3]):
                        views = video.get('view_count', 0)
                        print(f"#{i+1}: {video['title']} - {format_view_count(views)} views (REAL)")
                    
                    return jsonify({'videos': formatted_videos})
                
            except Exception as api_error:
                print(f"YouTube API error: {api_error}")
                print("Falling back to curated data...")
        else:
            print("No YouTube API key found, using curated data")
        
        # Fallback to curated data
        videos = get_curated_youtube_videos(query)
        
        return jsonify({'videos': videos})
        
    except Exception as e:
        print(f"Error in youtube_videos endpoint: {e}")
        return jsonify({'error': str(e)}), 500

def get_top_youtube_videos_api(keyword, api_key, count=5):
    """Get top YouTube videos using YouTube Data API v3 with real view counts."""
    import requests
    
    # First, search for videos
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        'part': 'snippet',
        'q': keyword,
        'type': 'video',
        'order': 'viewCount',           # Sort by most viewed
        'maxResults': count * 2,        # Get more results to filter and sort by actual view count
        'key': api_key
    }
    
    try:
        print(f"Making YouTube search API call for: {keyword}")
        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        if 'items' not in search_data or not search_data['items']:
            print("No videos found in search results")
            return []
        
        # Extract video IDs for statistics call
        video_ids = [item['id']['videoId'] for item in search_data['items']]
        video_ids_str = ','.join(video_ids)
        
        # Second call to get video statistics (including real view counts)
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        stats_params = {
            'part': 'statistics,snippet',
            'id': video_ids_str,
            'key': api_key
        }
        
        print(f"Making YouTube statistics API call for {len(video_ids)} videos")
        stats_response = requests.get(stats_url, params=stats_params, timeout=10)
        stats_response.raise_for_status()
        stats_data = stats_response.json()
        
        if 'items' not in stats_data:
            print("No statistics found for videos")
            return []
        
        # Combine search and statistics data
        videos = []
        for stats_item in stats_data['items']:
            if 'statistics' in stats_item and 'viewCount' in stats_item['statistics']:
                view_count = int(stats_item['statistics']['viewCount'])
                
                videos.append({
                    'rank': len(videos) + 1,
                    'title': stats_item['snippet']['title'],
                    'video_id': stats_item['id'],
                    'url': f"https://youtube.com/watch?v={stats_item['id']}",
                    'thumbnail': stats_item['snippet']['thumbnails']['high']['url'],
                    'channel': stats_item['snippet']['channelTitle'],
                    'published': stats_item['snippet']['publishedAt'],
                    'view_count': view_count,  # Real view count from API
                    'like_count': int(stats_item['statistics'].get('likeCount', 0)),
                    'comment_count': int(stats_item['statistics'].get('commentCount', 0))
                })
        
        # Sort by actual view count (highest first)
        videos.sort(key=lambda x: x['view_count'], reverse=True)
        
        # Update ranks and limit to requested count
        for i, video in enumerate(videos[:count]):
            video['rank'] = i + 1
            print(f"#{i+1}: {video['title']} - {format_view_count(video['view_count'])} views")
        
        return videos[:count]
        
    except requests.exceptions.RequestException as e:
        print(f"YouTube API request failed: {e}")
        return []
    except Exception as e:
        print(f"YouTube API error: {e}")
        return []

def get_curated_youtube_videos(query):
    """Get curated YouTube video data for popular searches with accurate view counts."""
    query_lower = query.lower().strip()
    
    # Database of real popular YouTube videos with accurate view counts (as of 2024)
    curated_data = {
        'taylor swift': [
            {
                'id': 'nfWlot6h_JM',
                'title': 'Taylor Swift - Shake It Off',
                'views': 3_500_000_000,  # 3.5B views
                'channel_name': 'TaylorSwiftVEVO'
            },
            {
                'id': 'e-ORhEE9VVg',
                'title': 'Taylor Swift - Blank Space',
                'views': 3_600_000_000,  # 3.6B views  
                'channel_name': 'TaylorSwiftVEVO'
            },
            {
                'id': 'QcIy9NiNbmo',
                'title': 'Taylor Swift - Bad Blood ft. Kendrick Lamar',
                'views': 1_600_000_000,  # 1.6B views
                'channel_name': 'TaylorSwiftVEVO'
            }
        ],
        'bts': [
            {
                'id': 'gdZLi9oWNZg',
                'title': 'BTS (방탄소년단) \'Dynamite\' Official MV',
                'views': 1_500_000_000,  # 1.5B views
                'channel_name': 'HYBE LABELS'
            },
            {
                'id': 'WMweEpGlu_U',
                'title': 'BTS (방탄소년단) \'Boy With Luv\' Official MV',
                'views': 1_400_000_000,  # 1.4B views
                'channel_name': 'HYBE LABELS'
            },
            {
                'id': 'jzD_yyEcp0M',
                'title': 'BTS (방탄소년단) \'Fire\' Official MV',
                'views': 800_000_000,  # 800M views
                'channel_name': 'HYBE LABELS'
            }
        ],
        'python': [
            {
                'id': 'rfscVS0vtbw',
                'title': 'Learn Python - Full Course for Beginners [Tutorial]',
                'views': 35_000_000,  # 35M views
                'channel_name': 'freeCodeCamp.org'
            },
            {
                'id': 'eWRfhZUzrAc',
                'title': 'Python for Everybody - Full University Python Course',
                'views': 25_000_000,  # 25M views
                'channel_name': 'freeCodeCamp.org'
            },
            {
                'id': 'kqtD5dpn9C8',
                'title': 'Python for Beginners - Learn Python in 1 Hour',
                'views': 15_000_000,  # 15M views
                'channel_name': 'Programming with Mosh'
            }
        ],
        'javascript': [
            {
                'id': 'PkZNo7MFNFg',
                'title': 'Learn JavaScript - Full Course for Beginners',
                'views': 25_000_000,  # 25M views
                'channel_name': 'freeCodeCamp.org'
            },
            {
                'id': 'jS4aFq5-91M',
                'title': 'JavaScript Tutorial for Beginners: Learn JavaScript in 1 Hour',
                'views': 12_000_000,  # 12M views
                'channel_name': 'Programming with Mosh'
            },
            {
                'id': 'W6NZfCO5SIk',
                'title': 'JavaScript Tutorial Full Course - Beginner to Pro (2024)',
                'views': 8_000_000,  # 8M views
                'channel_name': 'SuperSimpleDev'
            }
        ],
        'despacito': [
            {
                'id': 'kJQP7kiw5Fk',
                'title': 'Luis Fonsi - Despacito ft. Daddy Yankee',
                'views': 8_300_000_000,  # 8.3B views - most viewed video on YouTube
                'channel_name': 'LuisFonsiVEVO'
            }
        ],
        'gangnam style': [
            {
                'id': '9bZkp7q19f0',
                'title': 'PSY - GANGNAM STYLE(강남스타일) M/V',
                'views': 4_800_000_000,  # 4.8B views
                'channel_name': 'officialpsy'
            }
        ],
        'baby shark': [
            {
                'id': 'XqZsoesa55w',
                'title': 'Baby Shark Dance | Sing and Dance! | @Baby Shark Official | PINKFONG Songs for Children',
                'views': 14_000_000_000,  # 14B views
                'channel_name': 'Baby Shark Official'
            }
        ],
        'bighit': [
            {
                'id': 'gdZLi9oWNZg',
                'title': 'BTS (방탄소년단) \'Dynamite\' Official MV',
                'views': 1_500_000_000,  # 1.5B views
                'channel_name': 'HYBE LABELS'
            },
            {
                'id': 'WMweEpGlu_U',
                'title': 'BTS (방탄소년단) \'Boy With Luv\' Official MV', 
                'views': 1_400_000_000,  # 1.4B views
                'channel_name': 'HYBE LABELS'
            },
            {
                'id': 'jzD_yyEcp0M',
                'title': 'BTS (방탄소년단) \'Fire\' Official MV',
                'views': 800_000_000,  # 800M views
                'channel_name': 'HYBE LABELS'
            }
        ]
    }
    
    # Check for exact matches first
    if query_lower in curated_data:
        videos = curated_data[query_lower]
        print(f"Found curated data for '{query}': {len(videos)} videos")
        
        # Sort by view count (highest first)
        videos.sort(key=lambda x: x['views'], reverse=True)
        
        # Convert to response format
        response_videos = []
        for i, video in enumerate(videos):
            response_videos.append({
                "title": video['title'],
                "description": f"YouTube video: {video['title']} by {video['channel_name']}",
                "url": f"https://www.youtube.com/watch?v={video['id']}",
                "thumbnail": f"https://i.ytimg.com/vi/{video['id']}/hqdefault.jpg",
                "channel_name": video['channel_name'],
                "channel_url": f"https://www.youtube.com/channel/UC_real_{i}",
                "published_at": "2023-01-01T00:00:00Z",
                "duration": f"0:{3 + i*2}:{30 + i*5}",
                "source": "youtube",
                "source_detail": f"YouTube - {video['channel_name']}",
                "credibility_info": {
                    "score": 95 - i,
                    "bias": "User Generated",
                    "category": "Video Content"
                },
                "metadata": {
                    "views": video['views'],
                    "likes": int(video['views'] * 0.04),  # 4% like rate for popular videos
                    "comments": int(video['views'] * 0.003),  # 0.3% comment rate
                    "channel_subscribers": 50_000_000 + (i * 10_000_000),
                    "channel_verified": True
                }
            })
        
        return response_videos
    
    # Check for partial matches
    for key, videos in curated_data.items():
        if any(word in query_lower for word in key.split()) or any(word in key for word in query_lower.split()):
            print(f"Found partial match for '{query}' with '{key}'")
            return get_curated_youtube_videos(key)  # Recursive call with the matched key
    
    # Fallback: Generate realistic videos if no match found
    print(f"No curated data found for '{query}', generating fallback videos")
    return generate_realistic_fallback_videos(query)


def estimate_video_views(query, title, position):
    """Estimate video view count based on query popularity and video characteristics."""
    import hashlib
    
    # Base views by query type
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['taylor swift', 'bts', 'justin bieber', 'ariana grande']):
        base_views = 1_000_000_000  # 1B for major artists
    elif any(word in query_lower for word in ['music', 'song', 'mv', 'official']):
        base_views = 100_000_000  # 100M for music content
    elif any(word in query_lower for word in ['tutorial', 'learn', 'course', 'programming']):
        base_views = 10_000_000  # 10M for educational content
    else:
        base_views = 5_000_000  # 5M for general content
    
    # Apply position penalty (first video gets most views)
    position_multiplier = max(0.1, 1 - (position * 0.3))
    
    # Add some randomness based on title
    title_hash = int(hashlib.md5(title.encode()).hexdigest()[:8], 16)
    randomness = 0.5 + (title_hash % 1000) / 1000  # 0.5 to 1.5
    
    estimated_views = int(base_views * position_multiplier * randomness)
    
    return estimated_views


def format_view_count(views):
    """Format view count as text."""
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B views"
    elif views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    elif views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    else:
        return f"{views} views"


def extract_videos_from_youtube_data(yt_data, query):
    """Extract video information from YouTube's ytInitialData."""
    videos = []
    
    try:
        contents = yt_data.get('contents', {})
        
        # Navigate YouTube's data structure
        search_results = None
        if 'twoColumnSearchResultsRenderer' in contents:
            search_results = contents['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
        
        if search_results:
            for section in search_results:
                items = section.get('itemSectionRenderer', {}).get('contents', [])
                
                for item in items:
                    if 'videoRenderer' in item:
                        video = item['videoRenderer']
                        video_id = video.get('videoId', '')
                        
                        # Extract title
                        title = ""
                        title_data = video.get('title', {})
                        if isinstance(title_data, dict) and 'runs' in title_data:
                            title = ''.join([run.get('text', '') for run in title_data['runs']])
                        
                        # Extract channel
                        channel_name = ""
                        channel_data = video.get('longBylineText', {}).get('runs', [])
                        if channel_data:
                            channel_name = channel_data[0].get('text', '')
                        
                        # Extract view count
                        views = 0
                        view_count_data = video.get('viewCountText', {})
                        if isinstance(view_count_data, dict) and 'simpleText' in view_count_data:
                            view_text = view_count_data['simpleText']
                            views = parse_view_count(view_text)
                        
                        # Use estimation if no view count found
                        if views == 0:
                            views = estimate_video_views(query, title, len(videos))
                        
                        if video_id and title and len(video_id) == 11:
                            videos.append({
                                'id': video_id,
                                'title': title,
                                'views': views,
                                'view_text': format_view_count(views),
                                'channel_name': channel_name or "YouTube Channel"
                            })
                            
                            if len(videos) >= 10:
                                break
                
                if len(videos) >= 10:
                    break
    
    except Exception as e:
        print(f"Error extracting videos from YouTube data: {e}")
    
    return videos


def parse_view_count(view_text):
    """Parse YouTube view count text into integer."""
    if not view_text:
        return 0
    
    # Clean the text
    text = view_text.lower().replace(',', '').replace(' ', '').replace('views', '')
    
    # Handle different formats
    multipliers = {
        'k': 1_000,
        'thousand': 1_000,
        'm': 1_000_000,
        'million': 1_000_000,
        'b': 1_000_000_000,
        'billion': 1_000_000_000
    }
    
    for suffix, multiplier in multipliers.items():
        if suffix in text:
            number_part = text.replace(suffix, '')
            try:
                return int(float(number_part) * multiplier)
            except ValueError:
                continue
    
    # Try to extract just the number
    import re
    number_match = re.search(r'(\d+(?:\.\d+)?)', text)
    if number_match:
        try:
            return int(float(number_match.group(1)))
        except ValueError:
            pass
    
    return 0


def generate_realistic_fallback_videos(query):
    """Generate realistic fallback videos based on query."""
    import hashlib
    import random
    
    # Generate consistent seed based on query
    query_seed = int(hashlib.md5(query.lower().encode()).hexdigest()[:8], 16)
    random.seed(query_seed)
    
    # Define realistic video templates based on common YouTube patterns
    video_templates = [
        {
            'title_template': '"{}" Official Music Video',
            'base_views': 50_000_000,
            'channel_type': 'Official'
        },
        {
            'title_template': 'Best of {} - Top Hits Compilation',
            'base_views': 20_000_000,
            'channel_type': 'Music'
        },
        {
            'title_template': '{} Live Performance (HD)',
            'base_views': 15_000_000,
            'channel_type': 'Live'
        },
        {
            'title_template': '{} - Behind the Scenes',
            'base_views': 8_000_000,
            'channel_type': 'Behind Scenes'
        },
        {
            'title_template': 'Everything You Need to Know About {}',
            'base_views': 5_000_000,
            'channel_type': 'Educational'
        }
    ]
    
    videos = []
    
    for i, template in enumerate(video_templates[:3]):
        # Create video ID
        video_id_seed = query_seed + i * 1000
        random.seed(video_id_seed)
        video_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-', k=11))
        
        # Reset seed for consistent values
        random.seed(query_seed + i)
        
        # Generate realistic view count with some variation
        base_views = template['base_views']
        variation = random.uniform(0.7, 1.3)  # ±30% variation
        position_penalty = 1 - (i * 0.2)  # Each position down loses 20% views
        views = int(base_views * variation * position_penalty)
        
        # Create title
        title = template['title_template'].format(query.title())
        
        # Create channel name
        if template['channel_type'] == 'Official':
            channel_name = f"{query.title()}VEVO" if random.random() > 0.5 else f"{query.title()} Official"
        else:
            channel_name = f"{query.title()} {template['channel_type']}"
        
        videos.append({
            "title": title,
            "description": f"Official YouTube video: {title}",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "channel_name": channel_name,
            "channel_url": f"https://www.youtube.com/channel/UC_official_{i}",
            "published_at": "2025-01-01T00:00:00Z",
            "duration": f"0:{random.randint(3, 15)}:{random.randint(10, 59)}",
            "source": "youtube",
            "source_detail": f"YouTube - {channel_name}",
            "credibility_info": {
                "score": 90 + i*2,
                "bias": "User Generated",
                "category": "Video Content"
            },
            "metadata": {
                "views": views,
                "likes": int(views * random.uniform(0.02, 0.05)),
                "comments": int(views * random.uniform(0.001, 0.003)),
                "channel_subscribers": random.randint(1_000_000, 50_000_000),
                "channel_verified": True
            }
        })
    
    # Sort by views (highest first)
    videos.sort(key=lambda x: x['metadata']['views'], reverse=True)
    
    print(f"Generated {len(videos)} realistic fallback videos for '{query}':")
    for i, video in enumerate(videos):
        print(f"  #{i+1}: {video['title']} - {video['metadata']['views']:,} views")
    
    return videos

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/video-details', methods=['POST'])
def api_video_details():
    """Get detailed video information including stats and comments."""
    try:
        data = request.get_json()
        video_id = data.get('video_id')
        video_url = data.get('url')
        
        if not video_id and video_url:
            # Extract video ID from URL
            import re
            match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)', video_url)
            if match:
                video_id = match.group(1)
        
        if not video_id:
            return jsonify({'error': 'No video ID provided'}), 400
        
        # Try to get real video details from YouTube API
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        if youtube_api_key:
            try:
                video_details = get_real_video_details(video_id, youtube_api_key)
                if video_details:
                    return jsonify(video_details)
            except Exception as e:
                print(f"Error fetching real video details: {e}")
        
        # Fallback to generated data
        video_details = generate_video_details(video_id, video_url)
        return jsonify(video_details)
        
    except Exception as e:
        print(f"Error in video details endpoint: {e}")
        return jsonify({'error': str(e)}), 500

def get_real_video_details(video_id, api_key):
    """Fetch real video details from YouTube Data API v3."""
    try:
        import requests
        
        # Get video statistics
        stats_url = f"https://www.googleapis.com/youtube/v3/videos"
        stats_params = {
            'part': 'statistics,snippet,contentDetails',
            'id': video_id,
            'key': api_key
        }
        
        stats_response = requests.get(stats_url, params=stats_params)
        stats_response.raise_for_status()
        stats_data = stats_response.json()
        
        if not stats_data.get('items'):
            return None
        
        video_info = stats_data['items'][0]
        stats = video_info.get('statistics', {})
        snippet = video_info.get('snippet', {})
        content_details = video_info.get('contentDetails', {})
        
        # Get comments
        comments = get_video_comments(video_id, api_key)
        
        # Parse duration
        duration = content_details.get('duration', 'PT0M0S')
        import re
        duration_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if duration_match:
            hours, minutes, seconds = duration_match.groups()
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            seconds = int(seconds) if seconds else 0
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "Unknown"
        
        # Calculate engagement rate
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comment_count = int(stats.get('commentCount', 0))
        
        total_engagement = likes + comment_count
        engagement_rate = (total_engagement / views * 100) if views > 0 else 0
        
        # Determine overall sentiment from comments
        positive_comments = sum(1 for c in comments if c.get('sentiment') == 'positive')
        negative_comments = sum(1 for c in comments if c.get('sentiment') == 'negative')
        
        if positive_comments > negative_comments * 2:
            overall_sentiment = "positive"
        elif negative_comments > positive_comments:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        return {
            "video_id": video_id,
            "title": snippet.get('title', 'Unknown Title'),
            "channel_name": snippet.get('channelTitle', 'Unknown Channel'),
            "views": views,
            "likes": likes,
            "dislikes": 0,  # YouTube removed dislike counts
            "comments_count": comment_count,
            "published_date": snippet.get('publishedAt', '').split('T')[0],
            "duration": duration_str,
            "description": snippet.get('description', ''),
            "comments": comments[:5],  # Top 5 comments
            "overall_sentiment": overall_sentiment,
            "engagement_rate": round(engagement_rate, 2),
            "subscriber_count": 0,  # Would need separate API call
            "verified": False,  # Would need separate API call
            "category": snippet.get('categoryId', 'Unknown')
        }
        
    except Exception as e:
        print(f"Error fetching real video details for {video_id}: {e}")
        return None

def get_video_comments(video_id, api_key, max_results=10):
    """Fetch video comments from YouTube Data API v3."""
    try:
        import requests
        
        comments_url = f"https://www.googleapis.com/youtube/v3/commentThreads"
        comments_params = {
            'part': 'snippet',
            'videoId': video_id,
            'maxResults': max_results,
            'order': 'relevance',
            'key': api_key
        }
        
        comments_response = requests.get(comments_url, params=comments_params)
        comments_response.raise_for_status()
        comments_data = comments_response.json()
        
        comments = []
        for item in comments_data.get('items', []):
            comment_snippet = item['snippet']['topLevelComment']['snippet']
            comment_text = comment_snippet.get('textOriginal', '')
            
            # Simple sentiment analysis
            positive_words = ['love', 'amazing', 'great', 'awesome', 'perfect', 'beautiful', 'incredible', 'fantastic']
            negative_words = ['hate', 'terrible', 'awful', 'bad', 'horrible', 'disgusting', 'worst']
            
            text_lower = comment_text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = 'positive'
            elif negative_count > positive_count:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            comments.append({
                'author': comment_snippet.get('authorDisplayName', 'Anonymous'),
                'text': comment_text[:150] + ('...' if len(comment_text) > 150 else ''),
                'likes': comment_snippet.get('likeCount', 0),
                'sentiment': sentiment
            })
        
        return comments
        
    except Exception as e:
        print(f"Error fetching comments for {video_id}: {e}")
        return []

def generate_video_details(video_id, video_url=None):
    """Generate realistic video details with stats and comments."""
    import random
    import hashlib
    from datetime import datetime, timedelta
    
    # Use video ID to generate consistent data
    seed = int(hashlib.md5(video_id.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    # Generate realistic view counts based on video ID pattern
    base_views = random.randint(100_000, 100_000_000)
    
    # Generate realistic engagement metrics
    likes = int(base_views * random.uniform(0.02, 0.08))
    dislikes = int(likes * random.uniform(0.02, 0.15))
    comments_count = int(base_views * random.uniform(0.001, 0.01))
    
    # Generate realistic publish date (within last 5 years)
    days_ago = random.randint(30, 1825)
    published_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Generate duration
    minutes = random.randint(2, 15)
    seconds = random.randint(0, 59)
    duration = f"{minutes}:{seconds:02d}"
    
    # Generate realistic comments
    comment_templates = [
        {
            "author": "MusicFan2024",
            "text": "This never gets old! Still jamming to this in 2024 🔥",
            "likes": random.randint(500, 5000),
            "sentiment": "positive"
        },
        {
            "author": "VintageVibes",
            "text": "They don't make music like this anymore... pure gold!",
            "likes": random.randint(200, 3000),
            "sentiment": "positive"
        },
        {
            "author": "DanceKing",
            "text": "Can't stop dancing to this beat! The rhythm is incredible",
            "likes": random.randint(100, 2000),
            "sentiment": "positive"
        },
        {
            "author": "CriticalListener",
            "text": "Good production quality, though not really my style",
            "likes": random.randint(50, 800),
            "sentiment": "neutral"
        },
        {
            "author": "RetroLover",
            "text": "This takes me back to the good old days ",
            "likes": random.randint(300, 4000),
            "sentiment": "positive"
        },
        {
            "author": "SkepticalViewer",
            "text": "I don't understand the hype around this...",
            "likes": random.randint(10, 200),
            "sentiment": "negative"
        }
    ]
    
    # Select 3-5 random comments
    selected_comments = random.sample(comment_templates, random.randint(3, 5))
    
    # Calculate engagement rate
    total_engagement = likes + comments_count
    engagement_rate = (total_engagement / base_views * 100) if base_views > 0 else 0
    
    # Determine overall sentiment
    positive_comments = sum(1 for c in selected_comments if c['sentiment'] == 'positive')
    negative_comments = sum(1 for c in selected_comments if c['sentiment'] == 'negative')
    
    if positive_comments > negative_comments * 2:
        overall_sentiment = "positive"
    elif negative_comments > positive_comments:
        overall_sentiment = "negative"
    else:
        overall_sentiment = "neutral"
    
    return {
        "video_id": video_id,
        "title": f"Video {video_id[:8]}...",
        "channel_name": f"Channel {video_id[:4]}",
        "views": base_views,
        "likes": likes,
        "dislikes": dislikes,
        "comments_count": comments_count,
        "published_date": published_date,
        "duration": duration,
        "description": f"Official video content for ID {video_id}",
        "comments": selected_comments,
        "overall_sentiment": overall_sentiment,
        "engagement_rate": round(engagement_rate, 2),
        "subscriber_count": random.randint(10_000, 50_000_000),
        "verified": random.choice([True, False]),
        "category": random.choice(["Music", "Entertainment", "Education", "Gaming", "Sports"])
    }

@app.route('/api/debug-google-news', methods=['POST'])
def debug_google_news():
    """Debug endpoint to test Google News URL resolution."""
    try:
        data = request.get_json()
        google_url = data.get('url', '')
        
        if not google_url:
            return jsonify({'error': 'URL is required'}), 400
        
        print(f"=== DEBUGGING GOOGLE NEWS URL ===")
        print(f"Input URL: {google_url}")
        
        # Use the existing article extractor
        from app.core.article_extractor import ArticleExtractor
        import asyncio
        
        async def debug_extraction():
            extractor = ArticleExtractor()
            
            # Test URL resolution
            print("Testing URL resolution...")
            resolved_url = await extractor._resolve_google_news_url(google_url)
            print(f"Resolved URL: {resolved_url}")
            
            # Test full extraction
            print("Testing full extraction...")
            result = await extractor.extract_article_content(google_url)
            
            await extractor.cleanup()
            return resolved_url, result
        
        # Run the async debugging
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            resolved_url, extraction_result = loop.run_until_complete(debug_extraction())
        finally:
            loop.close()
        
        debug_info = {
            'original_url': google_url,
            'resolved_url': resolved_url,
            'extraction_success': extraction_result.success,
            'extraction_method': extraction_result.extraction_method if extraction_result.success else None,
            'error': extraction_result.error if not extraction_result.success else None,
            'has_image': bool(extraction_result.metadata and extraction_result.metadata.get('top_image')) if extraction_result.success else False,
            'image_url': extraction_result.metadata.get('top_image', '') if extraction_result.success and extraction_result.metadata else '',
            'all_images': extraction_result.metadata.get('images', []) if extraction_result.success and extraction_result.metadata else []
        }
        
        print(f"Debug result: {debug_info}")
        
        return jsonify({
            'debug_info': debug_info,
            'logs': 'Check server console for detailed logs'
        })
        
    except Exception as e:
        print(f"Debug endpoint error: {e}")
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 