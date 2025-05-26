"""Google Scholar scraper for academic papers and citations."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
from scholarly import scholarly
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GoogleScholarScraper(WebBasedScraper):
    """Scraper for Google Scholar content"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Configure scholarly
        scholarly.use_proxy()  # Use proxy to avoid rate limiting
        
        # Default search settings
        self.max_results = self.config.get('max_results', 30)
        self.min_citations = self.config.get('min_citations', 5)
        self.years_filter = self.config.get('years_filter', 5)  # Papers from last 5 years
        
        # Keywords for tech/programming focus
        self.default_keywords = self.config.get('keywords', [
            'machine learning',
            'artificial intelligence',
            'deep learning',
            'software engineering',
            'computer science',
            'data science',
            'neural networks',
            'natural language processing'
        ])
    
    def search_papers(self, query: str, year_start: int = None) -> List[Dict[str, Any]]:
        """Search for papers on Google Scholar"""
        try:
            if not year_start:
                year_start = datetime.now().year - self.years_filter
                
            papers = []
            search_query = scholarly.search_pubs(query)
            
            for i, result in enumerate(search_query):
                if i >= self.max_results:
                    break
                    
                try:
                    # Get detailed paper info
                    paper_info = scholarly.fill(result)
                    
                    # Skip if too old or too few citations
                    if paper_info.get('year', 0) < year_start:
                        continue
                    if paper_info.get('num_citations', 0) < self.min_citations:
                        continue
                    
                    # Calculate credibility score
                    credibility_score = self._calculate_credibility({
                        'title': paper_info.get('title', ''),
                        'authors': paper_info.get('author_pub_ids', []),
                        'year': paper_info.get('year', 0),
                        'citations': paper_info.get('num_citations', 0),
                        'journal': paper_info.get('journal', ''),
                        'abstract': paper_info.get('abstract', '')
                    })
                    
                    paper = {
                        'title': paper_info.get('title', ''),
                        'authors': paper_info.get('author_pub_ids', []),
                        'year': paper_info.get('year', ''),
                        'abstract': paper_info.get('abstract', ''),
                        'url': paper_info.get('pub_url', ''),
                        'citations': paper_info.get('num_citations', 0),
                        'source': 'Google Scholar',
                        'source_detail': f"Scholar - {paper_info.get('journal', 'Unknown Journal')}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Research Paper',
                            'bias': 'peer-reviewed-academic'
                        },
                        'metadata': {
                            'journal': paper_info.get('journal', ''),
                            'volume': paper_info.get('volume', ''),
                            'issue': paper_info.get('issue', ''),
                            'publisher': paper_info.get('publisher', ''),
                            'citations': paper_info.get('num_citations', 0)
                        },
                        'scraped_at': time.time()
                    }
                    papers.append(paper)
                    
                except Exception as e:
                    logger.error(f"Error parsing Scholar paper: {e}")
                    continue
                    
            return papers
            
        except Exception as e:
            logger.error(f"Failed to search Google Scholar: {e}")
            return []
    
    def search_author(self, author_name: str) -> List[Dict[str, Any]]:
        """Search for papers by a specific author"""
        try:
            # Search for author
            search_query = scholarly.search_author(author_name)
            author = next(search_query)
            
            # Get author's papers
            author = scholarly.fill(author)
            papers = []
            
            for i, pub in enumerate(author['publications']):
                if i >= self.max_results:
                    break
                    
                try:
                    # Get detailed paper info
                    paper_info = scholarly.fill(pub)
                    
                    # Skip if too old or too few citations
                    if paper_info.get('year', 0) < datetime.now().year - self.years_filter:
                        continue
                    if paper_info.get('num_citations', 0) < self.min_citations:
                        continue
                    
                    # Calculate credibility score
                    credibility_score = self._calculate_credibility({
                        'title': paper_info.get('title', ''),
                        'authors': paper_info.get('author_pub_ids', []),
                        'year': paper_info.get('year', 0),
                        'citations': paper_info.get('num_citations', 0),
                        'journal': paper_info.get('journal', ''),
                        'abstract': paper_info.get('abstract', '')
                    })
                    
                    paper = {
                        'title': paper_info.get('title', ''),
                        'authors': paper_info.get('author_pub_ids', []),
                        'year': paper_info.get('year', ''),
                        'abstract': paper_info.get('abstract', ''),
                        'url': paper_info.get('pub_url', ''),
                        'citations': paper_info.get('num_citations', 0),
                        'source': 'Google Scholar',
                        'source_detail': f"Scholar - {author['name']}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Research Paper',
                            'bias': 'peer-reviewed-academic'
                        },
                        'metadata': {
                            'journal': paper_info.get('journal', ''),
                            'volume': paper_info.get('volume', ''),
                            'issue': paper_info.get('issue', ''),
                            'publisher': paper_info.get('publisher', ''),
                            'citations': paper_info.get('num_citations', 0),
                            'author_metrics': {
                                'name': author['name'],
                                'affiliation': author.get('affiliation', ''),
                                'interests': author.get('interests', []),
                                'citedby': author.get('citedby', 0),
                                'h_index': author.get('hindex', 0)
                            }
                        },
                        'scraped_at': time.time()
                    }
                    papers.append(paper)
                    
                except Exception as e:
                    logger.error(f"Error parsing author's paper: {e}")
                    continue
                    
            return papers
            
        except Exception as e:
            logger.error(f"Failed to search author on Google Scholar: {e}")
            return []
    
    def _calculate_credibility(self, paper: Dict[str, Any]) -> float:
        """Calculate credibility score based on paper metrics"""
        try:
            # Base score 85-98 for Google Scholar papers
            base_score = 85.0
            
            # Factors that increase credibility:
            # 1. Citation count
            citations = paper.get('citations', 0)
            if citations > 1000:
                base_score += 5
            elif citations > 100:
                base_score += 3
            elif citations > 10:
                base_score += 1
            
            # 2. Recent paper
            current_year = datetime.now().year
            year = paper.get('year', 0)
            if year >= current_year - 2:  # Very recent (0-2 years)
                base_score += 2
            elif year >= current_year - 5:  # Recent (3-5 years)
                base_score += 1
            
            # 3. Published in known journal
            if paper.get('journal'):
                base_score += 2
            
            # 4. Multiple authors
            if paper.get('authors') and len(paper.get('authors', [])) > 2:
                base_score += 1
            
            # 5. Has detailed abstract
            if paper.get('abstract') and len(paper.get('abstract', '')) > 200:
                base_score += 1
            
            return min(base_score, 98.0)  # Cap at 98
            
        except:
            return 85.0  # Default score for Scholar papers 