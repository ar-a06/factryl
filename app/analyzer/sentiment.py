"""
Sentiment analysis module for analyzing emotional tone of content.
"""

import asyncio
from typing import Dict, Any, Optional
import re
from textblob import TextBlob


class SentimentAnalyzer:
    """Analyzes sentiment of text content using TextBlob and rule-based approaches."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the sentiment analyzer.
        
        Args:
            config: Configuration dictionary with sentiment analysis settings
        """
        self.config = config or {}
        self.threshold_positive = self.config.get('threshold_positive', 0.1)
        self.threshold_negative = self.config.get('threshold_negative', -0.1)
        
        # Sentiment keywords for rule-based enhancement
        self.positive_keywords = {
            'excellent', 'amazing', 'fantastic', 'great', 'wonderful', 'outstanding',
            'brilliant', 'superb', 'magnificent', 'perfect', 'love', 'awesome',
            'incredible', 'remarkable', 'exceptional', 'marvelous', 'terrific'
        }
        
        self.negative_keywords = {
            'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'worst',
            'pathetic', 'useless', 'disappointing', 'frustrating', 'annoying',
            'ridiculous', 'stupid', 'waste', 'failure', 'disaster', 'nightmare'
        }
    
    async def analyze(self, content: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the given content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        if not content or not content.strip():
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'keywords': []
            }
        
        # Clean the content
        cleaned_content = self._clean_text(content)
        
        # TextBlob analysis
        blob = TextBlob(cleaned_content)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Rule-based enhancement
        keyword_sentiment = self._analyze_keywords(cleaned_content)
        
        # Combine scores (weighted average)
        final_polarity = (polarity * 0.7) + (keyword_sentiment['score'] * 0.3)
        
        # Determine label
        if final_polarity > self.threshold_positive:
            label = 'positive'
        elif final_polarity < self.threshold_negative:
            label = 'negative'
        else:
            label = 'neutral'
        
        # Calculate confidence based on absolute polarity and subjectivity
        confidence = min(abs(final_polarity) + (1 - subjectivity) * 0.3, 1.0)
        
        return {
            'polarity': round(final_polarity, 3),
            'subjectivity': round(subjectivity, 3),
            'label': label,
            'confidence': round(confidence, 3),
            'keywords': keyword_sentiment['keywords']
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis."""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _analyze_keywords(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using keyword matching."""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        positive_matches = words.intersection(self.positive_keywords)
        negative_matches = words.intersection(self.negative_keywords)
        
        # Calculate keyword-based sentiment score
        positive_count = len(positive_matches)
        negative_count = len(negative_matches)
        
        if positive_count + negative_count == 0:
            score = 0.0
        else:
            score = (positive_count - negative_count) / (positive_count + negative_count)
        
        return {
            'score': score,
            'keywords': {
                'positive': list(positive_matches),
                'negative': list(negative_matches)
            }
        }
    
    def analyze_batch(self, contents: list) -> list:
        """
        Analyze sentiment for a batch of content items.
        
        Args:
            contents: List of text content to analyze
            
        Returns:
            List of sentiment analysis results
        """
        return asyncio.run(self._analyze_batch_async(contents))
    
    async def _analyze_batch_async(self, contents: list) -> list:
        """Async batch processing of sentiment analysis."""
        tasks = [self.analyze(content) for content in contents]
        return await asyncio.gather(*tasks)
