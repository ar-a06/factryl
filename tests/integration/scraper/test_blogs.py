"""Unit tests for blog scrapers."""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import feedparser
from app.scraper.blogs import (
    MediumScraper,
    SubstackScraper,
    GhostBlogScraper,
    BlogScraper
)

@pytest.fixture
def mock_config():
    """Mock configuration for scrapers"""
    return {
        'max_posts': 5,
        'tags': ['python', 'javascript'],
        'publications': ['towards-data-science', 'hackernoon'],
        'substacks': ['stratechery.com', 'platformer.news'],
        'blogs': [
            {
                'domain': 'martinfowler.com',
                'name': 'Martin Fowler',
                'type': 'personal',
                'rss_url': 'https://martinfowler.com/feed.atom'
            },
            {
                'domain': 'engineering.linkedin.com',
                'name': 'LinkedIn Engineering',
                'type': 'company',
                'rss_url': 'https://engineering.linkedin.com/blog.rss.html'
            }
        ]
    }

@pytest.fixture
def mock_rss_feed():
    """Mock RSS feed response"""
    return {
        'entries': [{
            'title': 'Test Article',
            'link': 'https://example.com/test',
            'author': 'Test Author',
            'summary': 'Test summary',
            'published': '2024-03-20T12:00:00Z',
            'tags': ['python', 'testing']
        }]
    }

@pytest.fixture
def mock_ghost_html():
    """Mock Ghost blog HTML response"""
    return """
    <article class="post">
        <h2><a href="/test-post">Test Post</a></h2>
        <p>Test excerpt</p>
        <div class="author">Test Author</div>
        <div class="tags">
            <a>python</a>
            <a>testing</a>
        </div>
    </article>
    """

@pytest.fixture
def mock_substack_html():
    """Mock Substack HTML response"""
    return """
    <div class="post">
        <h3><a href="/test-newsletter">Test Newsletter</a></h3>
        <p>Test content</p>
        <div class="author">Test Author</div>
    </div>
    """

@pytest.fixture
def mock_blog_html():
    """Mock blog HTML response"""
    return """
    <article class="blog-post">
        <h2 class="title"><a href="/test-article">Test Blog Post</a></h2>
        <div class="post-excerpt">Test blog excerpt</div>
        <div class="author-name">Test Author</div>
    </article>
    """

