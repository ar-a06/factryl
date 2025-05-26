"""
Integration tests for social media scraper.
"""

import pytest
from app.scraper.social import SocialScraper

@pytest.fixture
async def scraper():
    """Fixture to create and cleanup a social media scraper instance."""
    config = {
        'social': {
            'platforms': ['linkedin', 'facebook'],
            'max_posts': 5,  # Reduced for testing
            'min_engagement': 10,  # Lower threshold for testing
            'time_filter': 'week',
            'min_credibility': 60
        },
        'cache': {
            'enabled': False
        }
    }
    
    scraper = SocialScraper(config)
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
        assert 'content' in result, "Result should have content"
        assert 'author' in result, "Result should have an author"
        assert 'url' in result, "Result should have a URL"
        assert 'source' in result, "Result should have a source"
        assert result['source'] in ['linkedin', 'facebook'], "Source should be LinkedIn or Facebook"
        assert 'credibility_info' in result, "Result should have credibility info"
        assert 'metadata' in result, "Result should have metadata"
        assert 'likes' in result['metadata'], "Result should have like count"
        assert 'comments' in result['metadata'], "Result should have comment count"

@pytest.mark.asyncio
async def test_platform_filtering(scraper):
    """Test that platform filtering works."""
    # Test LinkedIn only
    scraper.platforms = ['linkedin']
    results = await scraper.scrape("technology")
    assert all(r['source'] == 'linkedin' for r in results), "Should only return LinkedIn results"
    
    # Test Facebook only
    scraper.platforms = ['facebook']
    results = await scraper.scrape("technology")
    assert all(r['source'] == 'facebook' for r in results), "Should only return Facebook results"

@pytest.mark.asyncio
async def test_credibility_filtering(scraper):
    """Test that credibility filtering works."""
    scraper.min_credibility = 80
    results = await scraper.scrape("news")
    
    for result in results:
        assert result['credibility_info']['score'] >= 80, "All results should meet minimum credibility"

@pytest.mark.asyncio
async def test_engagement_filtering(scraper):
    """Test that engagement filtering works."""
    scraper.min_engagement = 100
    results = await scraper.scrape("viral")
    
    for result in results:
        total_engagement = (
            result['metadata']['likes'] +
            result['metadata']['comments'] +
            result.get('metadata', {}).get('shares', 0)
        )
        assert total_engagement >= 100, "All results should meet minimum engagement"

@pytest.mark.asyncio
async def test_empty_query(scraper):
    """Test that the scraper handles empty queries gracefully."""
    results = await scraper.scrape("")
    assert isinstance(results, list), "Should return empty list for empty query"
    assert len(results) == 0, "Should not find results for empty query"

@pytest.mark.asyncio
async def test_invalid_query(scraper):
    """Test that the scraper handles invalid queries gracefully."""
    results = await scraper.scrape("!@#$%^&*()")
    assert isinstance(results, list), "Should return list even for invalid query" 