"""
Deduplicator module for removing duplicate content items.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


class Deduplicator:
    """Removes duplicate content items using various similarity detection methods."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the deduplicator.
        
        Args:
            config: Configuration dictionary with deduplication settings
        """
        self.config = config or {}
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)
        self.title_threshold = self.config.get('title_threshold', 0.9)
        self.url_threshold = self.config.get('url_threshold', 0.95)
        self.content_threshold = self.config.get('content_threshold', 0.85)
        self.min_content_length = self.config.get('min_content_length', 50)
    
    def deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate items from the list.
        
        Args:
            items: List of content items to deduplicate
            
        Returns:
            List of unique content items
        """
        if not items:
            return []
        
        unique_items = []
        seen_hashes = set()
        processed_items = []
        
        # First pass: exact duplicates by hash
        for item in items:
            item_hash = self._generate_content_hash(item)
            if item_hash not in seen_hashes:
                seen_hashes.add(item_hash)
                processed_items.append(item)
        
        # Second pass: similarity-based deduplication
        for item in processed_items:
            is_duplicate = False
            
            for existing_item in unique_items:
                if self._are_similar(item, existing_item):
                    # Merge metadata from duplicate into existing item
                    self._merge_duplicate_metadata(existing_item, item)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
        
        return unique_items
    
    def _generate_content_hash(self, item: Dict[str, Any]) -> str:
        """Generate a hash for exact duplicate detection."""
        # Normalize content for hashing
        title = self._normalize_text(item.get('title', ''))
        content = self._normalize_text(item.get('content', ''))
        url = self._normalize_url(item.get('url', ''))
        
        # Create hash from normalized content
        hash_content = f"{title}|{content[:200]}|{url}"
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def _are_similar(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """Check if two items are similar enough to be considered duplicates."""
        # Check URL similarity first (most reliable)
        url_similarity = self._calculate_url_similarity(
            item1.get('url', ''), item2.get('url', '')
        )
        if url_similarity >= self.url_threshold:
            return True
        
        # Check title similarity
        title_similarity = self._calculate_text_similarity(
            item1.get('title', ''), item2.get('title', '')
        )
        
        # Check content similarity
        content_similarity = self._calculate_text_similarity(
            item1.get('content', ''), item2.get('content', '')
        )
        
        # Combine similarities with weights
        overall_similarity = (
            title_similarity * 0.4 +
            content_similarity * 0.4 +
            url_similarity * 0.2
        )
        
        return overall_similarity >= self.similarity_threshold
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        norm_text1 = self._normalize_text(text1)
        norm_text2 = self._normalize_text(text2)
        
        if not norm_text1 or not norm_text2:
            return 0.0
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm_text1, norm_text2).ratio()
    
    def _calculate_url_similarity(self, url1: str, url2: str) -> float:
        """Calculate similarity between two URLs."""
        if not url1 or not url2:
            return 0.0
        
        # Normalize URLs
        norm_url1 = self._normalize_url(url1)
        norm_url2 = self._normalize_url(url2)
        
        if norm_url1 == norm_url2:
            return 1.0
        
        # Parse URLs for component comparison
        try:
            parsed1 = urlparse(norm_url1)
            parsed2 = urlparse(norm_url2)
            
            # Compare domains
            if parsed1.netloc != parsed2.netloc:
                return 0.0
            
            # Compare paths
            path_similarity = SequenceMatcher(None, parsed1.path, parsed2.path).ratio()
            
            # Compare query parameters (if any)
            query_similarity = SequenceMatcher(None, parsed1.query, parsed2.query).ratio()
            
            # Weighted combination
            return path_similarity * 0.8 + query_similarity * 0.2
            
        except Exception:
            # Fallback to string similarity
            return SequenceMatcher(None, norm_url1, norm_url2).ratio()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        if not url:
            return ""
        
        # Remove common URL parameters that don't affect content
        url = re.sub(r'[?&](utm_[^&]*|ref[^&]*|source[^&]*|medium[^&]*)', '', url)
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Convert to lowercase
        url = url.lower()
        
        # Remove www. prefix
        url = re.sub(r'://www\.', '://', url)
        
        return url
    
    def _merge_duplicate_metadata(self, existing_item: Dict[str, Any], duplicate_item: Dict[str, Any]):
        """Merge metadata from duplicate item into existing item."""
        # Merge tags
        existing_tags = set(existing_item.get('tags', []))
        duplicate_tags = set(duplicate_item.get('tags', []))
        existing_item['tags'] = list(existing_tags.union(duplicate_tags))
        
        # Track duplicate sources
        if 'duplicate_sources' not in existing_item:
            existing_item['duplicate_sources'] = []
        
        existing_item['duplicate_sources'].append({
            'source_type': duplicate_item.get('source_type'),
            'url': duplicate_item.get('url'),
            'id': duplicate_item.get('id')
        })
