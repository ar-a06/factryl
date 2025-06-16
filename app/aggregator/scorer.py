"""
Content scorer module for ranking and scoring content items.
"""

from typing import List, Dict, Any, Optional
import math
from datetime import datetime, timedelta


class ContentScorer:
    """Scores and ranks content items based on various factors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the content scorer.
        
        Args:
            config: Configuration dictionary with scoring settings
        """
        self.config = config or {}
        self.min_score = self.config.get('min_score', 0.1)
        self.relevance_weight = self.config.get('relevance_weight', 0.4)
        self.credibility_weight = self.config.get('credibility_weight', 0.2)
        self.recency_weight = self.config.get('recency_weight', 0.2)
        self.engagement_weight = self.config.get('engagement_weight', 0.2)
        self.sort_by = self.config.get('sort_by', 'composite')
        
        # Scoring parameters
        self.max_age_days = self.config.get('max_age_days', 30)
        self.boost_factors = self.config.get('boost_factors', {})
        
        # Known entity types for specialized scoring
        self.entity_types = {
            'k-pop': ['bts', 'blackpink', 'twice', 'exo', 'nct', 'iu', 'psy'],
            'tech': ['apple', 'google', 'microsoft', 'meta', 'amazon'],
            'sports': ['nba', 'nfl', 'mlb', 'fifa', 'uefa']
        }
    
    def score(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score and rank content items.
        
        Args:
            items: List of content items to score
            
        Returns:
            List of scored and ranked content items
        """
        if not items:
            return []
        
        # Calculate scores for each item
        scored_items = []
        for item in items:
            score_data = self.calculate_score(item)
            item_copy = item.copy()
            item_copy['score'] = score_data
            scored_items.append(item_copy)
        
        # Sort by the specified criteria
        if self.sort_by == 'relevance':
            scored_items.sort(key=lambda x: x['score']['relevance'], reverse=True)
        elif self.sort_by == 'recency':
            scored_items.sort(key=lambda x: x['score']['recency'], reverse=True)
        elif self.sort_by == 'credibility':
            scored_items.sort(key=lambda x: x['score']['credibility'], reverse=True)
        elif self.sort_by == 'engagement':
            scored_items.sort(key=lambda x: x['score']['engagement'], reverse=True)
        else:  # composite score
            scored_items.sort(key=lambda x: x['score']['composite'], reverse=True)
        
        return scored_items
    
    def calculate_score(self, item: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive score for an item."""
        # Extract analysis data
        analysis = item.get('analysis', {})
        
        # Calculate component scores
        relevance_score = self._calculate_relevance_score(analysis)
        credibility_score = self._calculate_credibility_score(analysis)
        recency_score = self._calculate_recency_score(item)
        engagement_score = self._calculate_engagement_score(item)
        
        # Detect if content is about a known entity type
        entity_type = self._detect_entity_type(item)
        
        # Apply entity-specific scoring adjustments
        if entity_type:
            # For entity-focused content, boost relevance importance
            relevance_weight = self.relevance_weight * 1.5
            credibility_weight = self.credibility_weight * 0.8
            recency_weight = self.recency_weight
            engagement_weight = self.engagement_weight * 0.7
            
            # Normalize weights
            total_weight = relevance_weight + credibility_weight + recency_weight + engagement_weight
            relevance_weight /= total_weight
            credibility_weight /= total_weight
            recency_weight /= total_weight
            engagement_weight /= total_weight
        else:
            # Use default weights
            relevance_weight = self.relevance_weight
            credibility_weight = self.credibility_weight
            recency_weight = self.recency_weight
            engagement_weight = self.engagement_weight
        
        # Calculate composite score with appropriate weights
        composite_score = (
            relevance_score * relevance_weight +
            credibility_score * credibility_weight +
            recency_score * recency_weight +
            engagement_score * engagement_weight
        )
        
        # Apply source-specific boosts
        source_boost = self._calculate_source_boost(item)
        composite_score *= source_boost
        
        # For entity searches, if relevance is very low, significantly reduce overall score
        if entity_type and relevance_score < 0.3:
            composite_score *= 0.3  # Heavily penalize likely unrelated content
        
        return {
            'relevance': round(relevance_score, 3),
            'credibility': round(credibility_score, 3),
            'recency': round(recency_score, 3),
            'engagement': round(engagement_score, 3),
            'source_boost': round(source_boost, 3),
            'composite': round(max(composite_score, self.min_score), 3)
        }
    
    def _calculate_relevance_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate relevance score from analysis data."""
        relevance_data = analysis.get('relevance', {})
        
        if not relevance_data:
            return 0.5  # Default neutral score
        
        base_score = relevance_data.get('score', 0.5)
        
        # Boost for title matches
        title_matches = len(relevance_data.get('title_matches', []))
        title_boost = min(title_matches * 0.1, 0.3)
        
        # Boost for keyword density
        keyword_density = relevance_data.get('keyword_density', 0)
        density_boost = min(keyword_density * 2, 0.2)
        
        return min(base_score + title_boost + density_boost, 1.0)
    
    def _calculate_credibility_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate credibility score from analysis data."""
        credibility_data = analysis.get('credibility', {})
        
        if not credibility_data:
            return 0.5  # Default neutral score
        
        base_score = credibility_data.get('score', 0.5)
        
        # Penalty for risk factors
        risk_factors = credibility_data.get('risk_factors', [])
        risk_penalty = len(risk_factors) * 0.1
        
        return max(base_score - risk_penalty, 0.0)
    
    def _calculate_recency_score(self, item: Dict[str, Any]) -> float:
        """Calculate recency score based on publication date."""
        published_date = item.get('published_date')
        
        if not published_date:
            return 0.5  # Default neutral score
        
        try:
            # Parse the date
            if isinstance(published_date, str):
                pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            else:
                pub_date = published_date
            
            # Calculate age in days
            now = datetime.now()
            age_days = (now - pub_date).days
            
            # Score based on age (exponential decay)
            if age_days <= 0:
                return 1.0  # Future dates get max score
            elif age_days >= self.max_age_days:
                return 0.1  # Very old content gets minimal score
            else:
                # Exponential decay: score = e^(-age/half_life)
                half_life = self.max_age_days / 3  # Half score at 1/3 max age
                return math.exp(-age_days / half_life)
                
        except (ValueError, TypeError):
            return 0.5  # Default for unparseable dates
    
    def _calculate_engagement_score(self, item: Dict[str, Any]) -> float:
        """Calculate engagement score based on social metrics."""
        metadata = item.get('metadata', {})
        source_type = item.get('source_type', '')
        
        # Source-specific engagement calculation
        if source_type == 'youtube':
            views = metadata.get('views', 0)
            likes = metadata.get('likes', 0)
            
            # Normalize based on typical YouTube metrics
            view_score = min(math.log10(max(views, 1)) / 6, 1.0)  # Log scale up to 1M views
            like_ratio = likes / max(views, 1) if views > 0 else 0
            like_score = min(like_ratio * 100, 1.0)  # Up to 1% like ratio
            
            return (view_score * 0.7 + like_score * 0.3)
            
        elif source_type == 'reddit':
            score = metadata.get('score', 0)
            comments = metadata.get('comments', 0)
            upvote_ratio = metadata.get('upvote_ratio', 0.5)
            
            # Normalize Reddit metrics
            score_normalized = min(math.log10(max(score, 1)) / 4, 1.0)  # Log scale up to 10k
            comment_score = min(math.log10(max(comments, 1)) / 3, 1.0)  # Log scale up to 1k
            
            return (score_normalized * 0.4 + comment_score * 0.3 + upvote_ratio * 0.3)
            
        elif source_type == 'twitter':
            retweets = metadata.get('retweets', 0)
            likes = metadata.get('likes', 0)
            replies = metadata.get('replies', 0)
            
            # Normalize Twitter metrics
            retweet_score = min(math.log10(max(retweets, 1)) / 4, 1.0)
            like_score = min(math.log10(max(likes, 1)) / 4, 1.0)
            reply_score = min(math.log10(max(replies, 1)) / 3, 1.0)
            
            return (retweet_score * 0.4 + like_score * 0.4 + reply_score * 0.2)
            
        elif source_type == 'news':
            # For news, engagement is harder to measure
            # Use word count as a proxy for article depth
            word_count = len(item.get('content', '').split())
            
            # Optimal article length around 800-1200 words
            if 800 <= word_count <= 1200:
                return 1.0
            elif word_count < 200:
                return 0.3  # Too short
            elif word_count > 3000:
                return 0.6  # Too long
            else:
                return 0.7  # Reasonable length
                
        else:
            # Default engagement score for other sources
            return 0.5
    
    def _calculate_source_boost(self, item: Dict[str, Any]) -> float:
        """Calculate source-specific boost factors."""
        source_type = item.get('source_type', '')
        
        # Base boost from configuration
        base_boost = self.boost_factors.get(source_type, 1.0)
        
        # Additional boosts based on content characteristics
        additional_boost = 1.0
        
        # Boost for verified or authoritative sources
        metadata = item.get('metadata', {})
        if metadata.get('verified', False):
            additional_boost *= 1.2
        
        # Boost for academic or research content
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        if any(term in title + content for term in ['research', 'study', 'analysis', 'peer-reviewed']):
            additional_boost *= 1.1
        
        # Penalty for potential spam or low-quality indicators
        if any(term in title for term in ['click here', 'you won\'t believe', 'shocking']):
            additional_boost *= 0.8
        
        return base_boost * additional_boost
    
    def get_scoring_explanation(self, item: Dict[str, Any]) -> str:
        """Generate human-readable explanation of the scoring."""
        score_data = item.get('score', {})
        
        if not score_data:
            return "No scoring data available"
        
        explanations = []
        
        # Relevance explanation
        relevance = score_data.get('relevance', 0)
        if relevance >= 0.8:
            explanations.append("highly relevant")
        elif relevance >= 0.6:
            explanations.append("moderately relevant")
        elif relevance >= 0.4:
            explanations.append("somewhat relevant")
        else:
            explanations.append("low relevance")
        
        # Credibility explanation
        credibility = score_data.get('credibility', 0)
        if credibility >= 0.8:
            explanations.append("high credibility")
        elif credibility >= 0.6:
            explanations.append("moderate credibility")
        else:
            explanations.append("questionable credibility")
        
        # Recency explanation
        recency = score_data.get('recency', 0)
        if recency >= 0.8:
            explanations.append("very recent")
        elif recency >= 0.6:
            explanations.append("recent")
        elif recency >= 0.4:
            explanations.append("somewhat dated")
        else:
            explanations.append("old content")
        
        # Engagement explanation
        engagement = score_data.get('engagement', 0)
        if engagement >= 0.7:
            explanations.append("high engagement")
        elif engagement >= 0.5:
            explanations.append("moderate engagement")
        
        composite = score_data.get('composite', 0)
        
        return f"Score: {composite:.2f} - {', '.join(explanations)}"
    
    def _detect_entity_type(self, item: Dict[str, Any]) -> Optional[str]:
        """Detect if the content is about a known entity type."""
        query = item.get('metadata', {}).get('search_query', '').lower()
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        for entity_type, entities in self.entity_types.items():
            # Check if query matches any entity
            if any(entity in query for entity in entities):
                return entity_type
            
            # Check if title or content has strong entity presence
            entity_mentions = sum(1 for entity in entities if entity in title or entity in content)
            if entity_mentions >= 2:  # Multiple mentions indicate strong relevance
                return entity_type
        
        return None
