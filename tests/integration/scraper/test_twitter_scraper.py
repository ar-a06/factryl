"""
Integration tests for Twitter scraper.
"""

import pytest
from app.scraper.social.twitter import TwitterScraper

@pytest.fixture
async def scraper():
    """Fixture to create and cleanup a Twitter scraper instance."""
    config = {
        'twitter': {
            'max_tweets': 10,
            'min_likes': 50,
            'time_filter': 'week',
            'include_replies': False,
            'min_credibility': 70
        },
        'cache': {
            'enabled': False  # Disable caching for testing
        }
    }
    
    scraper = TwitterScraper(config)
    yield scraper
    await scraper.close()

@pytest.mark.asyncio
async def test_scraper_validation(scraper):
    """Test that the scraper can validate its configuration."""
    is_valid = await scraper.validate()
    assert is_valid, "Scraper validation failed"

@pytest.mark.asyncio
async def test_scraper_search(scraper):
    """Test that the scraper can search and return results."""
    query = "artificial intelligence ethics"
    results = await scraper.scrape(query)
    
    assert isinstance(results, list), "Results should be a list"
    assert len(results) > 0, "Should find at least one result"
    
    # Validate result structure
    for result in results:
        assert 'title' in result, "Result should have a title"
        assert 'source_detail' in result, "Result should have source details"
        assert 'url' in result, "Result should have a URL"
        assert 'metadata' in result, "Result should have metadata"
        assert 'likes' in result['metadata'], "Result should have like count"
        assert 'retweets' in result['metadata'], "Result should have retweet count"

@pytest.mark.asyncio
async def test_scraper_empty_query(scraper):
    """Test that the scraper handles empty queries gracefully."""
    results = await scraper.scrape("")
    assert isinstance(results, list), "Should return empty list for empty query"
    assert len(results) == 0, "Should not find results for empty query" 