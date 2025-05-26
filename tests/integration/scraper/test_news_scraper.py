"""
Integration tests for the news scraper module.
"""

import pytest
from pathlib import Path
from datetime import datetime
from app.scraper.news import NewsScraper

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

@pytest.mark.asyncio
class TestNewsScraper:
    """Integration tests for the news scraper."""
    
    @pytest.fixture
    async def news_scraper(self, base_config):
        """Create a news scraper instance."""
        scraper = NewsScraper(base_config)
        yield scraper
        await scraper.close()
    
    async def test_scrape_with_valid_query(self, news_scraper, test_queries):
        """Test scraping with valid queries."""
        for query in test_queries:
            results = await news_scraper.scrape(query)
            assert isinstance(results, list)
            if results:  # If we got any results
                for article in results:
                    # Verify required fields
                    assert 'title' in article
                    assert 'url' in article
                    assert 'content' in article
                    assert 'source' in article
                    assert 'source_detail' in article
                    assert 'credibility_info' in article
                    
                    # Verify credibility info
                    cred_info = article['credibility_info']
                    assert 'score' in cred_info
                    assert 'bias' in cred_info
                    assert 'category' in cred_info
                    
                    # Verify metadata
                    assert 'metadata' in article
                    metadata = article['metadata']
                    assert 'preview' in metadata
                    assert 'language' in metadata
                    assert 'scraped_at' in metadata
    
    async def test_scrape_with_empty_query(self, news_scraper):
        """Test scraping with empty query."""
        results = await news_scraper.scrape("")
        assert isinstance(results, list)
        assert len(results) == 0
    
    async def test_scrape_with_invalid_query(self, news_scraper):
        """Test scraping with invalid query."""
        results = await news_scraper.scrape("thisisaverylongquerythatwontmatchanything12345")
        assert isinstance(results, list)
        assert len(results) == 0
    
    async def test_source_credibility_filtering(self, news_scraper, base_config):
        """Test that sources below minimum credibility score are filtered out."""
        # Create a new scraper with high minimum credibility
        high_cred_config = base_config.copy()
        high_cred_config['scraping']['min_credibility_score'] = 95
        
        scraper = NewsScraper(high_cred_config)
        try:
            results = await scraper.scrape("test query")
            
            # Verify all returned articles meet minimum credibility
            for article in results:
                assert article['credibility_info']['score'] >= 95
        finally:
            await scraper.close()
    
    async def test_max_articles_limit(self, news_scraper, base_config):
        """Test that max_total_articles limit is respected."""
        # Create a new scraper with low article limit
        limited_config = base_config.copy()
        limited_config['scraping']['max_total_articles'] = 2
        
        scraper = NewsScraper(limited_config)
        try:
            results = await scraper.scrape("artificial intelligence")
            assert len(results) <= 2
        finally:
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