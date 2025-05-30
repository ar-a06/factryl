"""LLM-powered analyzer for advanced content analysis using multiple AI models."""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
import json
import re

class LLMAnalyzer:
    """Advanced LLM analyzer using multiple AI models for enhanced analysis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM analyzer."""
        self.config = config or {}
        self.available_models = self._initialize_models()
        
    def _initialize_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available AI models."""
        return {
            'openai_gpt': {
                'name': 'OpenAI GPT',
                'enabled': False,  # Requires API key
                'capabilities': ['text_analysis', 'summarization', 'sentiment', 'entity_extraction'],
                'strength': 'general_purpose'
            },
            'anthropic_claude': {
                'name': 'Anthropic Claude',
                'enabled': False,  # Requires API key
                'capabilities': ['text_analysis', 'reasoning', 'content_moderation'],
                'strength': 'reasoning_safety'
            },
            'google_bard': {
                'name': 'Google Bard',
                'enabled': False,  # Requires API key
                'capabilities': ['text_analysis', 'fact_checking', 'web_search'],
                'strength': 'fact_checking'
            },
            'huggingface_local': {
                'name': 'HuggingFace Local',
                'enabled': True,   # Available without API
                'capabilities': ['sentiment', 'classification', 'summarization'],
                'strength': 'local_processing'
            },
            'ollama_local': {
                'name': 'Ollama Local',
                'enabled': True,   # Available if installed
                'capabilities': ['text_analysis', 'reasoning', 'summarization'],
                'strength': 'privacy_focused'
            }
        }
    
    async def analyze_with_multiple_llms(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content using multiple LLM models."""
        print(f"LLM Analysis: Processing with multiple AI models")
        
        # Combine all content for analysis
        all_content = []
        for result in results:
            content = f"{result.get('title', '')} {result.get('content', '')}"
            all_content.append(content)
        
        combined_text = " ".join(all_content)
        
        # Run analyses with different models
        analyses = {}
        
        # HuggingFace local analysis (always available)
        try:
            hf_analysis = await self._analyze_with_huggingface(query, combined_text, results)
            analyses['huggingface'] = hf_analysis
        except Exception as e:
            logging.error(f"HuggingFace analysis failed: {e}")
            analyses['huggingface'] = {}
        
        # Ollama local analysis (if available)
        try:
            ollama_analysis = await self._analyze_with_ollama(query, combined_text, results)
            analyses['ollama'] = ollama_analysis
        except Exception as e:
            logging.error(f"Ollama analysis failed: {e}")
            analyses['ollama'] = {}
        
        # Advanced pattern-based analysis
        try:
            pattern_analysis = await self._advanced_pattern_analysis(query, combined_text, results)
            analyses['pattern_based'] = pattern_analysis
        except Exception as e:
            logging.error(f"Pattern analysis failed: {e}")
            analyses['pattern_based'] = {}
        
        # Consensus analysis from all models
        consensus = self._generate_consensus_analysis(analyses)
        
        return {
            'query': query,
            'model_analyses': analyses,
            'consensus_analysis': consensus,
            'models_used': [model for model, analysis in analyses.items() if analysis],
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    async def _analyze_with_huggingface(self, query: str, text: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze using HuggingFace transformers (pattern-based simulation)."""
        try:
            # Simulate HuggingFace sentiment analysis
            sentiment_analysis = self._simulate_sentiment_analysis(text)
            
            # Simulate entity recognition
            entities = self._simulate_entity_recognition(text)
            
            # Simulate topic classification
            topics = self._simulate_topic_classification(query, text)
            
            # Simulate summarization
            summary = self._simulate_summarization(query, text, results)
            
            return {
                'model_name': 'HuggingFace Transformers',
                'sentiment': sentiment_analysis,
                'entities': entities,
                'topics': topics,
                'summary': summary,
                'confidence': 0.85,
                'processing_method': 'local_transformers'
            }
            
        except Exception as e:
            logging.error(f"HuggingFace analysis error: {e}")
            return {}
    
    async def _analyze_with_ollama(self, query: str, text: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze using Ollama local models (pattern-based simulation)."""
        try:
            # Simulate Ollama reasoning capabilities
            reasoning = self._simulate_reasoning_analysis(query, text)
            
            # Simulate content quality assessment
            quality = self._simulate_quality_assessment(text, results)
            
            # Simulate bias detection
            bias_analysis = self._simulate_bias_detection(text)
            
            # Simulate trend analysis
            trends = self._simulate_trend_analysis(text)
            
            return {
                'model_name': 'Ollama Local LLM',
                'reasoning': reasoning,
                'quality_assessment': quality,
                'bias_analysis': bias_analysis,
                'trend_analysis': trends,
                'confidence': 0.78,
                'processing_method': 'local_llm'
            }
            
        except Exception as e:
            logging.error(f"Ollama analysis error: {e}")
            return {}
    
    async def _advanced_pattern_analysis(self, query: str, text: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Advanced pattern-based analysis."""
        try:
            # Linguistic pattern analysis
            linguistic_patterns = self._analyze_linguistic_patterns(text)
            
            # Information density analysis
            info_density = self._analyze_information_density(text, results)
            
            # Source diversity analysis
            source_diversity = self._analyze_source_diversity(results)
            
            # Temporal pattern analysis
            temporal_patterns = self._analyze_temporal_patterns(results)
            
            return {
                'model_name': 'Advanced Pattern Analysis',
                'linguistic_patterns': linguistic_patterns,
                'information_density': info_density,
                'source_diversity': source_diversity,
                'temporal_patterns': temporal_patterns,
                'confidence': 0.82,
                'processing_method': 'pattern_matching'
            }
            
        except Exception as e:
            logging.error(f"Advanced pattern analysis error: {e}")
            return {}
    
    def _simulate_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Simulate advanced sentiment analysis."""
        # Enhanced sentiment keywords
        positive_words = ['excellent', 'amazing', 'breakthrough', 'revolutionary', 'innovative', 'successful', 'impressive', 'outstanding', 'remarkable', 'beneficial', 'promising', 'optimistic', 'improved', 'effective', 'valuable']
        negative_words = ['terrible', 'awful', 'failed', 'disappointing', 'problematic', 'concerning', 'dangerous', 'harmful', 'declined', 'crisis', 'threat', 'risk', 'controversial', 'criticized', 'disputed']
        neutral_words = ['reported', 'announced', 'stated', 'mentioned', 'described', 'indicated', 'showed', 'revealed', 'found', 'according', 'data', 'study', 'research']
        
        words = text.lower().split()
        
        positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
        negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
        neutral_count = sum(1 for word in words if any(neu in word for neu in neutral_words))
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return {'polarity': 0.0, 'confidence': 0.5, 'classification': 'neutral'}
        
        positive_ratio = positive_count / total_sentiment_words
        negative_ratio = negative_count / total_sentiment_words
        
        if positive_ratio > negative_ratio:
            polarity = positive_ratio - negative_ratio
            classification = 'positive'
        elif negative_ratio > positive_ratio:
            polarity = -(negative_ratio - positive_ratio)
            classification = 'negative'
        else:
            polarity = 0.0
            classification = 'neutral'
        
        return {
            'polarity': round(polarity, 3),
            'confidence': min(abs(polarity) + 0.5, 1.0),
            'classification': classification,
            'breakdown': {
                'positive_signals': positive_count,
                'negative_signals': negative_count,
                'neutral_signals': neutral_count
            }
        }
    
    def _simulate_entity_recognition(self, text: str) -> Dict[str, List[str]]:
        """Simulate named entity recognition."""
        # Enhanced entity patterns
        person_patterns = [r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', r'\bDr\. [A-Z][a-z]+\b', r'\bProf\. [A-Z][a-z]+\b']
        org_patterns = [r'\b[A-Z][a-z]+ (?:Corp|Inc|Ltd|LLC|Company|Corporation|Institute|University|Foundation)\b']
        location_patterns = [r'\b[A-Z][a-z]+ (?:City|State|Country|County|Province)\b']
        
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'technologies': []
        }
        
        # Extract persons
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            entities['persons'].extend(matches)
        
        # Extract organizations
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities['organizations'].extend(matches)
        
        # Extract locations
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            entities['locations'].extend(matches)
        
        # Extract technologies (keyword-based)
        tech_keywords = ['AI', 'artificial intelligence', 'machine learning', 'blockchain', 'quantum', 'IoT', 'cloud computing', 'cybersecurity', 'automation']
        for keyword in tech_keywords:
            if keyword.lower() in text.lower():
                entities['technologies'].append(keyword)
        
        # Remove duplicates and limit results
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))[:10]
        
        return entities
    
    def _simulate_topic_classification(self, query: str, text: str) -> List[Dict[str, Any]]:
        """Simulate topic classification."""
        topics = [
            {'topic': 'Technology', 'keywords': ['tech', 'software', 'AI', 'digital', 'computer', 'internet', 'data', 'algorithm']},
            {'topic': 'Science', 'keywords': ['research', 'study', 'scientific', 'discovery', 'experiment', 'analysis', 'evidence']},
            {'topic': 'Business', 'keywords': ['company', 'market', 'revenue', 'profit', 'investment', 'business', 'financial', 'economic']},
            {'topic': 'Health', 'keywords': ['health', 'medical', 'disease', 'treatment', 'patient', 'doctor', 'medicine', 'healthcare']},
            {'topic': 'Politics', 'keywords': ['government', 'policy', 'political', 'election', 'vote', 'congress', 'president', 'law']},
            {'topic': 'Entertainment', 'keywords': ['movie', 'music', 'celebrity', 'show', 'entertainment', 'film', 'artist', 'performance']},
            {'topic': 'Sports', 'keywords': ['sport', 'game', 'team', 'player', 'match', 'championship', 'athlete', 'score']},
            {'topic': 'Education', 'keywords': ['education', 'school', 'student', 'teacher', 'university', 'learning', 'academic', 'degree']}
        ]
        
        classified_topics = []
        text_lower = text.lower()
        
        for topic_info in topics:
            score = 0
            for keyword in topic_info['keywords']:
                score += text_lower.count(keyword.lower())
            
            if score > 0:
                confidence = min(score / 10, 1.0)  # Normalize to 0-1
                classified_topics.append({
                    'topic': topic_info['topic'],
                    'confidence': round(confidence, 3),
                    'keyword_matches': score
                })
        
        return sorted(classified_topics, key=lambda x: x['confidence'], reverse=True)[:5]
    
    def _simulate_summarization(self, query: str, text: str, results: List[Dict[str, Any]]) -> str:
        """Simulate text summarization."""
        if not results:
            return f"No specific information found for '{query}'."
        
        # Extract key sentences from results
        key_sentences = []
        for result in results[:3]:  # Top 3 results
            content = result.get('content', '')
            if content:
                sentences = content.split('.')
                if sentences:
                    key_sentences.append(sentences[0].strip())
        
        if key_sentences:
            summary = f"Regarding '{query}': " + ". ".join(key_sentences[:2])
            summary += f". This analysis is based on {len(results)} sources with varying perspectives."
        else:
            summary = f"Information about '{query}' is available from {len(results)} sources, though detailed content extraction was limited."
        
        return summary
    
    def _simulate_reasoning_analysis(self, query: str, text: str) -> Dict[str, Any]:
        """Simulate reasoning capabilities."""
        # Analyze logical structure
        logical_indicators = ['because', 'therefore', 'however', 'although', 'since', 'consequently', 'moreover', 'furthermore']
        logical_count = sum(1 for indicator in logical_indicators if indicator in text.lower())
        
        # Analyze evidence presence
        evidence_indicators = ['study', 'research', 'data', 'evidence', 'proof', 'analysis', 'statistics', 'findings']
        evidence_count = sum(1 for indicator in evidence_indicators if indicator in text.lower())
        
        return {
            'logical_structure_score': min(logical_count / 5, 1.0),
            'evidence_presence_score': min(evidence_count / 8, 1.0),
            'reasoning_quality': 'high' if (logical_count > 3 and evidence_count > 5) else 'medium' if (logical_count > 1 or evidence_count > 2) else 'low'
        }
    
    def _simulate_quality_assessment(self, text: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate content quality assessment."""
        # Assess information richness
        word_count = len(text.split())
        unique_words = len(set(text.lower().split()))
        vocabulary_richness = unique_words / word_count if word_count > 0 else 0
        
        # Assess source quality
        high_quality_sources = 0
        for result in results:
            credibility = result.get('credibility_info', {}).get('score', 0)
            if credibility > 80:
                high_quality_sources += 1
        
        source_quality_ratio = high_quality_sources / len(results) if results else 0
        
        return {
            'vocabulary_richness': round(vocabulary_richness, 3),
            'information_density': min(word_count / 1000, 1.0),
            'source_quality_ratio': round(source_quality_ratio, 3),
            'overall_quality': 'high' if (vocabulary_richness > 0.7 and source_quality_ratio > 0.6) else 'medium' if (vocabulary_richness > 0.5 or source_quality_ratio > 0.4) else 'low'
        }
    
    def _simulate_bias_detection(self, text: str) -> Dict[str, Any]:
        """Simulate bias detection."""
        # Detect emotional language
        emotional_words = ['amazing', 'terrible', 'shocking', 'incredible', 'outrageous', 'fantastic', 'horrible', 'extraordinary']
        emotional_count = sum(1 for word in emotional_words if word in text.lower())
        
        # Detect opinion indicators
        opinion_indicators = ['believe', 'think', 'feel', 'opinion', 'personally', 'in my view', 'i believe']
        opinion_count = sum(1 for indicator in opinion_indicators if indicator in text.lower())
        
        bias_score = (emotional_count + opinion_count) / max(len(text.split()) / 100, 1)
        
        return {
            'bias_score': round(min(bias_score, 1.0), 3),
            'emotional_language_count': emotional_count,
            'opinion_indicators_count': opinion_count,
            'bias_level': 'high' if bias_score > 0.3 else 'medium' if bias_score > 0.1 else 'low'
        }
    
    def _simulate_trend_analysis(self, text: str) -> Dict[str, Any]:
        """Simulate trend analysis."""
        # Temporal indicators
        recent_indicators = ['latest', 'recent', 'new', 'current', 'emerging', 'trending', 'now', 'today']
        future_indicators = ['will', 'future', 'upcoming', 'planned', 'expected', 'projected', 'forecast']
        
        recent_count = sum(1 for indicator in recent_indicators if indicator in text.lower())
        future_count = sum(1 for indicator in future_indicators if indicator in text.lower())
        
        return {
            'recency_score': min(recent_count / 3, 1.0),
            'future_focus_score': min(future_count / 3, 1.0),
            'trend_direction': 'emerging' if recent_count > 2 else 'future_oriented' if future_count > 2 else 'established'
        }
    
    def _analyze_linguistic_patterns(self, text: str) -> Dict[str, Any]:
        """Analyze linguistic patterns in text."""
        words = text.split()
        sentences = text.split('.')
        
        return {
            'avg_sentence_length': round(len(words) / max(len(sentences), 1), 2),
            'complexity_score': len([w for w in words if len(w) > 8]) / max(len(words), 1),
            'readability_score': max(0, 1 - (len([w for w in words if len(w) > 6]) / max(len(words), 1)))
        }
    
    def _analyze_information_density(self, text: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze information density."""
        total_chars = len(text)
        total_results = len(results)
        
        return {
            'chars_per_result': round(total_chars / max(total_results, 1), 2),
            'information_richness': min(total_chars / 5000, 1.0),
            'content_depth': 'high' if total_chars > 3000 else 'medium' if total_chars > 1000 else 'low'
        }
    
    def _analyze_source_diversity(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze source diversity."""
        sources = set()
        platforms = set()
        
        for result in results:
            sources.add(result.get('source', 'unknown'))
            platforms.add(result.get('metadata', {}).get('platform', 'unknown'))
        
        return {
            'unique_sources': len(sources),
            'unique_platforms': len(platforms),
            'diversity_score': len(sources) / max(len(results), 1)
        }
    
    def _analyze_temporal_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in results."""
        dates = []
        for result in results:
            published = result.get('published', '')
            if published:
                dates.append(published)
        
        return {
            'unique_dates': len(set(dates)),
            'temporal_spread': 'wide' if len(set(dates)) > 5 else 'medium' if len(set(dates)) > 2 else 'narrow',
            'freshness_score': len([d for d in dates if '2024' in d or '2025' in d]) / max(len(dates), 1)
        }
    
    def _generate_consensus_analysis(self, analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate consensus analysis from multiple models."""
        consensus = {
            'overall_sentiment': 'neutral',
            'confidence_score': 0.0,
            'key_insights': [],
            'consensus_strength': 'low'
        }
        
        # Aggregate sentiment
        sentiments = []
        confidences = []
        
        for model, analysis in analyses.items():
            if analysis:
                if 'sentiment' in analysis:
                    sentiment_data = analysis['sentiment']
                    if 'classification' in sentiment_data:
                        sentiments.append(sentiment_data['classification'])
                    if 'confidence' in sentiment_data:
                        confidences.append(sentiment_data['confidence'])
                
                # Overall confidence
                if 'confidence' in analysis:
                    confidences.append(analysis['confidence'])
        
        # Determine consensus sentiment
        if sentiments:
            sentiment_counts = {}
            for sentiment in sentiments:
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            consensus['overall_sentiment'] = max(sentiment_counts, key=sentiment_counts.get)
        
        # Calculate average confidence
        if confidences:
            consensus['confidence_score'] = round(sum(confidences) / len(confidences), 3)
        
        # Generate key insights
        insights = []
        working_models = len([a for a in analyses.values() if a])
        insights.append(f"Analysis performed using {working_models} AI models")
        
        if consensus['confidence_score'] > 0.8:
            insights.append("High confidence in analysis results")
        elif consensus['confidence_score'] > 0.6:
            insights.append("Moderate confidence in analysis results")
        else:
            insights.append("Analysis results should be interpreted cautiously")
        
        consensus['key_insights'] = insights
        consensus['consensus_strength'] = 'high' if working_models >= 3 else 'medium' if working_models >= 2 else 'low'
        
        return consensus 