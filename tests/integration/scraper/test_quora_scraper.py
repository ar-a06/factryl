"""
Integration tests for Quora scraper.
"""

import asyncio
import pytest
from app.scraper.quora import QuoraScraper

@pytest.fixture
async def scraper():
    """Fixture to create and cleanup a Quora scraper instance."""
    config = {
        'cache': {
            'enabled': False
        },
        'quora': {
            'max_answers': 5,  # Limiting to 5 answers for testing
            'min_upvotes': 5,
            'time_filter': 'week',
            'min_credibility': 60
        }
    }
    
    scraper = QuoraScraper(config)
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
    query = "What are the best practices for Python programming?"
    results = await scraper.scrape(query)
    
    assert isinstance(results, list), "Results should be a list"
    assert len(results) > 0, "Should find at least one result"
    
    # Validate result structure
    for result in results:
        assert 'title' in result, "Result should have a title"
        assert 'author' in result, "Result should have an author"
        assert 'url' in result, "Result should have a URL"
        assert 'credibility_info' in result, "Result should have credibility info"
        assert isinstance(result['credibility_info']['score'], (int, float)), "Credibility score should be numeric"

@pytest.mark.asyncio
async def test_scraper_empty_query(scraper):
    """Test that the scraper handles empty queries gracefully."""
    results = await scraper.scrape("")
    assert isinstance(results, list), "Should return empty list for empty query"
    assert len(results) == 0, "Should not find results for empty query"

@pytest.mark.asyncio
async def test_scraper_invalid_query(scraper):
    """Test that the scraper handles invalid queries gracefully."""
    results = await scraper.scrape("!@#$%^&*()")
    assert isinstance(results, list), "Should return list even for invalid query" 