@pytest.mark.asyncio
class TestBlogScrapers:
    """Test suite for blog scrapers"""
    
    @patch('feedparser.parse')
    async def test_medium_scraper(self, mock_parse, mock_config, mock_rss_feed):
        """Test Medium scraper"""
        mock_parse.return_value = mock_rss_feed
        
        scraper = MediumScraper(mock_config)
        
        # Test tag scraping
        tag_results = await scraper.scrape_by_tag('python')
        assert len(tag_results) > 0
        result = tag_results[0]
        assert result['title'] == 'Test Article'
        assert result['source'] == 'Medium'
        assert result['credibility_info']['category'] == 'Technical Blog'
        assert result['metadata']['tag'] == 'python'
        
        # Test publication scraping
        pub_results = await scraper.scrape_publication('towards-data-science')
        assert len(pub_results) > 0
        result = pub_results[0]
        assert result['source'] == 'Medium'
        assert result['credibility_info']['bias'] == 'publication-reviewed'
        assert result['metadata']['publication'] == 'towards-data-science'
        
        # Test user scraping
        user_results = await scraper.scrape_user('testuser')
        assert len(user_results) > 0
        result = user_results[0]
        assert result['source'] == 'Medium'
        assert result['credibility_info']['bias'] == 'individual-author'
        assert result['metadata']['username'] == 'testuser'
    
    @patch('feedparser.parse')
    async def test_substack_scraper(self, mock_parse, mock_config, mock_rss_feed, mock_substack_html):
        """Test Substack scraper"""
        mock_parse.return_value = mock_rss_feed
        
        scraper = SubstackScraper(mock_config)
        scraper.get_soup = MagicMock(return_value=BeautifulSoup(mock_substack_html, 'html.parser'))
        
        results = await scraper.scrape_substack('stratechery.com')
        assert len(results) > 0
        result = results[0]
        
        # Test RSS-based result
        assert result['title'] == 'Test Article'
        assert result['source'] == 'Substack'
        assert result['credibility_info']['category'] == 'Newsletter'
        assert result['metadata']['substack'] == 'stratechery.com'
        
        # Test web-based fallback
        mock_parse.return_value = {'entries': []}  # Force web scraping
        results = await scraper.scrape_substack('stratechery.com')
        assert len(results) > 0
        result = results[0]
        assert result['title'] == 'Test Newsletter'
        assert result['source'] == 'Substack'
        assert result['author'] == 'Test Author'
    
    @patch('feedparser.parse')
    async def test_ghost_blog_scraper(self, mock_parse, mock_config, mock_rss_feed, mock_ghost_html):
        """Test Ghost blog scraper"""
        mock_parse.return_value = mock_rss_feed
        
        scraper = GhostBlogScraper(mock_config)
        scraper.get_soup = MagicMock(return_value=BeautifulSoup(mock_ghost_html, 'html.parser'))
        
        results = await scraper.scrape_ghost_blog('blog.ghost.org')
        assert len(results) > 0
        result = results[0]
        
        # Test RSS-based result
        assert result['title'] == 'Test Article'
        assert result['source'] == 'Ghost Blog'
        assert result['credibility_info']['category'] == 'Technical Blog'
        assert result['metadata']['blog'] == 'blog.ghost.org'
        
        # Test web-based fallback
        mock_parse.return_value = {'entries': []}  # Force web scraping
        results = await scraper.scrape_ghost_blog('blog.ghost.org')
        assert len(results) > 0
        result = results[0]
        assert result['title'] == 'Test Post'
        assert result['source'] == 'Ghost Blog'
        assert result['author'] == 'Test Author'
        assert len(result['tags']) == 2
    
    @patch('feedparser.parse')
    async def test_blog_scraper(self, mock_parse, mock_config, mock_rss_feed, mock_blog_html):
        """Test generic blog scraper"""
        mock_parse.return_value = mock_rss_feed
        
        scraper = BlogScraper(mock_config)
        scraper.get_soup = MagicMock(return_value=BeautifulSoup(mock_blog_html, 'html.parser'))
        
        # Test RSS-based scraping
        blog_config = mock_config['blogs'][0]  # Martin Fowler blog
        results = await scraper.scrape_blog(blog_config)
        assert len(results) > 0
        result = results[0]
        
        # Test RSS result
        assert result['title'] == 'Test Article'
        assert result['source'] == 'Technical Blog'
        assert result['credibility_info']['category'] == 'Technical Blog'
        assert result['credibility_info']['bias'] == 'personal-authored'
        assert result['metadata']['blog_name'] == 'Martin Fowler'
        assert result['metadata']['blog_type'] == 'personal'
        
        # Test web-based fallback
        mock_parse.return_value = {'entries': []}  # Force web scraping
        results = await scraper.scrape_blog(blog_config)
        assert len(results) > 0
        result = results[0]
        assert result['title'] == 'Test Blog Post'
        assert result['source'] == 'Technical Blog'
        assert result['author'] == 'Test Author'
        assert result['summary'] == 'Test blog excerpt'
        
        # Test company blog
        blog_config = mock_config['blogs'][1]  # LinkedIn Engineering blog
        results = await scraper.scrape_blog(blog_config)
        assert len(results) > 0
        result = results[0]
        assert result['metadata']['blog_type'] == 'company'
        assert result['credibility_info']['bias'] == 'company-authored'
    
    def test_credibility_calculations(self):
        """Test credibility score calculations for all scrapers"""
        # Medium credibility
        medium_scraper = MediumScraper()
        medium_score = medium_scraper._calculate_credibility({
            'author_bio': 'Test bio',
            'tags': ['python', 'testing'],
            'content': 'x' * 4000,  # Long content
            'publication': 'towards-data-science'
        })
        assert 85 <= medium_score <= 95
        
        # Substack credibility
        substack_scraper = SubstackScraper()
        substack_score = substack_scraper._calculate_credibility({
            'author': 'Test Author',
            'summary': 'x' * 1000,  # Long summary
            'substack': 'stratechery.com',
            'comment_count': 20
        })
        assert 85 <= substack_score <= 95
        
        # Ghost blog credibility
        ghost_scraper = GhostBlogScraper()
        ghost_score = ghost_scraper._calculate_credibility({
            'author': 'Test Author',
            'summary': 'x' * 1000,  # Long summary
            'tags': ['python', 'testing', 'web'],
            'blog': 'troyhunt.com'
        })
        assert 85 <= ghost_score <= 95
        
        # Generic blog credibility
        blog_scraper = BlogScraper()
        
        # Test personal blog
        personal_score = blog_scraper._calculate_credibility({
            'author': 'Test Author',
            'summary': 'x' * 1000,  # Long summary
            'blog_type': 'personal',
            'blog_name': 'Martin Fowler'  # Known authority
        })
        assert 85 <= personal_score <= 95
        
        # Test company blog
        company_score = blog_scraper._calculate_credibility({
            'author': 'Test Author',
            'summary': 'x' * 1000,  # Long summary
            'blog_type': 'company',
            'blog_name': 'LinkedIn Engineering'  # Known company
        })
        assert 85 <= company_score <= 95
        
        # Test invalid inputs
        assert medium_scraper._calculate_credibility({}) == 85.0
        assert substack_scraper._calculate_credibility({}) == 85.0
        assert ghost_scraper._calculate_credibility({}) == 85.0
        assert blog_scraper._calculate_credibility({}) == 85.0 