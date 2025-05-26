"""Unit tests for community scrapers."""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import feedparser
from app.scraper.communities import (
    StackOverflowScraper,
    DevToScraper,
    ProductHuntScraper,
    IndieHackersScraper,
    RedditScraper,
    QuoraScraper
)

@pytest.fixture
def mock_config():
    """Mock configuration for scrapers"""
    return {
        'max_results': 5,
        'tags': ['python', 'javascript'],
        'max_per_tag': 3,
        'subreddits': ['programming', 'technology'],
        'topics': ['Programming', 'Technology']
    }

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
        <div class="topics">
            <a>Tech</a>
            <a>Productivity</a>
        </div>
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
        <div class="content">Test content preview</div>
        <div class="topics">
            <a>Startups</a>
            <a>Marketing</a>
        </div>
    </div>
    """

@pytest.fixture
def mock_reddit_post():
    """Mock Reddit post object"""
    class MockPost:
        def __init__(self):
            self.title = "Test Post"
            self.permalink = "/r/programming/comments/123/test_post"
            self.author = "test_user"
            self.selftext = "Test content"
            self.score = 100
            self.upvote_ratio = 0.95
            self.num_comments = 50
            self.is_original_content = True
            self.created_utc = 1616213400
            self.subreddit = MagicMock()
            self.subreddit.display_name = "programming"
            self.link_flair_text = "Discussion"
    return MockPost()

@pytest.fixture
def mock_quora_html():
    """Mock Quora HTML response"""
    return """
    <div class="q-box">
        <span class="q-text">Test Question</span>
        <a class="q-box" href="/What-is-programming">What is programming?</a>
        <div class="q-text">This is a test answer</div>
        <div class="q-upvotes">100</div>
        <div class="q-comments">20</div>
        <a class="q-user">John Doe</a>
    </div>
    """

@pytest.mark.asyncio
class TestCommunityScrapers:
    """Test suite for community scrapers"""

    async def test_stackoverflow_scraper(self, mock_config, mock_so_html):
        """Test Stack Overflow scraper"""
        scraper = StackOverflowScraper(mock_config)
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

    @patch('feedparser.parse')
    async def test_devto_scraper(self, mock_parse, mock_config):
        """Test Dev.to scraper"""
        mock_parse.return_value = {
            'entries': [{
                'title': 'Test Article',
                'link': 'https://dev.to/test',
                'author': 'Test Author',
                'summary': 'Test summary',
                'published': '2024-03-20T12:00:00Z',
                'tags': ['python', 'testing']
            }]
        }
        
        scraper = DevToScraper(mock_config)
        results = await scraper.scrape()
        
        assert len(results) > 0
        result = results[0]
        assert result['title'] == 'Test Article'
        assert result['link'] == 'https://dev.to/test'
        assert result['author'] == 'Test Author'
        assert result['source'] == 'Dev.to'
        assert result['credibility_info']['score'] >= 85
        assert result['credibility_info']['category'] == 'Technical Blog'

    async def test_producthunt_scraper(self, mock_config, mock_ph_html):
        """Test Product Hunt scraper"""
        scraper = ProductHuntScraper(mock_config)
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
        assert len(result['topics']) == 2
        assert 'Tech' in result['topics']

    async def test_indiehackers_scraper(self, mock_config, mock_ih_html):
        """Test IndieHackers scraper"""
        scraper = IndieHackersScraper(mock_config)
        scraper.get_soup = MagicMock(return_value=BeautifulSoup(mock_ih_html, 'html.parser'))
        
        results = await scraper.scrape()
        
        assert len(results) == 1
        result = results[0]
        assert result['title'] == 'Test Post'
        assert result['link'].endswith('/post/123')
        assert result['author'] == 'Test Author'
        assert result['preview'] == 'Test content preview'
        assert result['source'] == 'IndieHackers'
        assert result['credibility_info']['score'] >= 85
        assert result['credibility_info']['category'] == 'Community Discussion'
        assert len(result['topics']) == 2
        assert 'Startups' in result['topics']

    @patch('praw.Reddit')
    async def test_reddit_scraper(self, mock_reddit, mock_config, mock_reddit_post):
        """Test Reddit scraper"""
        # Setup mock Reddit client
        mock_subreddit = MagicMock()
        mock_subreddit.hot.return_value = [mock_reddit_post]
        mock_reddit.return_value.subreddit.return_value = mock_subreddit
        
        scraper = RedditScraper(mock_config)
        results = await scraper.scrape()
        
        assert len(results) > 0
        result = results[0]
        assert result['title'] == "Test Post"
        assert result['link'].endswith("/test_post")
        assert result['author'] == "test_user"
        assert result['content'] == "Test content"
        assert result['source'] == 'Reddit'
        assert result['credibility_info']['score'] >= 85
        assert result['credibility_info']['category'] == 'Community Discussion'
        assert result['metadata']['score'] == 100
        assert result['metadata']['upvote_ratio'] == 0.95
        assert result['metadata']['num_comments'] == 50
        assert result['metadata']['is_original_content'] is True
        assert result['metadata']['flair'] == "Discussion"

    @patch('playwright.async_api.async_playwright')
    async def test_quora_scraper(self, mock_playwright, mock_config, mock_quora_html):
        """Test Quora scraper"""
        # Setup mock Playwright
        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = [BeautifulSoup(mock_quora_html, 'html.parser')]
        mock_page.goto = MagicMock()
        
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.start.return_value = mock_playwright_instance
        
        scraper = QuoraScraper(mock_config)
        results = await scraper.scrape()
        
        assert len(results) > 0
        result = results[0]
        assert result['title'] == "Test Question"
        assert result['link'].endswith("What-is-programming")
        assert result['answer_preview'] == "This is a test answer"
        assert result['author'] == "John Doe"
        assert result['source'] == 'Quora'
        assert result['credibility_info']['score'] >= 85
        assert result['credibility_info']['category'] == 'Q&A'
        assert result['metadata']['upvotes'] == "100"
        assert result['metadata']['comments'] == "20"

    def test_credibility_calculations(self):
        """Test credibility score calculations for all scrapers"""
        # Stack Overflow credibility
        so_scraper = StackOverflowScraper()
        so_score = so_scraper._calculate_credibility('100', '50', '10000')
        assert 85 <= so_score <= 95
        
        # Product Hunt credibility
        ph_scraper = ProductHuntScraper()
        ph_score = ph_scraper._calculate_credibility('1000')
        assert 85 <= ph_score <= 95
        
        # IndieHackers credibility
        ih_scraper = IndieHackersScraper()
        ih_score = ih_scraper._calculate_credibility('50 comments')
        assert 85 <= ih_score <= 95
        
        # Reddit credibility
        reddit_scraper = RedditScraper()
        mock_post = MagicMock()
        mock_post.score = 1000
        mock_post.upvote_ratio = 0.9
        mock_post.num_comments = 100
        mock_post.is_original_content = True
        reddit_score = reddit_scraper._calculate_credibility(mock_post)
        assert 85 <= reddit_score <= 95
        
        # Quora credibility
        quora_scraper = QuoraScraper()
        quora_score = quora_scraper._calculate_credibility('100', '50')
        assert 85 <= quora_score <= 95
        
        # Test invalid inputs
        assert so_scraper._calculate_credibility('invalid', 'invalid', 'invalid') == 85.0
        assert ph_scraper._calculate_credibility('invalid') == 85.0
        assert ih_scraper._calculate_credibility('invalid') == 85.0
        assert reddit_scraper._calculate_credibility(mock_post) == 85.0
        assert quora_scraper._calculate_credibility('invalid', 'invalid') == 85.0 