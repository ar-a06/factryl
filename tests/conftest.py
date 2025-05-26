"""
Global pytest fixtures and configurations.
"""

import pytest
import pytest_asyncio
import os
import sys
import json
import asyncio
from typing import Dict, Any
from unittest.mock import MagicMock

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scrapers
from app.scraper.blogs.blog import BlogScraper
from app.scraper.weather.weather import WeatherScraper
from app.scraper.news import NewsScraper
from app.scraper.media.youtube import YouTubeScraper

@pytest.fixture(scope="session")
def base_config() -> Dict[str, Any]:
    """Base configuration for all scrapers."""
    return {
        'cache': {
            'enabled': False,  # Disable Redis cache for testing
            'host': 'localhost',
            'port': 6379,
            'ttl': 3600
        },
        'scraping': {
            'max_total_articles': 5,  # Limit articles for testing
            'min_credibility_score': 85,
            'rate_limit': {
                'requests_per_minute': 30,
                'concurrent_requests': 3
            }
        },
        'apis': {
            'openweathermap': {
                'base_url': 'https://api.openweathermap.org/data/2.5',
                'units': 'metric'
            },
            'weatherapi': {
                'base_url': 'https://api.weatherapi.com/v1',
                'days': 3
            },
            'youtube': {
                'base_url': 'https://www.googleapis.com/youtube/v3',
                'max_results': 10
            }
        }
    }

@pytest.fixture(scope="session")
def test_queries() -> Dict[str, list]:
    """Common test queries for scrapers."""
    return {
        'blog': [
            "artificial intelligence latest developments",
            "machine learning trends",
            "data science best practices"
        ],
        'news': [
            "climate change impact",
            "renewable energy developments",
            "technology innovations"
        ],
        'weather': [
            "London,UK",
            "New York,US",
            "Tokyo,JP"
        ],
        'youtube': [
            "space exploration news",
            "quantum computing explained",
            "sustainable technology"
        ]
    }

@pytest.fixture(scope="session")
def mock_responses() -> Dict[str, str]:
    """Mock API responses for testing."""
    return {
        'blog': {
            'success': json.dumps({
                'items': [
                    {
                        'title': 'Test Blog Post',
                        'author': 'Test Author',
                        'content': 'Test Content',
                        'url': 'https://test.com/blog'
                    }
                ]
            }),
            'error': '{"error": "Not found"}'
        },
        'weather': {
            'openweathermap': json.dumps({
                'main': {'temp': 20},
                'weather': [{'description': 'clear sky'}]
            }),
            'weatherapi': json.dumps({
                'current': {
                    'temp_c': 20,
                    'condition': {'text': 'Clear'}
                }
            })
        },
        'news': {
            'success': json.dumps({
                'articles': [
                    {
                        'title': 'Climate Change Impact on Global Weather Patterns',
                        'url': 'https://test.com/news',
                        'source': {'name': 'Test Source'},
                        'publishedAt': '2024-03-20T12:00:00Z',
                        'description': 'Test news content about climate change'
                    }
                ]
            })
        }
    }

@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_http_response():
    """Mock HTTP response for testing."""
    class MockResponse:
        def __init__(self, text="", status=200, json_data=None):
            self._text = text
            self.status = status
            self._json = json_data
        
        async def text(self):
            return self._text
            
        async def json(self):
            return self._json if self._json else json.loads(self._text)
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    return MockResponse

@pytest.fixture
def mock_aiohttp_client(mock_http_response):
    """Mock aiohttp client for testing."""
    class MockClientSession:
        def __init__(self):
            self.response = mock_http_response()
            
        def get(self, url, **kwargs):
            """Return a context manager that yields the response."""
            return self.response
            
        async def close(self):
            pass
    
    return MockClientSession

@pytest_asyncio.fixture
async def mock_blog_scraper(base_config, mock_aiohttp_client):
    """Create a mock blog scraper instance."""
    scraper = BlogScraper(base_config)
    scraper.session = mock_aiohttp_client()
    yield scraper
    await scraper.close()

@pytest_asyncio.fixture
async def mock_weather_scraper(base_config, mock_aiohttp_client):
    """Create a mock weather scraper instance."""
    scraper = WeatherScraper(base_config)
    scraper.session = mock_aiohttp_client()
    yield scraper
    await scraper.close()

@pytest_asyncio.fixture
async def mock_news_scraper(base_config, mock_aiohttp_client):
    """Create a mock news scraper instance."""
    scraper = NewsScraper(base_config)
    scraper.session = mock_aiohttp_client()
    yield scraper
    await scraper.close()

@pytest_asyncio.fixture
async def mock_youtube_scraper(base_config, mock_aiohttp_client):
    """Create a mock youtube scraper instance."""
    scraper = YouTubeScraper(base_config)
    scraper.session = mock_aiohttp_client()
    yield scraper
    await scraper.close() 