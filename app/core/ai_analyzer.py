"""AI-powered analyzer for advanced content analysis and insights."""

from typing import List, Dict, Any, Optional
import re
import asyncio
import logging
from datetime import datetime
from collections import Counter
import json

class AIAnalyzer:
    """Advanced AI analyzer for content understanding and insights."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AI analyzer."""
        self.config = config or {}
        
    async def analyze_topic_comprehensively(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comprehensive AI analysis of search results for a topic."""
        
        print(f"AI Analysis: Processing {len(results)} results for '{query}'")
        
        # Combine all content for analysis
        all_content = []
        for result in results:
            content = f"{result.get('title', '')} {result.get('content', '')}"
            all_content.append(content)
        
        combined_text = " ".join(all_content).lower()
        
        # Perform various AI analyses
        analyses = await asyncio.gather(
            self._extract_key_entities(query, combined_text),
            self._analyze_topic_sentiment(combined_text),
            self._identify_key_themes(query, combined_text),
            self._detect_trends_and_patterns(combined_text),
            self._assess_information_completeness(query, results),
            self._generate_topic_summary(query, results),
            return_exceptions=True
        )
        
        entities, sentiment, themes, trends, completeness, summary = analyses
        
        return {
            'query_analysis': {
                'search_term': query,
                'results_count': len(results),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'entities': entities if not isinstance(entities, Exception) else {},
            'sentiment_analysis': sentiment if not isinstance(sentiment, Exception) else {},
            'key_themes': themes if not isinstance(themes, Exception) else [],
            'trends_patterns': trends if not isinstance(trends, Exception) else {},
            'completeness_score': completeness if not isinstance(completeness, Exception) else 0,
            'ai_summary': summary if not isinstance(summary, Exception) else "",
            'insights': await self._generate_insights(query, results)
        }
    
    async def _extract_key_entities(self, query: str, text: str) -> Dict[str, Any]:
        """Extract key entities (people, places, organizations) from content."""
        try:
            entities = {
                'people': [],
                'organizations': [],
                'locations': [],
                'topics': [],
                'technologies': []
            }
            
            # Simple pattern matching for entities
            # People (names with capital letters)
            people_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
            people = re.findall(people_pattern, text)
            entities['people'] = list(set(people))[:10]
            
            # Organizations (common org patterns)
            org_keywords = ['company', 'corporation', 'inc', 'ltd', 'org', 'foundation', 'institute', 'university', 'college']
            org_pattern = r'\b[A-Z][A-Za-z\s]+(?:' + '|'.join(org_keywords) + r')\b'
            orgs = re.findall(org_pattern, text, re.IGNORECASE)
            entities['organizations'] = list(set(orgs))[:10]
            
            # Locations (countries, cities)
            location_keywords = ['city', 'country', 'state', 'nation', 'capital', 'metropolitan']
            location_pattern = r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:\s(?:' + '|'.join(location_keywords) + r'))\b'
            locations = re.findall(location_pattern, text, re.IGNORECASE)
            entities['locations'] = list(set(locations))[:10]
            
            # Technology terms
            tech_keywords = ['ai', 'artificial intelligence', 'machine learning', 'blockchain', 'cryptocurrency', 'bitcoin', 'ethereum', 'nft', 'cloud', 'api', 'software', 'app', 'platform', 'algorithm', 'data', 'neural network']
            found_tech = [term for term in tech_keywords if term in text.lower()]
            entities['technologies'] = found_tech[:10]
            
            # Extract topics related to query
            query_words = query.lower().split()
            topics = []
            for word in query_words:
                if len(word) > 3:
                    # Find related terms
                    pattern = rf'\b\w*{re.escape(word)}\w*\b'
                    related = re.findall(pattern, text, re.IGNORECASE)
                    topics.extend(related[:5])
            entities['topics'] = list(set(topics))[:15]
            
            return entities
            
        except Exception as e:
            logging.error(f"Error extracting entities: {e}")
            return {}
    
    async def _analyze_topic_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment around the topic."""
        try:
            # Simple sentiment analysis using keyword matching
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'positive', 'successful', 'beneficial', 'improved', 'growth', 'increase', 'rising', 'up', 'high', 'strong', 'win', 'victory', 'achievement']
            negative_words = ['bad', 'terrible', 'awful', 'negative', 'decline', 'decrease', 'falling', 'down', 'low', 'weak', 'loss', 'failure', 'problem', 'issue', 'crisis', 'concern', 'worry', 'risk', 'threat', 'danger']
            neutral_words = ['neutral', 'stable', 'unchanged', 'steady', 'consistent', 'normal', 'average', 'standard']
            
            words = text.lower().split()
            
            positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
            negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
            neutral_count = sum(1 for word in words if any(neu in word for neu in neutral_words))
            
            total_sentiment_words = positive_count + negative_count + neutral_count
            
            if total_sentiment_words == 0:
                return {'overall': 'neutral', 'confidence': 0.5, 'breakdown': {'positive': 0, 'negative': 0, 'neutral': 0}}
            
            positive_ratio = positive_count / total_sentiment_words
            negative_ratio = negative_count / total_sentiment_words
            neutral_ratio = neutral_count / total_sentiment_words
            
            if positive_ratio > negative_ratio and positive_ratio > neutral_ratio:
                overall = 'positive'
                confidence = positive_ratio
            elif negative_ratio > positive_ratio and negative_ratio > neutral_ratio:
                overall = 'negative'
                confidence = negative_ratio
            else:
                overall = 'neutral'
                confidence = max(neutral_ratio, 0.5)
            
            return {
                'overall': overall,
                'confidence': round(confidence, 2),
                'breakdown': {
                    'positive': round(positive_ratio, 2),
                    'negative': round(negative_ratio, 2),
                    'neutral': round(neutral_ratio, 2)
                },
                'sentiment_indicators': {
                    'positive_signals': positive_count,
                    'negative_signals': negative_count,
                    'neutral_signals': neutral_count
                }
            }
            
        except Exception as e:
            logging.error(f"Error analyzing sentiment: {e}")
            return {}
    
    async def _identify_key_themes(self, query: str, text: str) -> List[Dict[str, Any]]:
        """Identify key themes and topics in the content."""
        try:
            # Word frequency analysis
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            word_freq = Counter(words)
            
            # Common stop words to exclude
            stop_words = {'that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'what', 'when', 'where', 'which', 'more', 'some', 'time', 'very', 'than', 'them', 'well', 'just'}
            
            # Filter out stop words and get top themes
            themes = []
            for word, freq in word_freq.most_common(20):
                if word not in stop_words and len(word) > 3:
                    importance = min(freq / len(words) * 100, 10)  # Cap importance at 10
                    themes.append({
                        'theme': word,
                        'frequency': freq,
                        'importance': round(importance, 2),
                        'relevance_to_query': self._calculate_theme_relevance(word, query)
                    })
            
            return themes[:15]
            
        except Exception as e:
            logging.error(f"Error identifying themes: {e}")
            return []
    
    def _calculate_theme_relevance(self, theme: str, query: str) -> float:
        """Calculate how relevant a theme is to the original query."""
        query_words = query.lower().split()
        theme_lower = theme.lower()
        
        # Direct match
        if theme_lower in query.lower():
            return 1.0
        
        # Partial match
        relevance = 0.0
        for word in query_words:
            if word in theme_lower or theme_lower in word:
                relevance += 0.3
        
        return min(relevance, 1.0)
    
    async def _detect_trends_and_patterns(self, text: str) -> Dict[str, Any]:
        """Detect trends and patterns in the content."""
        try:
            patterns = {}
            
            # Time-based patterns
            time_indicators = ['recent', 'new', 'latest', 'updated', 'current', 'today', 'yesterday', 'this week', 'this month', 'this year']
            time_mentions = sum(1 for indicator in time_indicators if indicator in text.lower())
            patterns['recency_focus'] = time_mentions > 5
            
            # Growth/decline patterns
            growth_terms = ['increase', 'growth', 'rising', 'up', 'surge', 'boom', 'expansion']
            decline_terms = ['decrease', 'decline', 'falling', 'down', 'drop', 'crash', 'reduction']
            
            growth_mentions = sum(1 for term in growth_terms if term in text.lower())
            decline_mentions = sum(1 for term in decline_terms if term in text.lower())
            
            if growth_mentions > decline_mentions:
                patterns['trend_direction'] = 'growth'
            elif decline_mentions > growth_mentions:
                patterns['trend_direction'] = 'decline'
            else:
                patterns['trend_direction'] = 'stable'
            
            # Innovation patterns
            innovation_terms = ['innovation', 'breakthrough', 'new technology', 'advancement', 'revolutionary', 'cutting-edge']
            innovation_score = sum(1 for term in innovation_terms if term in text.lower())
            patterns['innovation_level'] = 'high' if innovation_score > 3 else 'medium' if innovation_score > 1 else 'low'
            
            # Market/business patterns
            business_terms = ['market', 'business', 'company', 'revenue', 'profit', 'investment', 'funding']
            business_focus = sum(1 for term in business_terms if term in text.lower())
            patterns['business_focus'] = business_focus > 5
            
            return patterns
            
        except Exception as e:
            logging.error(f"Error detecting patterns: {e}")
            return {}
    
    async def _assess_information_completeness(self, query: str, results: List[Dict[str, Any]]) -> float:
        """Assess how complete the information is for the query."""
        try:
            # Factors that indicate completeness
            score = 0.0
            
            # Number of sources
            source_count = len(set(result.get('source', '') for result in results))
            score += min(source_count / 5, 0.3)  # Max 0.3 for having 5+ sources
            
            # Content length
            total_content_length = sum(len(result.get('content', '')) for result in results)
            score += min(total_content_length / 2000, 0.2)  # Max 0.2 for having 2000+ chars
            
            # Source diversity
            source_types = set(result.get('source_type', '') for result in results)
            score += min(len(source_types) / 4, 0.2)  # Max 0.2 for having 4+ types
            
            # Query coverage
            query_words = query.lower().split()
            covered_words = 0
            all_content = ' '.join(result.get('content', '') for result in results).lower()
            
            for word in query_words:
                if len(word) > 2 and word in all_content:
                    covered_words += 1
            
            query_coverage = covered_words / len(query_words) if query_words else 0
            score += query_coverage * 0.3  # Max 0.3 for full query coverage
            
            return min(score, 1.0)
            
        except Exception as e:
            logging.error(f"Error assessing completeness: {e}")
            return 0.5
    
    async def _generate_topic_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate an AI-powered summary of the topic."""
        try:
            if not results:
                return f"No information found for '{query}'."
            
            # Extract key points from results
            key_points = []
            for result in results[:5]:  # Top 5 results
                title = result.get('title', '')
                content = result.get('content', '')
                if title and content:
                    # Extract first sentence or key point
                    sentences = content.split('.')
                    if sentences:
                        key_points.append(sentences[0].strip())
            
            # Create summary structure
            summary_parts = []
            summary_parts.append(f"Based on current information about '{query}':")
            
            if key_points:
                summary_parts.append(f"\n\nKey findings:")
                for i, point in enumerate(key_points[:3], 1):
                    if point:
                        summary_parts.append(f"{i}. {point}")
            
            # Add source count
            source_count = len(set(result.get('source', '') for result in results))
            summary_parts.append(f"\n\nThis analysis is based on {len(results)} results from {source_count} different sources.")
            
            return ' '.join(summary_parts)
            
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return f"Summary generation failed for '{query}', but {len(results)} results were found."
    
    async def _generate_insights(self, query: str, results: List[Dict[str, Any]]) -> List[str]:
        """Generate AI-powered insights about the topic."""
        try:
            insights = []
            
            if not results:
                insights.append(f"Limited information available for '{query}' - consider refining your search terms.")
                return insights
            
            # Source diversity insight
            sources = [result.get('source', '') for result in results]
            unique_sources = set(sources)
            if len(unique_sources) > 5:
                insights.append(f"Information comes from {len(unique_sources)} diverse sources, indicating good coverage.")
            elif len(unique_sources) < 3:
                insights.append("Information sources are limited - consider additional verification.")
            
            # Content recency insight
            recent_keywords = ['today', 'recently', 'new', 'latest', 'current']
            recent_count = 0
            for result in results:
                content = result.get('content', '').lower()
                if any(keyword in content for keyword in recent_keywords):
                    recent_count += 1
            
            if recent_count > len(results) * 0.5:
                insights.append("Topic appears to be current with recent developments.")
            
            # Credibility insight
            high_cred_count = sum(1 for result in results if result.get('credibility_info', {}).get('score', 0) > 85)
            if high_cred_count > len(results) * 0.6:
                insights.append("Information comes from highly credible sources.")
            elif high_cred_count < len(results) * 0.3:
                insights.append("Consider verifying information from additional authoritative sources.")
            
            # Topic complexity insight
            all_content = ' '.join(result.get('content', '') for result in results)
            complex_terms = ['analysis', 'research', 'study', 'investigation', 'comprehensive', 'detailed']
            if sum(1 for term in complex_terms if term in all_content.lower()) > 5:
                insights.append("Topic involves complex or technical information requiring careful interpretation.")
            
            return insights
            
        except Exception as e:
            logging.error(f"Error generating insights: {e}")
            return [f"AI insights could not be generated for '{query}'"] 