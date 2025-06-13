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
    
    def generate_article_summary(self, article: Dict[str, Any], max_words: int = 300) -> str:
        """
        Generate a concise summary for a single article to display in article tiles.
        
        Args:
            article: Article data containing title, content, source, etc.
            max_words: Maximum words for the summary (default 300 for comprehensive summaries)
        
        Returns:
            A concise, engaging summary highlighting key information
        """
        if not self.is_available:
            return self._fallback_summary(article, max_words)
        
        try:
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            source = article.get('source', 'Unknown').title()
            url_context = article.get('url_context', '')
            
            # Debug logging to see what content we're working with
            logger.info(f"Article summary request - Title: {title[:100]}...")
            logger.info(f"Article summary request - Content length: {len(content)} chars")
            logger.info(f"Article summary request - Content preview: {content[:200]}...")
            logger.info(f"Article summary request - Source: {source}")
            
            # Create comprehensive article analysis prompt
            prompt = f"""
You are an expert news analyst creating a comprehensive summary that captures ALL the key points from an article. Your goal is to extract every important detail and present a complete picture of the story.

ARTICLE DATA:
Title: {title}
Source: {source}
Content: {content[:3000]}
{f"URL Context: {url_context}" if url_context else ""}

YOUR MISSION:
Create a comprehensive {max_words}-word summary that highlights ALL the key points, important details, and significant information from this article. Think of this as a complete briefing that covers everything a reader needs to know.

COMPREHENSIVE ANALYSIS FRAMEWORK:
1. MAIN EVENT/STORY: What is the primary news or development?
2. KEY PLAYERS: Who are the main people, organizations, or entities involved?
3. IMPORTANT DETAILS: What specific facts, numbers, dates, locations are mentioned?
4. BACKGROUND CONTEXT: What led to this situation or why is it happening now?
5. IMPACT & CONSEQUENCES: What are the effects, implications, or outcomes?
6. FUTURE DEVELOPMENTS: What happens next or what to expect?

QUALITY STANDARDS:
✓ Include ALL significant facts mentioned in the article
✓ Preserve specific numbers, dates, names, and locations
✓ Explain the "who, what, when, where, why, and how"
✓ Connect different aspects of the story together
✓ Highlight both immediate and long-term implications
✓ Use clear, informative language that flows well

CRITICAL INSTRUCTIONS:
🚫 REJECT GENERIC CONTENT: If you see phrases like "Products shown on this page are not available in all countries" or "Visit support.google.com" or "explore official site for merchandise," these are NOT real article content - they are generic website navigation text.

✅ WHEN CONTENT IS GENERIC: Use the title to infer what the real story is about and create a factual, journalistic summary based on what that type of news story would logically contain.

📰 EXTRACT REAL NEWS: Look for actual news facts in any content provided. Focus on:
- Specific events that happened
- People involved and their actions  
- Dates, locations, numbers, and details
- Consequences and implications
- What readers actually need to know

🎯 CREATE COMPREHENSIVE SUMMARIES: Include every important detail, connect different aspects of the story, and provide complete context.

⚠️ IMPORTANT: If the content appears to be just a headline or very short, DO NOT create a generic summary. Instead, analyze what the headline suggests and create a factual, journalistic summary that explains what this type of news story would typically contain based on the headline and source.

🔍 CONTENT ANALYSIS: 
- If content is short (< 100 chars), focus on the title and create a detailed explanation of what this news story is about
- If content is medium length (100-500 chars), extract all key facts and expand on them
- If content is long (> 500 chars), provide a comprehensive summary covering all major points

Write your comprehensive news summary covering all key points:
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
            
            if len(summary) > 10:  # Much more lenient validation - just check if we have content
                logger.info(f"Generated LLM summary: {summary[:50]}...")
                return summary
            else:
                logger.warning(f"LLM summary too short, using fallback")
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
            
            # Create enhanced news analysis prompt
            prompt = f"""
You are a senior journalist and news analyst creating a comprehensive overview of current developments regarding: "{query}"

AVAILABLE SOURCES:
{chr(10).join(article_summaries)}

YOUR MISSION:
Write a {max_words}-word comprehensive news analysis that synthesizes these sources into a clear, engaging overview that helps readers understand the full picture.

STRUCTURE YOUR ANALYSIS:
1. **LEAD** (25-30 words): Start with the most significant current development or trend
2. **CONTEXT** (40-50 words): Provide essential background and recent developments  
3. **KEY FINDINGS** (80-100 words): Synthesize the most important information from your sources
4. **MULTIPLE PERSPECTIVES** (40-50 words): Include different viewpoints or aspects covered
5. **SIGNIFICANCE** (30-40 words): Explain why this matters to readers
6. **CURRENT STATUS** (30-40 words): Where things stand now and immediate next steps

WRITING EXCELLENCE:
✓ Use compelling, journalistic language that engages readers
✓ Include specific facts, figures, names, and timelines from the sources
✓ Weave sources together naturally - don't just list them separately  
✓ Show connections and patterns across different reports
✓ Make complex topics accessible to general audiences
✓ Use active voice and varied sentence structure
✓ Be authoritative but not academic or dry

CREDIBILITY STANDARDS:
- Only include information supported by your sources
- Distinguish between confirmed facts and ongoing developments  
- Note when sources disagree or provide different perspectives
- Avoid speculation beyond what sources reasonably suggest
- Don't manufacture quotes or specific details not in sources

Begin your analysis with: "Current developments regarding {query}..."

Write your comprehensive {max_words}-word news analysis:
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
        """Generate intelligent fallback summary when LLM is unavailable."""
        title = article.get('title', '').strip()
        content = article.get('content', '').strip()
        source = article.get('source', 'Unknown').title()
        
        if not title:
            return "Article content available for review."
        
        # Create intelligent summary based on title analysis
        return self._create_intelligent_title_summary(title, source, max_words)
    
    def _create_intelligent_title_summary(self, title: str, source: str, max_words: int) -> str:
        """Create an intelligent summary based on the title and source."""
        title_lower = title.lower()
        
        # Analyze title for key entities and context
        if any(name in title_lower for name in ['taylor swift', 'swift']):
            # Remove all generic or promotional fallback summaries for Taylor Swift
            return f"{title} - {source}"
        elif any(name in title_lower for name in ['blake lively', 'lively']):
            return f"{title} - {source}"
        elif any(term in title_lower for term in ['bts', 'justin baldoni']):
            return f"{title} - {source}"
        # Generic but professional fallback
        else:
            words = title.split()
            key_entities = [word for word in words if len(word) > 3 and word[0].isupper()]
            if key_entities:
                main_entity = key_entities[0]
                return f"{title} - {source}"
            else:
                return f"{title} - {source}"
    
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