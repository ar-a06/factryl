"""
Aggregator module for combining, deduplicating, and scoring content.
"""

from typing import List, Dict, Any
import hashlib
from difflib import SequenceMatcher
from .combiner import ContentCombiner
from .deduplicator import Deduplicator
from .scorer import ContentScorer


class NewsAggregator:
    """Aggregates and processes news articles from multiple sources."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the aggregator with configuration."""
        self.config = config
        aggregator_config = config.get('aggregator', {})
        self.deduplication_threshold = aggregator_config.get('deduplication_threshold', 0.8)
        self.max_articles_per_source = aggregator_config.get('max_articles_per_source', 5)
        self.min_article_length = aggregator_config.get('min_article_length', 100)
    
    def deduplicate(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on content similarity."""
        unique_articles = []
        
        for article in articles:
            is_duplicate = False
            for existing in unique_articles:
                similarity = self._calculate_similarity(
                    article.get('content', ''),
                    existing.get('content', '')
                )
                if similarity >= self.deduplication_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
        
        return unique_articles
    
    def apply_source_limits(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply per-source article limits."""
        source_counts = {}
        limited_articles = []
        
        for article in articles:
            source = article.get('source', 'unknown')
            current_count = source_counts.get(source, 0)
            
            if current_count < self.max_articles_per_source:
                limited_articles.append(article)
                source_counts[source] = current_count + 1
        
        return limited_articles
    
    def filter_content(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter articles based on content criteria."""
        filtered_articles = []
        
        for article in articles:
            content = article.get('content', '')
            if len(content) >= self.min_article_length:
                filtered_articles.append(article)
        
        return filtered_articles
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def aggregate(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Main aggregation method that applies all processing steps."""
        processed_articles = self.filter_content(articles)
        processed_articles = self.deduplicate(processed_articles)
        processed_articles = self.apply_source_limits(processed_articles)
        return processed_articles


__all__ = [
    'ContentCombiner',
    'Deduplicator',
    'ContentScorer'
]
