"""
Smart Source Manager for Factryl LLM Integration
Implements hybrid approach prioritizing rich content sources for LLM while maintaining comprehensive coverage
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SmartSourceManager:
    """Manages source prioritization for optimal LLM content vs comprehensive coverage."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Define source categories by content richness
        self.rich_content_sources = {
            'techcrunch': {
                'priority': 1,
                'content_quality': 'high',
                'typical_content_length': 500,
                'llm_suitable': True,
                'coverage_type': 'specialized',
                'description': 'In-depth technology reporting with full article content'
            },
            'bbc': {
                'priority': 1,
                'content_quality': 'high',
                'typical_content_length': 400,
                'llm_suitable': True,
                'coverage_type': 'broad',
                'description': 'Professional journalism with substantial content'
            },
            'wikipedia': {
                'priority': 2,
                'content_quality': 'high',
                'typical_content_length': 300,
                'llm_suitable': True,
                'coverage_type': 'reference',
                'description': 'Comprehensive reference material'
            }
        }
        
        self.headline_sources = {
            'google_news': {
                'priority': 3,
                'content_quality': 'enhanced',
                'typical_content_length': 200,
                'llm_suitable': True,  # Now suitable due to intelligent enhancement
                'coverage_type': 'comprehensive',
                'description': 'Broad news coverage with intelligent content enhancement'
            }
        }
        
        self.search_sources = {
            'duckduckgo': {
                'priority': 4,
                'content_quality': 'variable',
                'typical_content_length': 150,
                'llm_suitable': False,
                'coverage_type': 'broad',
                'description': 'Search results with variable content quality'
            },
            'bing': {
                'priority': 4,
                'content_quality': 'variable',
                'typical_content_length': 150,
                'llm_suitable': False,
                'coverage_type': 'broad',
                'description': 'Search results with variable content quality'
            }
        }
        
        # All sources combined
        self.all_sources = {
            **self.rich_content_sources,
            **self.headline_sources,
            **self.search_sources
        }
    
    def should_use_llm_summary(self, article: Dict[str, Any]) -> bool:
        """Determine if an article should use LLM summarization based on source and content quality."""
        
        source = article.get('source', '').lower()
        content_length = len(article.get('content', ''))
        
        # Get source information
        source_info = self.all_sources.get(source, {})
        
        # Priority 1: Rich content sources with substantial content
        if source in self.rich_content_sources:
            return content_length > 100  # Rich sources need minimal content threshold
        
        # Priority 2: Enhanced headline sources (like Google News with intelligent enhancement)
        if source in self.headline_sources:
            content_enhanced = article.get('metadata', {}).get('content_enhanced', False)
            return content_enhanced and content_length > 150  # Enhanced content should be longer
        
        # Priority 3: Other sources need substantial content
        return content_length > 300
    
    def get_content_quality_score(self, article: Dict[str, Any]) -> float:
        """Calculate content quality score for ranking purposes."""
        
        source = article.get('source', '').lower()
        content_length = len(article.get('content', ''))
        
        source_info = self.all_sources.get(source, {})
        base_score = 0.5  # Default score
        
        # Source quality multiplier
        if source in self.rich_content_sources:
            base_score = 0.9
        elif source in self.headline_sources:
            base_score = 0.7
        elif source in self.search_sources:
            base_score = 0.5
        
        # Content length bonus
        length_bonus = min(content_length / 500, 0.2)  # Up to 0.2 bonus for longer content
        
        # Enhancement bonus
        if article.get('metadata', {}).get('content_enhanced'):
            enhancement_bonus = 0.1
        else:
            enhancement_bonus = 0
        
        return min(base_score + length_bonus + enhancement_bonus, 1.0)
    
    def categorize_articles_for_processing(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize articles into different processing groups based on content quality."""
        
        categorized = {
            'llm_priority': [],      # Rich content sources - best for LLM
            'llm_suitable': [],      # Enhanced sources - good for LLM
            'display_only': [],      # Headlines/search results - display without LLM
            'unknown': []            # Uncategorized sources
        }
        
        for article in articles:
            source = article.get('source', '').lower()
            content_length = len(article.get('content', ''))
            
            if source in self.rich_content_sources and content_length > 100:
                categorized['llm_priority'].append(article)
            elif self.should_use_llm_summary(article):
                categorized['llm_suitable'].append(article)
            elif source in self.all_sources:
                categorized['display_only'].append(article)
            else:
                categorized['unknown'].append(article)
        
        return categorized
    
    def get_source_recommendations(self, query: str) -> Dict[str, Any]:
        """Get source recommendations based on query type."""
        
        query_lower = query.lower()
        recommendations = {
            'primary_sources': [],
            'secondary_sources': [],
            'coverage_strategy': '',
            'llm_strategy': ''
        }
        
        # Technology queries
        if any(term in query_lower for term in ['ai', 'technology', 'tech', 'startup', 'software']):
            recommendations['primary_sources'] = ['techcrunch', 'bbc']
            recommendations['secondary_sources'] = ['google_news', 'wikipedia']
            recommendations['coverage_strategy'] = 'technology_focused'
            recommendations['llm_strategy'] = 'prioritize_rich_content'
        
        # General news queries
        elif any(term in query_lower for term in ['news', 'politics', 'world', 'economic']):
            recommendations['primary_sources'] = ['bbc', 'google_news']
            recommendations['secondary_sources'] = ['duckduckgo', 'wikipedia']
            recommendations['coverage_strategy'] = 'broad_coverage'
            recommendations['llm_strategy'] = 'mixed_sources'
        
        # Reference/knowledge queries
        elif any(term in query_lower for term in ['what is', 'define', 'explain', 'how to']):
            recommendations['primary_sources'] = ['wikipedia', 'bbc']
            recommendations['secondary_sources'] = ['techcrunch', 'google_news']
            recommendations['coverage_strategy'] = 'knowledge_focused'
            recommendations['llm_strategy'] = 'comprehensive_analysis'
        
        # Default strategy
        else:
            recommendations['primary_sources'] = ['bbc', 'techcrunch', 'google_news']
            recommendations['secondary_sources'] = ['wikipedia', 'duckduckgo']
            recommendations['coverage_strategy'] = 'balanced'
            recommendations['llm_strategy'] = 'adaptive'
        
        return recommendations
    
    def optimize_article_mix(self, articles: List[Dict[str, Any]], target_count: int = 20) -> List[Dict[str, Any]]:
        """Optimize the mix of articles to balance content quality and coverage diversity."""
        
        categorized = self.categorize_articles_for_processing(articles)
        
        # Target distribution
        llm_priority_target = min(target_count // 3, len(categorized['llm_priority']))
        llm_suitable_target = min(target_count // 3, len(categorized['llm_suitable']))
        display_only_target = target_count - llm_priority_target - llm_suitable_target
        
        optimized = []
        
        # Add LLM priority articles first (highest quality)
        optimized.extend(categorized['llm_priority'][:llm_priority_target])
        
        # Add LLM suitable articles
        optimized.extend(categorized['llm_suitable'][:llm_suitable_target])
        
        # Fill remaining slots with display-only articles
        remaining_articles = categorized['display_only'] + categorized['unknown']
        optimized.extend(remaining_articles[:display_only_target])
        
        return optimized[:target_count]
    
    def get_source_statistics(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about source distribution and content quality."""
        
        stats = {
            'source_distribution': {},
            'content_quality_distribution': {},
            'llm_suitable_count': 0,
            'total_articles': len(articles),
            'average_content_length': 0,
            'rich_content_percentage': 0
        }
        
        if not articles:
            return stats
        
        total_content_length = 0
        llm_suitable_count = 0
        rich_content_count = 0
        
        for article in articles:
            source = article.get('source', 'unknown')
            content_length = len(article.get('content', ''))
            total_content_length += content_length
            
            # Source distribution
            stats['source_distribution'][source] = stats['source_distribution'].get(source, 0) + 1
            
            # LLM suitability
            if self.should_use_llm_summary(article):
                llm_suitable_count += 1
            
            # Rich content count
            if source in self.rich_content_sources:
                rich_content_count += 1
        
        stats['llm_suitable_count'] = llm_suitable_count
        stats['average_content_length'] = total_content_length / len(articles)
        stats['rich_content_percentage'] = (rich_content_count / len(articles)) * 100
        
        return stats
    
    def get_source_info(self, source_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific source."""
        return self.all_sources.get(source_name.lower(), {
            'priority': 5,
            'content_quality': 'unknown',
            'typical_content_length': 0,
            'llm_suitable': False,
            'coverage_type': 'unknown',
            'description': 'Unknown source'
        }) 