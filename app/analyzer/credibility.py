"""
Credibility analysis module for assessing content trustworthiness and reliability.
"""

import asyncio
from typing import Dict, Any, Optional, List
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta


class CredibilityAnalyzer:
    """Analyzes credibility of content based on source, recency, and content quality indicators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the credibility analyzer.
        
        Args:
            config: Configuration dictionary with credibility analysis settings
        """
        self.config = config or {}
        self.min_score = self.config.get('min_score', 0.3)
        self.fact_check_apis = self.config.get('fact_check_apis', [])
        
        # Trusted domains with credibility scores
        self.trusted_domains = {
            # News sources
            'reuters.com': 0.95,
            'bbc.com': 0.95,
            'apnews.com': 0.95,
            'npr.org': 0.90,
            'cnn.com': 0.85,
            'nytimes.com': 0.90,
            'washingtonpost.com': 0.90,
            'theguardian.com': 0.85,
            'wsj.com': 0.90,
            
            # Academic and research
            'arxiv.org': 0.95,
            'pubmed.ncbi.nlm.nih.gov': 0.95,
            'scholar.google.com': 0.90,
            'researchgate.net': 0.85,
            'ieee.org': 0.90,
            'acm.org': 0.90,
            
            # Government sources
            'gov': 0.90,
            'edu': 0.85,
            'org': 0.70,
            
            # Tech sources
            'github.com': 0.80,
            'stackoverflow.com': 0.75,
            'medium.com': 0.60,
            'dev.to': 0.65,
            
            # Social media (lower credibility)
            'twitter.com': 0.40,
            'facebook.com': 0.35,
            'reddit.com': 0.50,
            'quora.com': 0.45,
            'youtube.com': 0.45
        }
        
        # Quality indicators
        self.quality_indicators = {
            'positive': {
                'citations', 'references', 'study', 'research', 'data', 'analysis',
                'peer-reviewed', 'published', 'journal', 'university', 'professor',
                'expert', 'official', 'verified', 'fact-check', 'evidence'
            },
            'negative': {
                'rumor', 'unconfirmed', 'alleged', 'conspiracy', 'hoax', 'fake',
                'misleading', 'clickbait', 'sensational', 'breaking', 'exclusive',
                'shocking', 'you won\'t believe', 'doctors hate this'
            }
        }
    
    async def analyze(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze credibility of the given content.
        
        Args:
            content: Content dictionary with source, URL, title, content, etc.
            
        Returns:
            Dictionary containing credibility analysis results
        """
        # Extract content fields
        url = content.get('url', '')
        source = content.get('source', '')
        title = content.get('title', '')
        text_content = content.get('content', '')
        author = content.get('author', '')
        published_date = content.get('published_date', '')
        
        # Calculate different credibility factors
        domain_score = self._analyze_domain(url)
        source_score = self._analyze_source(source)
        content_score = self._analyze_content_quality(title, text_content)
        recency_score = self._analyze_recency(published_date)
        author_score = self._analyze_author(author)
        
        # Combine scores with weights
        final_score = (
            domain_score * 0.3 +
            source_score * 0.2 +
            content_score * 0.25 +
            recency_score * 0.15 +
            author_score * 0.1
        )
        
        # Determine credibility level
        if final_score >= 0.8:
            level = 'very_high'
        elif final_score >= 0.6:
            level = 'high'
        elif final_score >= 0.4:
            level = 'medium'
        elif final_score >= 0.2:
            level = 'low'
        else:
            level = 'very_low'
        
        # Generate explanation
        explanation = self._generate_explanation(
            final_score, domain_score, source_score, content_score, recency_score
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(title, text_content, url)
        
        return {
            'score': round(final_score, 3),
            'level': level,
            'explanation': explanation,
            'risk_factors': risk_factors,
            'components': {
                'domain_score': round(domain_score, 3),
                'source_score': round(source_score, 3),
                'content_score': round(content_score, 3),
                'recency_score': round(recency_score, 3),
                'author_score': round(author_score, 3)
            }
        }
    
    def _analyze_domain(self, url: str) -> float:
        """Analyze credibility based on domain reputation."""
        if not url:
            return 0.5  # Neutral score for missing URL
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check exact domain matches
            if domain in self.trusted_domains:
                return self.trusted_domains[domain]
            
            # Check TLD-based scoring
            if domain.endswith('.gov'):
                return 0.90
            elif domain.endswith('.edu'):
                return 0.85
            elif domain.endswith('.org'):
                return 0.70
            elif domain.endswith('.com'):
                return 0.60
            else:
                return 0.50
                
        except Exception:
            return 0.30  # Low score for malformed URLs
    
    def _analyze_source(self, source: str) -> float:
        """Analyze credibility based on source type."""
        if not source:
            return 0.5
        
        source_lower = source.lower()
        
        # Academic and research sources
        if any(term in source_lower for term in ['university', 'research', 'institute', 'journal']):
            return 0.90
        
        # Government sources
        if any(term in source_lower for term in ['government', 'official', 'agency']):
            return 0.85
        
        # News organizations
        if any(term in source_lower for term in ['news', 'times', 'post', 'herald', 'tribune']):
            return 0.75
        
        # Tech sources
        if any(term in source_lower for term in ['tech', 'developer', 'engineering']):
            return 0.70
        
        # Social media
        if any(term in source_lower for term in ['social', 'twitter', 'facebook', 'reddit']):
            return 0.45
        
        return 0.60  # Default score
    
    def _analyze_content_quality(self, title: str, content: str) -> float:
        """Analyze content quality indicators."""
        full_text = f"{title} {content}".lower()
        
        # Count positive and negative indicators
        positive_count = sum(1 for indicator in self.quality_indicators['positive'] 
                           if indicator in full_text)
        negative_count = sum(1 for indicator in self.quality_indicators['negative'] 
                           if indicator in full_text)
        
        # Check for specific quality markers
        quality_score = 0.5  # Base score
        
        # Positive indicators
        if positive_count > 0:
            quality_score += min(positive_count * 0.1, 0.3)
        
        # Negative indicators
        if negative_count > 0:
            quality_score -= min(negative_count * 0.15, 0.4)
        
        # Check for excessive capitalization (clickbait indicator)
        if title and sum(1 for c in title if c.isupper()) / len(title) > 0.3:
            quality_score -= 0.2
        
        # Check for excessive punctuation
        if title and title.count('!') > 2:
            quality_score -= 0.1
        
        return max(0.0, min(1.0, quality_score))
    
    def _analyze_recency(self, published_date: str) -> float:
        """Analyze content recency (newer content generally more credible for current events)."""
        if not published_date:
            return 0.5  # Neutral score for missing date
        
        try:
            # Try to parse the date (assuming ISO format or common formats)
            if isinstance(published_date, str):
                # Simple parsing - would need more robust date parsing in production
                pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            else:
                pub_date = published_date
            
            now = datetime.now()
            age_days = (now - pub_date).days
            
            # Scoring based on age
            if age_days <= 1:
                return 0.95  # Very recent
            elif age_days <= 7:
                return 0.85  # Recent
            elif age_days <= 30:
                return 0.75  # Moderately recent
            elif age_days <= 90:
                return 0.65  # Somewhat old
            elif age_days <= 365:
                return 0.55  # Old
            else:
                return 0.45  # Very old
                
        except Exception:
            return 0.5  # Neutral score for unparseable dates
    
    def _analyze_author(self, author: str) -> float:
        """Analyze author credibility indicators."""
        if not author:
            return 0.5
        
        author_lower = author.lower()
        
        # Check for credibility indicators in author info
        if any(term in author_lower for term in ['dr.', 'prof.', 'phd', 'md']):
            return 0.85
        
        if any(term in author_lower for term in ['researcher', 'scientist', 'expert']):
            return 0.80
        
        if any(term in author_lower for term in ['journalist', 'reporter', 'correspondent']):
            return 0.75
        
        return 0.60  # Default score for named authors
    
    def _identify_risk_factors(self, title: str, content: str, url: str) -> List[str]:
        """Identify potential credibility risk factors."""
        risk_factors = []
        full_text = f"{title} {content}".lower()
        
        # Clickbait indicators
        if title and any(phrase in title.lower() for phrase in [
            'you won\'t believe', 'shocking', 'doctors hate', 'one weird trick'
        ]):
            risk_factors.append('clickbait_title')
        
        # Misinformation indicators
        if any(term in full_text for term in ['conspiracy', 'cover-up', 'they don\'t want you to know']):
            risk_factors.append('conspiracy_language')
        
        # Lack of sources
        if content and len(content) > 500 and not any(term in full_text for term in [
            'source', 'study', 'research', 'according to'
        ]):
            risk_factors.append('no_sources_cited')
        
        # Suspicious domain
        if url and any(term in url.lower() for term in ['fake', 'hoax', 'conspiracy']):
            risk_factors.append('suspicious_domain')
        
        # Excessive emotional language
        emotional_words = ['outrageous', 'shocking', 'unbelievable', 'devastating', 'explosive']
        if sum(1 for word in emotional_words if word in full_text) > 3:
            risk_factors.append('excessive_emotional_language')
        
        return risk_factors
    
    def _generate_explanation(
        self, 
        final_score: float, 
        domain_score: float, 
        source_score: float, 
        content_score: float, 
        recency_score: float
    ) -> str:
        """Generate human-readable explanation of credibility assessment."""
        explanations = []
        
        if domain_score >= 0.8:
            explanations.append("trusted domain")
        elif domain_score <= 0.4:
            explanations.append("questionable domain")
        
        if source_score >= 0.8:
            explanations.append("reputable source")
        elif source_score <= 0.4:
            explanations.append("unverified source")
        
        if content_score >= 0.7:
            explanations.append("high-quality content")
        elif content_score <= 0.4:
            explanations.append("low-quality content indicators")
        
        if recency_score >= 0.8:
            explanations.append("recent publication")
        elif recency_score <= 0.4:
            explanations.append("outdated content")
        
        if not explanations:
            return f"Moderate credibility (score: {final_score:.2f})"
        
        return f"Credibility based on: {', '.join(explanations)}"
    
    async def analyze_batch(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze credibility for a batch of content items.
        
        Args:
            contents: List of content dictionaries
            
        Returns:
            List of credibility analysis results
        """
        tasks = [self.analyze(content) for content in contents]
        return await asyncio.gather(*tasks)
