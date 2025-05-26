"""
Unit tests for forum scrapers.
Tests Dev.to, Stack Overflow, Product Hunt, and IndieHackers scrapers.
"""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from app.scraper.communities import (
    DevToScraper,
    StackOverflowScraper,
    ProductHuntScraper,
    IndieHackersScraper
)

@pytest.fixture
def mock_so_html():
    """Mock Stack Overflow HTML response"""
    return """
    <div class="s-post-summary">
        <h3><a href="/questions/12345/test-question">Test Question</a></h3>
        <div class="s-post-summary--stats">
            <span title="10 votes">10</span>
            <span title="5 answers">5</span>
            <span title="1000 views">1k</span>
        </div>
        <div class="s-post-summary--meta-tags">
            <a class="post-tag">python</a>
            <a class="post-tag">testing</a>
        </div>
        <div class="s-post-summary--content-excerpt">
            This is a test question excerpt
        </div>
    </div>
    """

@pytest.fixture
def mock_ph_html():
    """Mock Product Hunt HTML response"""
    return """
    <div data-test="homepage-section">
        <h3>Test Product</h3>
        <a href="/products/test">Link</a>
        <p>A great test product</p>
        <span>50 upvotes</span>
    </div>
    """

@pytest.fixture
def mock_ih_html():
    """Mock IndieHackers HTML response"""
    return """
    <div class="feed-item">
        <h2><a href="/post/123">Test Post</a></h2>
        <span class="author">Test Author</span>
        <span>10 comments</span>
    </div>
    """

@pytest.mark.asyncio
class TestForumScrapers:
    """Test suite for forum scrapers"""

    async def test_stackoverflow_scraper(self, mock_so_html):
        """Test Stack Overflow scraper"""
        scraper = StackOverflowScraper()
        scraper.get_soup = MagicMock(return_value=BeautifulSoup(mock_so_html, 'html.parser'))
        
        results = await scraper.scrape_questions('python')
        
        assert len(results) == 1
        result = results[0]
        assert result['title'] == 'Test Question'
        assert result['link'].endswith('/questions/12345/test-question')
        assert result['votes'] == '10'
        assert result['answers'] == '5'
        assert result['views'] == '1k'
        assert 'python' in result['tags']
        assert 'testing' in result['tags']
        assert result['excerpt'] == 'This is a test question excerpt'
        assert result['source'] == 'Stack Overflow'
        assert result['credibility_info']['score'] >= 85
        assert result['credibility_info']['category'] == 'Q&A'
        assert result['credibility_info']['bias'] == 'technical'

    async def test_stackoverflow_credibility(self):
        """Test Stack Overflow credibility calculation"""
        scraper = StackOverflowScraper()
        
        # Test high engagement
        score = scraper._calculate_credibility('100', '50', '10000')
        assert 85 <= score <= 95
        
        # Test low engagement
        score = scraper._calculate_credibility('1', '0', '100')
        assert score >= 85
        
        # Test invalid input
        score = scraper._calculate_credibility('invalid', 'invalid', 'invalid')
        assert score == 85.0

    async def test_producthunt_scraper(self, mock_ph_html):
        """Test Product Hunt scraper"""
        scraper = ProductHuntScraper()
        scraper.get_soup = MagicMock(return_value=BeautifulSoup(mock_ph_html, 'html.parser'))
        
        results = await scraper.scrape()
        
        assert len(results) == 1
        result = results[0]
        assert result['title'] == 'Test Product'
        assert result['link'].endswith('/products/test')
        assert result['description'] == 'A great test product'
        assert result['source'] == 'Product Hunt'
        assert result['credibility_info']['score'] >= 85
        assert result['credibility_info']['category'] == 'Product Launch'
        assert result['credibility_info']['bias'] == 'community-curated'

    async def test_producthunt_credibility(self):
        """Test Product Hunt credibility calculation"""
        scraper = ProductHuntScraper()
        
        # Test high votes
        score = scraper._calculate_credibility('1000')
        assert 85 <= score <= 95
        
        # Test low votes
        score = scraper._calculate_credibility('10')
        assert score >= 85
        
        # Test invalid input
        score = scraper._calculate_credibility('invalid')
        assert score == 85.0

    async def test_indiehackers_scraper(self, mock_ih_html):
        """Test IndieHackers scraper"""
        scraper = IndieHackersScraper()
        scraper.get_soup = MagicMock(return_value=BeautifulSoup(mock_ih_html, 'html.parser'))
        
        results = await scraper.scrape()
        
        assert len(results) == 1
        result = results[0]
        assert result['title'] == 'Test Post'
        assert result['link'].endswith('/post/123')
        assert result['author'] == 'Test Author'
        assert result['source'] == 'IndieHackers'
        assert result['credibility_info']['score'] >= 85
        assert result['credibility_info']['category'] == 'Community Discussion'
        assert result['credibility_info']['bias'] == 'indie-focused'

    async def test_indiehackers_credibility(self):
        """Test IndieHackers credibility calculation"""
        scraper = IndieHackersScraper()
        
        # Test high engagement
        score = scraper._calculate_credibility('100')
        assert 85 <= score <= 95
        
        # Test low engagement
        score = scraper._calculate_credibility('5')
        assert score >= 85
        
        # Test invalid input
        score = scraper._calculate_credibility('invalid')
        assert score == 85.0

    @patch('feedparser.parse')
    async def test_devto_scraper(self, mock_parse):
        """Test Dev.to scraper"""
        mock_parse.return_value = {
            'entries': [{
                'title': 'Test Article',
                'link': 'https://dev.to/test',
                'author': 'Test Author',
                'summary': 'Test summary',
                'published': '2024-03-20T12:00:00Z'
            }]
        }
        
        scraper = DevToScraper()
        results = await scraper.scrape()
        
        assert len(results) > 0
        result = results[0]
        assert result['title'] == 'Test Article'
        assert result['link'] == 'https://dev.to/test'
        assert 'Test Author' in str(result)
        assert 'Test summary' in str(result)
        assert result['source'] == 'Dev.to' 