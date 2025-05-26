"""
Unit tests for the aggregator module.
"""

import pytest
from app.aggregator import NewsAggregator

@pytest.fixture
def aggregator():
    """Fixture to create a news aggregator instance."""
    config = {
        'aggregator': {
            'deduplication_threshold': 0.8,
            'max_articles_per_source': 5,
            'min_article_length': 100
        }
    }
    return NewsAggregator(config)

def test_article_deduplication(aggregator):
    """Test that similar articles are properly deduplicated."""
    articles = [
        {
            'title': 'AI Makes Breakthrough in Protein Folding',
            'content': 'Scientists announce major AI breakthrough...',
            'source': 'Source A'
        },
        {
            'title': 'Artificial Intelligence Solves Protein Folding',
            'content': 'Scientists announce major AI breakthrough...',
            'source': 'Source B'
        },
        {
            'title': 'Completely Different Article',
            'content': 'This is about something else entirely...',
            'source': 'Source C'
        }
    ]
    
    unique_articles = aggregator.deduplicate(articles)
    assert len(unique_articles) < len(articles), "Should remove duplicate articles"
    assert len(unique_articles) == 2, "Should keep one of the similar articles"

def test_source_limits(aggregator):
    """Test that per-source article limits are enforced."""
    articles = [
        {'title': 'Article 1', 'source': 'Source A'},
        {'title': 'Article 2', 'source': 'Source A'},
        {'title': 'Article 3', 'source': 'Source A'},
        {'title': 'Article 4', 'source': 'Source A'},
        {'title': 'Article 5', 'source': 'Source A'},
        {'title': 'Article 6', 'source': 'Source A'},
        {'title': 'Article 1', 'source': 'Source B'},
        {'title': 'Article 2', 'source': 'Source B'}
    ]
    
    limited_articles = aggregator.apply_source_limits(articles)
    source_counts = {}
    for article in limited_articles:
        source_counts[article['source']] = source_counts.get(article['source'], 0) + 1
    
    assert source_counts['Source A'] <= aggregator.config['aggregator']['max_articles_per_source']

def test_content_filtering(aggregator):
    """Test that articles are filtered based on content criteria."""
    articles = [
        {
            'title': 'Good Article',
            'content': 'This is a long enough article with proper content...' * 10,
            'source': 'Source A'
        },
        {
            'title': 'Short Article',
            'content': 'Too short',
            'source': 'Source B'
        }
    ]
    
    filtered_articles = aggregator.filter_content(articles)
    assert len(filtered_articles) == 1, "Should remove articles that don't meet length requirements"
    assert filtered_articles[0]['title'] == 'Good Article', "Should keep the longer article"
