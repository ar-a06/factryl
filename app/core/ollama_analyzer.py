"""
Ollama LLM Analyzer for Factryl
Provides real LLM integration for article summarization using Ollama + Llama 3.1
"""

import ollama
import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OllamaAnalyzer:
    """LLM analyzer using Ollama for intelligent article summarization."""
    
    def __init__(self, model_name: str = "llama3.1", base_url: str = None):
        """Initialize the Ollama analyzer with specified model."""
        self.model_name = model_name
        self.base_url = base_url
        self.client = None
        self.is_available = False
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize connection to Ollama service."""
        try:
            # Check if Ollama is running and model is available
            models = ollama.list()
            available_models = [model['name'] for model in models['models']]
            
            if self.model_name in available_models:
                self.is_available = True
                logger.info(f"Ollama connection established with model: {self.model_name}")
            else:
                logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                # Try to pull the model
                try:
                    logger.info(f"Attempting to pull model: {self.model_name}")
                    ollama.pull(self.model_name)
                    self.is_available = True
                    logger.info(f"Successfully pulled model: {self.model_name}")
                except Exception as e:
                    logger.error(f"Failed to pull model {self.model_name}: {e}")
                    self.is_available = False
        
        except Exception as e:
            logger.error(f"Failed to initialize Ollama connection: {e}")
            self.is_available = False
    
    def is_service_available(self) -> bool:
        """Check if Ollama service is available."""
        return self.is_available
    
    def generate_article_summary(self, article: Dict[str, Any], max_words: int = 50) -> str:
        """
        Generate a concise summary for a single article to display in article tiles.
        
        Args:
            article: Article data containing title, content, source, etc.
            max_words: Maximum words for the summary (default 50 for tiles)
        
        Returns:
            A concise, engaging summary highlighting key information
        """
        if not self.is_available:
            return self._fallback_summary(article, max_words)
        
        try:
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            source = article.get('source', 'Unknown').title()
            
            # Create focused prompt for article tile summaries
            prompt = f"""
Create a concise, engaging summary for this article that will appear in a news tile.

ARTICLE DETAILS:
Title: {title}
Source: {source}
Content: {content[:500]}

REQUIREMENTS:
- Maximum {max_words} words
- Focus on the most important/interesting aspect
- Make it engaging and informative
- Use present tense
- No speculation or opinion
- Start with action or key fact
- Suitable for quick scanning

EXAMPLE FORMATS:
- "Scientists discover new treatment for..."
- "Company announces major breakthrough in..."
- "Government implements new policy affecting..."
- "Research reveals surprising finding about..."

Generate the summary:
"""

            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.3,  # More focused, less creative
                    'top_p': 0.9,
                    'num_predict': max_words * 2  # Give some buffer for word count
                }
            )
            
            summary = response['message']['content'].strip()
            
            # Clean and validate summary
            summary = self._clean_summary(summary, max_words)
            
            if len(summary.split()) <= max_words and len(summary) > 20:
                logger.info(f"Generated LLM summary: {summary[:50]}...")
                return summary
            else:
                logger.warning(f"LLM summary failed validation, using fallback")
                return self._fallback_summary(article, max_words)
                
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._fallback_summary(article, max_words)
    
    def generate_intelligence_report(self, articles: List[Dict[str, Any]], query: str, max_words: int = 280) -> str:
        """
        Generate a comprehensive intelligence report from multiple articles.
        
        Args:
            articles: List of article data
            query: Search query/topic
            max_words: Maximum words for the report
        
        Returns:
            Comprehensive intelligence analysis
        """
        if not self.is_available:
            return self._fallback_intelligence_report(articles, query, max_words)
        
        try:
            # Prepare article data for analysis
            article_summaries = []
            sources = set()
            
            for i, article in enumerate(articles[:10], 1):
                title = article.get('title', '').strip()
                content = article.get('content', '').strip()
                source = article.get('source', 'Unknown')
                sources.add(source)
                
                article_summaries.append(f"""
Article {i} ({source}):
Title: {title}
Content: {content[:300]}...
""")
            
            # Create comprehensive intelligence analysis prompt
            prompt = f"""
