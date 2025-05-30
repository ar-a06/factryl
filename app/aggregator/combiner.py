"""
Content combiner module for merging and organizing content from multiple sources.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib


class ContentCombiner:
    """Combines content from multiple sources into a unified format."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the content combiner.
        
        Args:
            config: Configuration dictionary with combiner settings
        """
        self.config = config or {}
        self.max_items_per_source = self.config.get('max_items_per_source', 100)
        self.preserve_source_metadata = self.config.get('preserve_source_metadata', True)
        self.source_credibility = {}
        self._load_source_credibility()
    
    def _load_source_credibility(self):
        """Load source credibility information from hardcoded data."""
        # Hardcoded source credibility data (moved from FactrylEngine)
        self.source_credibility = {
            'bbc': {
                'score': 0.9,
                'bias': 'Center',
                'category': 'News',
                'type': 'news'
            },
            'techcrunch': {
                'score': 0.85,
                'bias': 'Center-Left',
                'category': 'Technology News',
                'type': 'news'
            },
            'google_news': {
                'score': 0.8,
                'bias': 'Center',
                'category': 'News Aggregator',
                'type': 'news'
            },
            'duckduckgo': {
                'score': 0.75,
                'bias': 'Neutral',
                'category': 'Search Engine',
                'type': 'search'
            },
            'bing': {
                'score': 0.75,
                'bias': 'Neutral',
                'category': 'Search Engine',
                'type': 'search'
            },
            'safari': {
                'score': 0.75,
                'bias': 'Neutral',
                'category': 'Search Engine',
                'type': 'search'
            },
            'edge': {
                'score': 0.75,
                'bias': 'Neutral',
                'category': 'Search Engine',
                'type': 'search'
            },
            'wikipedia': {
                'score': 0.85,
                'bias': 'Neutral',
                'category': 'Knowledge Base',
                'type': 'knowledge'
            },
            'hackernews': {
                'score': 0.8,
                'bias': 'Center',
                'category': 'Technology Community',
                'type': 'social'
            },
            'dictionary': {
                'score': 0.95,
                'bias': 'Neutral',
                'category': 'Reference',
                'type': 'dictionary'
            }
        }
    
    def get_source_credibility(self, source: str) -> Dict[str, Any]:
        """Get credibility information for a source."""
        return self.source_credibility.get(source, {
            'score': 0.5,  # Default score
            'bias': 'Unknown',
            'category': 'Uncategorized',
            'type': 'unknown'
        })
    
    def combine(self, source_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Combine content from multiple sources into a unified list.
        
        Args:
            source_data: Dictionary mapping source names to lists of content items
            
        Returns:
            Combined list of content items with standardized format
        """
        combined_items = []
        
        for source_name, items in source_data.items():
            # Get source credibility information
            cred_info = self.get_source_credibility(source_name)
            
            # Limit items per source
            limited_items = items[:self.max_items_per_source]
            
            for item in limited_items:
                # Standardize the item format
                standardized_item = self._standardize_item(item, source_name, cred_info)
                combined_items.append(standardized_item)
        
        # Sort by timestamp if available, otherwise by relevance
        combined_items.sort(key=self._get_sort_key, reverse=True)
        
        return combined_items
    
    def _standardize_item(self, item: Dict[str, Any], source: str, cred_info: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize a content item to a common format."""
        # Generate a unique ID if not present
        if 'id' not in item:
            content_hash = hashlib.md5(
                f"{item.get('title', '')}{item.get('content', '')}{item.get('url', '')}".encode()
            ).hexdigest()
            item['id'] = f"{source}_{content_hash}"
        
        # Ensure required fields
        standardized = {
            'id': item['id'],
            'title': item.get('title', ''),
            'content': item.get('content', ''),
            'url': item.get('url', ''),
            'source': source,
            'source_type': cred_info['type'],
            'source_category': cred_info['category'],
            'credibility_score': cred_info['score'],
            'bias_rating': cred_info['bias'],
            'published': item.get('published', datetime.utcnow().isoformat()),
            'author': item.get('author', ''),
            'metadata': {}
        }
        
        # Preserve additional metadata if configured
        if self.preserve_source_metadata:
            for key, value in item.items():
                if key not in standardized:
                    standardized['metadata'][key] = value
        
        return standardized
    
    def _get_sort_key(self, item: Dict[str, Any]) -> tuple:
        """Get sort key for an item, prioritizing timestamp then relevance."""
        try:
            # Try to parse timestamp
            timestamp = datetime.fromisoformat(item.get('published', '').replace('Z', '+00:00'))
            return (timestamp, item.get('relevance_score', 0))
        except (ValueError, TypeError):
            # Fall back to relevance score
            return (datetime.min, item.get('relevance_score', 0))
    
    def get_source_statistics(self, combined_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about the combined content.
        
        Args:
            combined_items: List of combined content items
            
        Returns:
            Dictionary with statistics about sources and content
        """
        if not combined_items:
            return {'total_items': 0, 'sources': {}}
        
        source_counts = {}
        total_items = len(combined_items)
        
        for item in combined_items:
            source = item.get('source_type', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Calculate percentages
        source_percentages = {
            source: round((count / total_items) * 100, 1)
            for source, count in source_counts.items()
        }
        
        return {
            'total_items': total_items,
            'sources': source_counts,
            'source_percentages': source_percentages,
            'unique_sources': len(source_counts)
        }
