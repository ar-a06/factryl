"""
Unit tests for the search engine module.
"""

import pytest
from app.engine import SearchEngine

@pytest.fixture
def engine():
    """Fixture to create a search engine instance."""
    config = {
        'engine': {
            'max_results': 10,
            'min_relevance': 0.5,
            'timeout': 5
        }
    }
    return SearchEngine(config)

def test_search_query_parsing(engine):
    """Test that search queries are parsed correctly."""
    query = "AI ethics in healthcare"
    parsed = engine.parse_query(query)
    
    assert isinstance(parsed, dict), "Parsed query should be a dictionary"
    assert 'keywords' in parsed, "Should extract keywords"
    assert 'topics' in parsed, "Should identify topics"
    assert len(parsed['keywords']) > 0, "Should find at least one keyword"

def test_result_ranking(engine):
    """Test that search results are ranked properly."""
    results = [
        {'relevance': 0.8, 'freshness': 0.9},
        {'relevance': 0.9, 'freshness': 0.7},
        {'relevance': 0.7, 'freshness': 0.8}
    ]
    
    ranked = engine.rank_results(results)
    assert len(ranked) == len(results), "Should preserve all results"
    assert ranked[0]['relevance'] > ranked[-1]['relevance'], "Should sort by relevance"

def test_empty_query(engine):
    """Test handling of empty queries."""
    results = engine.search("")
    assert isinstance(results, list), "Should return empty list for empty query"
    assert len(results) == 0, "Should not find results for empty query"
