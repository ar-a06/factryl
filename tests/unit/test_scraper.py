"""
Unit tests for scrapers.
"""

import pytest
import pytest_asyncio
import json
import os
from unittest.mock import patch, MagicMock
import aiohttp
from datetime import datetime

from app.scraper.blogs.blog import BlogScraper
from app.scraper.weather.weather import WeatherScraper
from app.scraper.news import NewsScraper
from app.scraper.media.youtube import YouTubeScraper

# Load test configuration
@pytest.fixture
def config():
    with open('config/config.json', 'r') as f:
        return json.load(f)

@pytest_asyncio.fixture
async def blog_scraper(config):
    """Create a blog scraper instance."""
    scraper = BlogScraper(config)
    yield scraper
    await scraper.close()

@pytest_asyncio.fixture
async def weather_scraper(config):
    """Create a weather scraper instance."""
    scraper = WeatherScraper(config)
    yield scraper
    await scraper.close()

@pytest_asyncio.fixture
async def news_scraper(config):
    """Create a news scraper instance."""
    scraper = NewsScraper(config)
    yield scraper
    await scraper.close()

@pytest_asyncio.fixture
async def youtube_scraper(config):
    """Create a YouTube scraper instance."""
    scraper = YouTubeScraper(config)
    yield scraper
    await scraper.close()

@pytest.mark.asyncio
class TestScrapers:
    """Test suite for all scrapers."""

    async def test_blog_scraper_success(self, mock_blog_scraper, mock_responses, test_queries):
        """Test successful blog scraping."""
        # Set up mock response
        mock_blog_scraper.session.response._text = mock_responses['blog']['success']
        mock_blog_scraper.session.response.status = 200
        
        # Test with valid query
        results = await mock_blog_scraper.scrape(test_queries['blog'][0])
        
        assert isinstance(results, list)
        assert len(results) > 0
        result = results[0]
        assert 'title' in result
        assert 'url' in result
        assert 'author' in result
        assert 'content' in result

    async def test_blog_scraper_error(self, mock_blog_scraper, mock_responses):
        """Test blog scraper error handling."""
        # Set up error response
        mock_blog_scraper.session.response._text = mock_responses['blog']['error']
        mock_blog_scraper.session.response.status = 404
        
        results = await mock_blog_scraper.scrape("test query")
        assert isinstance(results, list)
        assert len(results) == 0

    async def test_weather_scraper_success(self, mock_weather_scraper, mock_responses, test_queries):
        """Test successful weather scraping."""
        # Set up mock responses for both providers
        mock_weather_scraper.session.response._json = json.loads(mock_responses['weather']['openweathermap'])
        mock_weather_scraper.session.response.status = 200
        
        results = await mock_weather_scraper.scrape(test_queries['weather'][0])
        
        assert isinstance(results, list)
        assert len(results) > 0
        for result in results:
            assert 'provider' in result
            assert 'location' in result
            assert 'current' in result
            assert 'timestamp' in result

    async def test_weather_scraper_invalid_location(self, mock_weather_scraper):
        """Test weather scraper with invalid location."""
        mock_weather_scraper.session.response.status = 404
        
        results = await mock_weather_scraper.scrape("InvalidCity123,XX")
        assert isinstance(results, list)
        assert len(results) == 0

    async def test_news_scraper_success(self, mock_news_scraper, mock_responses, test_queries):
        """Test successful news scraping."""
        # Set up mock response
        mock_news_scraper.session.response._text = mock_responses['news']['success']
        mock_news_scraper.session.response.status = 200
        
        results = await mock_news_scraper.scrape(test_queries['news'][0])
        
        assert isinstance(results, list)
        assert len(results) > 0
        result = results[0]
        assert 'title' in result
        assert 'url' in result
        assert 'source' in result

    async def test_youtube_scraper_success(self, mock_youtube_scraper, test_queries):
        """Test successful YouTube scraping."""
        # Set up mock response
        mock_youtube_scraper.session.response._json = {
            'items': [
                {
                    'snippet': {
                        'title': 'Test Video',
                        'channelTitle': 'Test Channel'
                    },
                    'id': {'videoId': '12345'},
                    'statistics': {'viewCount': '1000'}
                }
            ]
        }
        mock_youtube_scraper.session.response.status = 200
        
        results = await mock_youtube_scraper.scrape(test_queries['youtube'][0])
        
        assert isinstance(results, list)
        assert len(results) > 0
        result = results[0]
        assert 'title' in result
        assert 'url' in result
        assert 'channel' in result
        assert 'views' in result

    async def test_rate_limiting(self, mock_blog_scraper):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        start_time = pytest.importorskip("datetime").datetime.now()
        
        for _ in range(3):
            await mock_blog_scraper.scrape("test query")
            
        duration = (pytest.importorskip("datetime").datetime.now() - start_time).total_seconds()
        assert duration >= 1.0  # At least 1 second for rate limiting

    async def test_error_handling(self, mock_blog_scraper, mock_weather_scraper, 
                                mock_news_scraper, mock_youtube_scraper):
        """Test error handling in scrapers."""
        # Simulate network error
        mock_blog_scraper.session.response.status = 500
        mock_weather_scraper.session.response.status = 500
        mock_news_scraper.session.response.status = 500
        mock_youtube_scraper.session.response.status = 500
        
        # Test all scrapers with error condition
        scrapers = [
            (mock_blog_scraper, "test query"),
            (mock_weather_scraper, "London,UK"),
            (mock_news_scraper, "test news"),
            (mock_youtube_scraper, "test video")
        ]
        
        for scraper, query in scrapers:
            results = await scraper.scrape(query)
            assert isinstance(results, list)
            assert len(results) == 0  # Should return empty list on error
