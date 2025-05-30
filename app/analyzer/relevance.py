"""
Relevance analysis module for determining content relevance to queries.
"""

import asyncio
from typing import Dict, Any, Optional, List
import re
from collections import Counter
import math


class RelevanceAnalyzer:
    """Analyzes relevance of content to search queries using TF-IDF and keyword matching."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the relevance analyzer.
        
        Args:
            config: Configuration dictionary with relevance analysis settings
        """
        self.config = config or {}
        self.min_score = self.config.get('min_score', 0.1)
        self.max_distance = self.config.get('max_distance', 0.8)
        self.boost_title = self.config.get('boost_title', 2.0)
        self.boost_keywords = self.config.get('boost_keywords', 1.5)
        
        # Common stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }
    
    async def analyze(self, content: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Analyze relevance of content to the given query.
        
        Args:
            content: Content dictionary with 'title', 'content', etc.
            query: Search query string
            
        Returns:
            Dictionary containing relevance analysis results
        """
        # Defensive: swap if arguments are reversed
        if isinstance(content, str) and isinstance(query, dict):
            content, query = query, content
        
        if not query or not query.strip():
            return {
                'score': 0.0,
                'matches': [],
                'title_matches': [],
                'keyword_density': 0.0,
                'explanation': 'No query provided'
            }
        
        # Extract text fields
        title = content.get('title', '')
        text_content = content.get('content', '')
        description = content.get('description', '')
        tags = content.get('tags', [])
        
        # Combine all text for analysis
        full_text = f"{title} {description} {text_content}"
        if isinstance(tags, list):
            full_text += " " + " ".join(tags)
        
        # Clean and tokenize query and content
        query_tokens = self._tokenize(query)
        content_tokens = self._tokenize(full_text)
        title_tokens = self._tokenize(title)
        
        # Calculate different relevance scores
        keyword_score = self._calculate_keyword_score(query_tokens, content_tokens)
        title_score = self._calculate_keyword_score(query_tokens, title_tokens) * self.boost_title
        tfidf_score = self._calculate_tfidf_score(query_tokens, content_tokens)
        semantic_score = self._calculate_semantic_score(query, full_text)
        
        # Combine scores with weights
        final_score = (
            keyword_score * 0.3 +
            title_score * 0.3 +
            tfidf_score * 0.2 +
            semantic_score * 0.2
        )
        
        # Find specific matches
        matches = self._find_matches(query_tokens, content_tokens)
        title_matches = self._find_matches(query_tokens, title_tokens)
        
        # Calculate keyword density
        keyword_density = len(matches) / max(len(content_tokens), 1)
        
        # Generate explanation
        explanation = self._generate_explanation(
            final_score, matches, title_matches, keyword_density
        )
        
        return {
            'score': round(min(final_score, 1.0), 3),
            'matches': matches,
            'title_matches': title_matches,
            'keyword_density': round(keyword_density, 3),
            'explanation': explanation,
            'components': {
                'keyword_score': round(keyword_score, 3),
                'title_score': round(title_score, 3),
                'tfidf_score': round(tfidf_score, 3),
                'semantic_score': round(semantic_score, 3)
            }
        }
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into clean words."""
        if not text:
            return []
        
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short words
        return [word for word in words if word not in self.stop_words and len(word) > 2]
    
    def _calculate_keyword_score(self, query_tokens: List[str], content_tokens: List[str]) -> float:
        """Calculate simple keyword matching score."""
        if not query_tokens or not content_tokens:
            return 0.0
        
        content_set = set(content_tokens)
        matches = sum(1 for token in query_tokens if token in content_set)
        
        return matches / len(query_tokens)
    
    def _calculate_tfidf_score(self, query_tokens: List[str], content_tokens: List[str]) -> float:
        """Calculate TF-IDF based relevance score."""
        if not query_tokens or not content_tokens:
            return 0.0
        
        content_counter = Counter(content_tokens)
        total_words = len(content_tokens)
        
        score = 0.0
        for token in query_tokens:
            if token in content_counter:
                # Term frequency
                tf = content_counter[token] / total_words
                
                # Simple IDF approximation (would need document corpus for real IDF)
                idf = math.log(1000 / (content_counter[token] + 1))
                
                score += tf * idf
        
        return min(score, 1.0)
    
    def _calculate_semantic_score(self, query: str, content: str) -> float:
        """Calculate semantic similarity (simplified version)."""
        if not query or not content:
            return 0.0
        
        # Simple semantic scoring based on word overlap and proximity
        query_words = set(self._tokenize(query))
        content_words = set(self._tokenize(content))
        
        if not query_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(query_words.intersection(content_words))
        union = len(query_words.union(content_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _find_matches(self, query_tokens: List[str], content_tokens: List[str]) -> List[str]:
        """Find specific query tokens that match in content."""
        content_set = set(content_tokens)
        return [token for token in query_tokens if token in content_set]
    
    def _generate_explanation(
        self, 
        score: float, 
        matches: List[str], 
        title_matches: List[str], 
        keyword_density: float
    ) -> str:
        """Generate human-readable explanation of relevance score."""
        if score < 0.2:
            return f"Low relevance - few matching keywords ({len(matches)} matches)"
        elif score < 0.5:
            return f"Moderate relevance - some matching keywords ({len(matches)} matches)"
        elif score < 0.8:
            explanation = f"High relevance - many matching keywords ({len(matches)} matches)"
            if title_matches:
                explanation += f", including {len(title_matches)} in title"
            return explanation
        else:
            explanation = f"Very high relevance - strong keyword matches ({len(matches)} matches)"
            if title_matches:
                explanation += f", {len(title_matches)} in title"
            if keyword_density > 0.05:
                explanation += f", high keyword density ({keyword_density:.1%})"
            return explanation
    
    async def analyze_batch(self, contents: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Analyze relevance for a batch of content items.
        
        Args:
            contents: List of content dictionaries
            query: Search query string
            
        Returns:
            List of relevance analysis results
        """
        tasks = [self.analyze(content, query) for content in contents]
        return await asyncio.gather(*tasks)
