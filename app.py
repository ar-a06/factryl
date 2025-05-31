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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.factryl_engine import FactrylEngine

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'factryl_secret_key_2024'

# Initialize the Factryl Engine
print("Starting Factryl Infometrics Web Application...")
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
        max_results = data.get('max_results', 25)
        
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
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        query = data['query'].strip()
        
        if not query:
            return jsonify({'error': 'Empty query'}), 400
        
        print(f"Image search request: '{query}'")
        
        import requests
        from urllib.parse import quote_plus
        import re
        
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
                    r'"(https://[^"]*\.(?:jpg|jpeg|png|webp)(?:\?[^"]*)?)"',
                    r'imgurl=(https://[^&]*\.(?:jpg|jpeg|png|webp)(?:\?[^&]*)?)',
                    r'"ou":"(https://[^"]*\.(?:jpg|jpeg|png|webp)(?:\?[^"]*)?)"'
                ]
                
                found_images = []
                for pattern in img_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Clean up the URL
                        img_url = match.replace('\\u003d', '=').replace('\\u0026', '&')
                        
                        # Filter criteria
                        if (len(img_url) > 30 and 
                            'gstatic' not in img_url and 
                            'googleusercontent' not in img_url and
                            'google.com' not in img_url and
                            not img_url.endswith('.gif')):
                            found_images.append(img_url)
                
                # Try to use the first good image found
                for img_url in found_images[:3]:  # Try first 3 images
                    try:
                        print(f"Testing image URL: {img_url[:80]}...")
                        
                        # Test if image is accessible
                        img_response = requests.head(img_url, timeout=3, headers=headers, allow_redirects=True)
                        if img_response.status_code == 200:
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
                        first_result = data['results'][0]
                        img_url = first_result.get('image')
                        
                        if img_url:
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
                
                for match in matches[:3]:  # Try first 3 images
                    try:
                        # Decode URL if needed
                        img_url = match.replace('\\u002f', '/')
                        
                        # Test if image is accessible
                        img_response = requests.head(img_url, timeout=3)
                        if img_response.status_code == 200:
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
async def youtube_videos():
    """Fetch YouTube videos for the search query."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        logger.info(f"YouTube video search request: '{query}'")
        
        # For now, use mock data based on existing structure
        # TODO: Integrate with actual YouTube API when available
        mock_videos = [
            {
                "title": f"Physics Explained: {query.title()} Fundamentals",
                "description": f"Comprehensive guide to understanding {query} with clear explanations and visual demonstrations.",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                "channel_name": "Physics World",
                "channel_url": "https://www.youtube.com/channel/UC_physics_world",
                "published_at": "2025-05-20T18:45:22Z",
                "duration": "0:12:45",
                "source": "youtube",
                "source_detail": "YouTube - Physics World",
                "credibility_info": {
                    "score": 95,
                    "bias": "Educational",
                    "category": "Educational Content"
                },
                "metadata": {
                    "views": 1250000,
                    "likes": 45000,
                    "comments": 3200,
                    "channel_subscribers": 2100000,
                    "channel_verified": true
                }
            },
            {
                "title": f"Advanced {query.title()} Concepts",
                "description": f"Deep dive into advanced concepts in {query} for students and researchers.",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                "channel_name": "MIT OpenCourseWare",
                "channel_url": "https://www.youtube.com/channel/UC_mit_opencourse",
                "published_at": "2025-05-19T14:30:15Z",
                "duration": "0:25:30",
                "source": "youtube",
                "source_detail": "YouTube - MIT OpenCourseWare",
                "credibility_info": {
                    "score": 98,
                    "bias": "Academic",
                    "category": "Educational Content"
                },
                "metadata": {
                    "views": 890000,
                    "likes": 32000,
                    "comments": 1800,
                    "channel_subscribers": 5400000,
                    "channel_verified": true
                }
            },
            {
                "title": f"{query.title()} in 10 Minutes",
                "description": f"Quick overview of key {query} principles and applications.",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
                "channel_name": "SciShow",
                "channel_url": "https://www.youtube.com/channel/UC_scishow",
                "published_at": "2025-05-18T12:15:30Z",
                "duration": "0:10:22",
                "source": "youtube",
                "source_detail": "YouTube - SciShow",
                "credibility_info": {
                    "score": 92,
                    "bias": "Popular Science",
                    "category": "Educational Content"
                },
                "metadata": {
                    "views": 567000,
                    "likes": 28000,
                    "comments": 950,
                    "channel_subscribers": 7200000,
                    "channel_verified": true
                }
            }
        ]
        
        # Sort by views (most viewed first)
        sorted_videos = sorted(mock_videos, key=lambda x: x['metadata']['views'], reverse=True)
        
        return jsonify({
            'videos': sorted_videos,
            'total': len(sorted_videos),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"YouTube video search error: {str(e)}")
        return jsonify({'error': 'Failed to fetch videos'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 