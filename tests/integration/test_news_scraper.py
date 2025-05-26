"""
Integration tests for the news scraper module.
"""

import pytest
from pathlib import Path
from datetime import datetime
from app.scraper import NewsScraper

@pytest.fixture
def test_dirs(tmp_path):
    """Fixture to create test directories."""
    output_dir = tmp_path / "output"
    logs_dir = output_dir / "logs"
    data_dir = output_dir / "data"
    reports_dir = output_dir / "reports"
    
    for dir_path in [logs_dir, data_dir, reports_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        
    return {
        'output': output_dir,
        'logs': logs_dir,
        'data': data_dir,
        'reports': reports_dir
    }

@pytest.fixture
async def scraper():
    """Fixture to create and cleanup a news scraper instance."""
    config = {
        'cache': {
            'enabled': False,
            'host': 'localhost',
            'port': 6379
        },
        'scraping': {
            'max_total_articles': 10,  # Reduced for testing
            'min_credibility_score': 85,
            'default_timeout': 10
        }
    }
    
    scraper = NewsScraper(config)
    yield scraper
    await scraper.close()

@pytest.mark.asyncio
async def test_news_scraper_search(scraper, test_dirs):
    """Test that the news scraper can search and aggregate results."""
    query = "artificial intelligence latest developments"
    articles = await scraper.scrape(query)
    
    assert isinstance(articles, list), "Results should be a list"
    assert len(articles) > 0, "Should find at least one article"
    
    # Validate article structure
    for article in articles:
        assert 'title' in article, "Article should have a title"
        assert 'source_detail' in article, "Article should have source details"
        assert 'url' in article, "Article should have a URL"
        assert 'credibility_info' in article, "Article should have credibility info"
        assert 'metadata' in article, "Article should have metadata"
        assert 'preview' in article['metadata'], "Article should have a preview"

@pytest.mark.asyncio
async def test_news_scraper_categories(scraper):
    """Test that articles are properly categorized."""
    query = "technology and science news"
    articles = await scraper.scrape(query)
    
    # Group articles by category
    categories = {}
    for article in articles:
        cat = article['credibility_info']['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)
    
    assert len(categories) > 0, "Should have at least one category"
    for category, cat_articles in categories.items():
        assert isinstance(category, str), "Category should be a string"
        assert len(cat_articles) > 0, "Category should have at least one article"

@pytest.mark.asyncio
async def test_news_scraper_credibility(scraper):
    """Test that articles meet credibility requirements."""
    query = "latest news"
    articles = await scraper.scrape(query)
    
    min_score = scraper.config['scraping']['min_credibility_score']
    for article in articles:
        score = article['credibility_info']['score']
        assert score >= min_score, f"Article credibility ({score}) should meet minimum requirement ({min_score})"
        assert 'bias' in article['credibility_info'], "Article should have bias rating"

@pytest.mark.asyncio
async def test_news_scraper_empty_query(scraper):
    """Test that the scraper handles empty queries gracefully."""
    results = await scraper.scrape("")
    assert isinstance(results, list), "Should return empty list for empty query"
    assert len(results) == 0, "Should not find results for empty query"

@pytest.mark.asyncio
async def test_save_results(scraper, test_dirs):
    """Test that results can be saved properly."""
    query = "test query"
    articles = await scraper.scrape(query)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_slug = query.lower().replace(' ', '_')[:30]
    
    # Save raw data
    data_path = test_dirs['data'] / f"{query_slug}_{timestamp}"
    data_path.mkdir(exist_ok=True)
    
    articles_file = data_path / "articles.json"
    with open(articles_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(articles, f)
    
    assert articles_file.exists(), "Articles file should be created"
    assert articles_file.stat().st_size > 0, "Articles file should not be empty" 