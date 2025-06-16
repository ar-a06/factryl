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
        
        # Known entities that should be treated as exact matches
        self.known_entities = {
            'bts': {
                'aliases': ['방탄소년단', 'bangtan boys', 'bangtantv', 'bangtan sonyeondan'],
                'related_terms': ['k-pop', 'kpop', 'korean', 'idol', 'army'],
                'members': [
                    'rm', 'kim nam-joon', 'kim namjoon',
                    'jin', 'kim seok-jin', 'kim seokjin',
                    'suga', 'min yoon-gi', 'min yoongi', 'agust d',
                    'j-hope', 'jung ho-seok', 'jung hoseok',
                    'jimin', 'park ji-min', 'park jimin',
                    'v', 'kim tae-hyung', 'kim taehyung',
                    'jungkook', 'jeon jung-kook', 'jeon jungkook'
                ]
            }
            # Add more entities as needed
        }
        
        # Common stop words to filter out
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }
    
    def _is_known_entity(self, query: str) -> Optional[Dict[str, Any]]:
        """Check if query matches any known entity."""
        query_lower = query.lower().strip()
        
        for entity, info in self.known_entities.items():
            # Check exact match
            if query_lower == entity:
                return info
            
            # Check aliases
            if query_lower in info['aliases']:
                return info
            
            # Check members (for group entities)
            if 'members' in info and query_lower in info['members']:
                return info
        
        return None
    
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
        
        # Check if query is a known entity
        entity_info = self._is_known_entity(query)
        
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
        
        # Apply entity-specific scoring if applicable
        if entity_info:
            # Check for exact entity matches
            entity_score = self._calculate_entity_score(query, full_text, entity_info)
            
            # Boost scores if entity-related terms are found
            if entity_score > 0:
                keyword_score *= 1.5
                title_score *= 1.5
                semantic_score = max(semantic_score, entity_score)
        
        # Combine scores with weights
        final_score = (
            keyword_score * 0.3 +
            title_score * 0.3 +
            tfidf_score * 0.2 +
            semantic_score * 0.2
        )
        
        # If it's a known entity but score is low, likely unrelated
        if entity_info and final_score < 0.4:
            final_score *= 0.5  # Penalize likely unrelated content
        
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
    
    def _calculate_entity_score(self, query: str, content: str, entity_info: Dict[str, Any]) -> float:
        """Calculate relevance score for known entities."""
        content_lower = content.lower()
        score = 0.0
        
        # Check for exact matches of entity name and aliases
        if query.lower() in content_lower:
            score += 0.6
        for alias in entity_info['aliases']:
            if alias in content_lower:
                score += 0.4
                break
        
        # Check for related terms
        for term in entity_info['related_terms']:
            if term in content_lower:
                score += 0.2
        
        # Check for member names if applicable
        if 'members' in entity_info:
            for member in entity_info['members']:
                if member in content_lower:
                    score += 0.3
                    break
        
        return min(score, 1.0)
    
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
