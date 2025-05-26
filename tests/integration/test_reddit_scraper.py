"""
Integration tests for Reddit scraper.
"""

import pytest
from app.scraper.reddit import RedditScraper

@pytest.fixture
async def scraper():
    """Fixture to create and cleanup a Reddit scraper instance."""
    config = {
        'reddit': {
            'max_posts': 5,
            'min_score': 100,
            'time_filter': 'month',
            'sort_by': 'relevance'
        },
        'cache': {
            'enabled': False  # Disable caching for testing
        }
    }
    
    scraper = RedditScraper(config)
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

@pytest.mark.asyncio
async def test_scraper_empty_query(scraper):
    """Test that the scraper handles empty queries gracefully."""
    results = await scraper.scrape("")
    assert isinstance(results, list), "Should return empty list for empty query"
    assert len(results) == 0, "Should not find results for empty query"

@pytest.mark.asyncio
async def test_scraper_sort_options(scraper):
    """Test that the scraper handles different sort options."""
    query = "test query"
    
    # Test different sort options
    sort_options = ['relevance', 'hot', 'new', 'top']
    for sort_by in sort_options:
        scraper.config['reddit']['sort_by'] = sort_by
        results = await scraper.scrape(query)
        assert isinstance(results, list), f"Should return list for sort_by={sort_by}" 