You are an intelligence analyst creating a comprehensive report on: "{query}"

SOURCE MATERIALS:
{chr(10).join(article_summaries)}

ANALYSIS REQUIREMENTS:
Create a {max_words}-word intelligence briefing with:

1. EXECUTIVE SUMMARY (2-3 sentences on key findings)
2. CURRENT SITUATION (What's happening now)
3. KEY DEVELOPMENTS (Major recent events/trends)
4. SOURCE ASSESSMENT (Brief note on {len(sources)} sources)
5. IMPLICATIONS (What this means)
6. OUTLOOK (What to expect)

STYLE GUIDELINES:
- Professional intelligence briefing tone
- Use present tense for current events
- Be analytical, not speculative
- Focus on verifiable information
- No HTML tags or special formatting
- Exactly {max_words} words

Begin with "Intelligence Analysis: {query}."

Generate the intelligence report:
"""

            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.2,  # Very focused for intelligence reports
                    'top_p': 0.85,
                    'num_predict': max_words * 2
                }
            )
            
            report = response['message']['content'].strip()
            
            # Clean and validate report
            report = self._clean_summary(report, max_words)
            
            if len(report) > 100 and "Intelligence Analysis:" in report:
                logger.info(f"Generated intelligence report: {len(report)} chars")
                return report
            else:
                logger.warning("Intelligence report failed validation, using fallback")
                return self._fallback_intelligence_report(articles, query, max_words)
                
        except Exception as e:
            logger.error(f"Intelligence report generation failed: {e}")
            return self._fallback_intelligence_report(articles, query, max_words)
    
    def _clean_summary(self, summary: str, max_words: int) -> str:
        """Clean and format the generated summary."""
        # Remove any potential formatting artifacts
        summary = summary.replace('**', '').replace('*', '')
        summary = summary.replace('\n', ' ').replace('\r', ' ')
        
        # Remove extra whitespace
        summary = ' '.join(summary.split())
        
        # Ensure it doesn't exceed word limit
        words = summary.split()
        if len(words) > max_words:
            summary = ' '.join(words[:max_words]) + '...'
        
        # Ensure it ends properly
        if not summary.endswith(('.', '!', '?', '...')):
            summary += '.'
        
        return summary
    
    def _fallback_summary(self, article: Dict[str, Any], max_words: int) -> str:
        """Generate fallback summary when LLM is unavailable."""
        title = article.get('title', '').strip()
        content = article.get('content', '').strip()
        
        if not title:
            return "Article content available for review."
        
        # Use title as base, add content if very short title
        if len(title.split()) < 8 and content:
            # Extract first sentence from content
            sentences = content.split('.')
            first_sentence = sentences[0].strip() if sentences else ""
            
            if first_sentence and len(first_sentence.split()) < max_words:
                return f"{title.rstrip('.')}. {first_sentence}."
        
        # Just return cleaned title
        words = title.split()
        if len(words) > max_words:
            return ' '.join(words[:max_words]) + '...'
        
        return title
    
    def _fallback_intelligence_report(self, articles: List[Dict[str, Any]], query: str, max_words: int) -> str:
        """Generate fallback intelligence report when LLM is unavailable."""
        if not articles:
            return f"Limited intelligence available on {query} at this time."
        
        # Extract key information
        sources = set(article.get('source', 'unknown') for article in articles)
        main_title = articles[0].get('title', '') if articles else ''
        
        return f"Intelligence Analysis: {query}. Current reporting from {len(sources)} sources indicates ongoing developments. {main_title.rstrip('.')} represents recent activity in this area. Analysis of available sources suggests continued interest and activity surrounding {query}. Further monitoring recommended as situation develops."
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Ollama service."""
        try:
            if not self.is_available:
                return {
                    'status': 'unavailable',
                    'model': self.model_name,
                    'error': 'Service not initialized'
                }
            
            # Test with simple query
            start_time = time.time()
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user', 
                    'content': 'Test response. Reply with: OK'
                }],
                options={'temperature': 0.1}
            )
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'model': self.model_name,
                'response_time': round(response_time, 2),
                'test_response': response['message']['content'][:50]
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'model': self.model_name,
                'error': str(e)
            } 