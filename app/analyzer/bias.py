"""
Bias analysis module for detecting potential bias and perspective in content.
"""

import asyncio
from typing import Dict, Any, Optional, List
import re
from collections import Counter


class BiasAnalyzer:
    """Analyzes content for potential bias indicators and perspective."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the bias analyzer.
        
        Args:
            config: Configuration dictionary with bias analysis settings
        """
        self.config = config or {}
        self.sensitivity = self.config.get('sensitivity', 0.5)
        
        # Political bias indicators
        self.political_indicators = {
            'left_leaning': {
                'progressive', 'liberal', 'democratic', 'social justice', 'equality',
                'climate change', 'gun control', 'healthcare reform', 'immigration rights',
                'minimum wage', 'wealth inequality', 'systemic racism', 'lgbtq rights'
            },
            'right_leaning': {
                'conservative', 'republican', 'traditional values', 'free market',
                'second amendment', 'border security', 'law and order', 'fiscal responsibility',
                'religious freedom', 'family values', 'small government', 'patriotic'
            }
        }
        
        # Emotional bias indicators
        self.emotional_bias = {
            'highly_emotional': {
                'outrageous', 'shocking', 'devastating', 'explosive', 'scandalous',
                'unbelievable', 'horrific', 'disgusting', 'appalling', 'catastrophic'
            },
            'loaded_language': {
                'radical', 'extremist', 'terrorist', 'criminal', 'corrupt', 'evil',
                'dangerous', 'threat', 'crisis', 'disaster', 'failure', 'betrayal'
            }
        }
        
        # Source bias indicators
        self.source_bias = {
            'opinion_markers': {
                'i think', 'i believe', 'in my opinion', 'personally', 'i feel',
                'it seems to me', 'from my perspective', 'i would argue'
            },
            'certainty_markers': {
                'definitely', 'certainly', 'obviously', 'clearly', 'undoubtedly',
                'without question', 'absolutely', 'unquestionably'
            }
        }
        
        # Gender bias indicators
        self.gender_bias = {
            'gendered_language': {
                'bossy', 'shrill', 'emotional', 'hysterical', 'aggressive',
                'ambitious', 'assertive', 'confident', 'strong-willed'
            }
        }
    
    async def analyze(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze bias in the given content.
        
        Args:
            content: Content dictionary with title, content, source, etc.
            
        Returns:
            Dictionary containing bias analysis results
        """
        # Extract content fields
        title = content.get('title', '')
        text_content = content.get('content', '')
        source = content.get('source', '')
        author = content.get('author', '')
        
        # Combine text for analysis
        full_text = f"{title} {text_content}".lower()
        
        # Analyze different types of bias
        political_bias = self._analyze_political_bias(full_text)
        emotional_bias = self._analyze_emotional_bias(full_text)
        source_bias = self._analyze_source_bias(full_text)
        gender_bias = self._analyze_gender_bias(full_text)
        
        # Calculate overall bias score
        bias_indicators = (
            political_bias['score'] +
            emotional_bias['score'] +
            source_bias['score'] +
            gender_bias['score']
        ) / 4
        
        # Determine bias level
        if bias_indicators >= 0.7:
            level = 'high'
        elif bias_indicators >= 0.4:
            level = 'moderate'
        elif bias_indicators >= 0.2:
            level = 'low'
        else:
            level = 'minimal'
        
        # Generate explanation
        explanation = self._generate_explanation(
            political_bias, emotional_bias, source_bias, gender_bias
        )
        
        # Identify specific bias types detected
        bias_types = self._identify_bias_types(
            political_bias, emotional_bias, source_bias, gender_bias
        )
        
        return {
            'score': round(bias_indicators, 3),
            'level': level,
            'explanation': explanation,
            'bias_types': bias_types,
            'components': {
                'political': political_bias,
                'emotional': emotional_bias,
                'source': source_bias,
                'gender': gender_bias
            }
        }
    
    def _analyze_political_bias(self, text: str) -> Dict[str, Any]:
        """Analyze political bias indicators."""
        left_matches = sum(1 for term in self.political_indicators['left_leaning'] 
                          if term in text)
        right_matches = sum(1 for term in self.political_indicators['right_leaning'] 
                           if term in text)
        
        total_matches = left_matches + right_matches
        
        if total_matches == 0:
            return {
                'score': 0.0,
                'direction': 'neutral',
                'confidence': 0.0,
                'indicators': []
            }
        
        # Calculate bias direction and strength
        if left_matches > right_matches:
            direction = 'left'
            bias_strength = (left_matches - right_matches) / total_matches
        elif right_matches > left_matches:
            direction = 'right'
            bias_strength = (right_matches - left_matches) / total_matches
        else:
            direction = 'neutral'
            bias_strength = 0.0
        
        # Score based on total political language and bias strength
        score = min((total_matches / 10) * (1 + bias_strength), 1.0)
        
        return {
            'score': round(score, 3),
            'direction': direction,
            'confidence': round(bias_strength, 3),
            'indicators': {
                'left_count': left_matches,
                'right_count': right_matches
            }
        }
    
    def _analyze_emotional_bias(self, text: str) -> Dict[str, Any]:
        """Analyze emotional bias and loaded language."""
        emotional_matches = sum(1 for term in self.emotional_bias['highly_emotional'] 
                               if term in text)
        loaded_matches = sum(1 for term in self.emotional_bias['loaded_language'] 
                            if term in text)
        
        total_emotional = emotional_matches + loaded_matches
        
        # Calculate emotional bias score
        score = min(total_emotional / 5, 1.0)
        
        return {
            'score': round(score, 3),
            'emotional_words': emotional_matches,
            'loaded_language': loaded_matches,
            'total_indicators': total_emotional
        }
    
    def _analyze_source_bias(self, text: str) -> Dict[str, Any]:
        """Analyze source bias and subjectivity."""
        opinion_matches = sum(1 for term in self.source_bias['opinion_markers'] 
                             if term in text)
        certainty_matches = sum(1 for term in self.source_bias['certainty_markers'] 
                               if term in text)
        
        # Check for first-person pronouns
        first_person = len(re.findall(r'\b(i|me|my|mine|myself)\b', text))
        
        # Calculate subjectivity score
        total_subjective = opinion_matches + certainty_matches + (first_person / 5)
        score = min(total_subjective / 5, 1.0)
        
        return {
            'score': round(score, 3),
            'opinion_markers': opinion_matches,
            'certainty_markers': certainty_matches,
            'first_person_count': first_person
        }
    
    def _analyze_gender_bias(self, text: str) -> Dict[str, Any]:
        """Analyze potential gender bias in language."""
        gendered_matches = sum(1 for term in self.gender_bias['gendered_language'] 
                              if term in text)
        
        # Check for gendered pronouns imbalance
        he_count = len(re.findall(r'\bhe\b', text))
        she_count = len(re.findall(r'\bshe\b', text))
        
        pronoun_imbalance = 0
        if he_count + she_count > 0:
            pronoun_imbalance = abs(he_count - she_count) / (he_count + she_count)
        
        # Calculate gender bias score
        score = min((gendered_matches / 3) + (pronoun_imbalance * 0.5), 1.0)
        
        return {
            'score': round(score, 3),
            'gendered_language': gendered_matches,
            'pronoun_imbalance': round(pronoun_imbalance, 3),
            'he_count': he_count,
            'she_count': she_count
        }
    
    def _identify_bias_types(
        self, 
        political: Dict, 
        emotional: Dict, 
        source: Dict, 
        gender: Dict
    ) -> List[str]:
        """Identify specific types of bias detected."""
        bias_types = []
        
        if political['score'] > 0.3:
            if political['direction'] != 'neutral':
                bias_types.append(f"political_{political['direction']}")
            else:
                bias_types.append('political_language')
        
        if emotional['score'] > 0.3:
            bias_types.append('emotional_bias')
        
        if source['score'] > 0.3:
            bias_types.append('subjective_language')
        
        if gender['score'] > 0.3:
            bias_types.append('gender_bias')
        
        return bias_types
    
    def _generate_explanation(
        self, 
        political: Dict, 
        emotional: Dict, 
        source: Dict, 
        gender: Dict
    ) -> str:
        """Generate human-readable explanation of bias analysis."""
        explanations = []
        
        if political['score'] > 0.3:
            if political['direction'] != 'neutral':
                explanations.append(f"{political['direction']}-leaning political language")
            else:
                explanations.append("political language detected")
        
        if emotional['score'] > 0.3:
            explanations.append("emotional or loaded language")
        
        if source['score'] > 0.3:
            explanations.append("subjective or opinion-based language")
        
        if gender['score'] > 0.3:
            explanations.append("potential gender bias in language")
        
        if not explanations:
            return "Minimal bias detected - relatively neutral language"
        
        return f"Bias indicators: {', '.join(explanations)}"
    
    async def analyze_batch(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze bias for a batch of content items.
        
        Args:
            contents: List of content dictionaries
            
        Returns:
            List of bias analysis results
        """
        tasks = [self.analyze(content) for content in contents]
        return await asyncio.gather(*tasks)
