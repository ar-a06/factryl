"""ArXiv scraper for research papers."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import feedparser
import arxiv
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ArXivScraper(WebBasedScraper):
    """Scraper for arXiv research papers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Configure arXiv client
        self.client = arxiv.Client()
        
        # Default categories to search
        self.categories = self.config.get('categories', [
            'cs.AI',     # Artificial Intelligence
            'cs.LG',     # Machine Learning
            'cs.CL',     # Computation and Language
            'cs.CV',     # Computer Vision
            'cs.NE',     # Neural and Evolutionary Computing
            'cs.SE',     # Software Engineering
            'cs.DB',     # Databases
            'cs.DC'      # Distributed Computing
        ])
        
        self.max_results = self.config.get('max_results', 50)
        self.sort_by = self.config.get('sort_by', 'submittedDate')
        self.sort_order = self.config.get('sort_order', 'descending')
        
    def search_papers(self, query: str = None, categories: List[str] = None) -> List[Dict[str, Any]]:
        """Search arXiv papers by query and categories"""
        try:
            # Build search query
            search_query = []
            if query:
                search_query.append(query)
            
            # Add categories to query
            cat_list = categories or self.categories
            if cat_list:
                cat_query = ' OR '.join(f'cat:{cat}' for cat in cat_list)
                search_query.append(f'({cat_query})')
            
            # Create search object
            search = arxiv.Search(
                query=' AND '.join(search_query),
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                try:
                    # Calculate credibility score
                    credibility_score = self._calculate_credibility({
                        'title': result.title,
                        'authors': result.authors,
                        'categories': result.categories,
                        'journal_ref': result.journal_ref,
                        'comment': result.comment
                    })
                    
                    paper = {
                        'title': result.title,
                        'authors': [str(author) for author in result.authors],
                        'summary': result.summary,
                        'published': result.published.isoformat(),
                        'updated': result.updated.isoformat(),
                        'link': result.entry_id,
                        'pdf_url': result.pdf_url,
                        'categories': list(result.categories),
                        'source': 'arXiv',
                        'source_detail': f"arXiv - {', '.join(result.categories)}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Research Paper',
                            'bias': 'peer-reviewed-preprint'
                        },
                        'metadata': {
                            'doi': result.doi,
                            'journal_ref': result.journal_ref,
                            'primary_category': result.primary_category,
                            'comment': result.comment,
                            'authors': [str(author) for author in result.authors]
                        },
                        'scraped_at': time.time()
                    }
                    papers.append(paper)
                    
                except Exception as e:
                    logger.error(f"Error parsing arXiv paper: {e}")
                    continue
                    
            return papers
            
        except Exception as e:
            logger.error(f"Failed to search arXiv papers: {e}")
            return []
    
    def get_recent_papers(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent papers from specified categories"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            # Build date-based query
            date_query = f'submittedDate:[{since_date.strftime("%Y%m%d")}0000 TO 99991231235959]'
            cat_query = ' OR '.join(f'cat:{cat}' for cat in self.categories)
            
            search = arxiv.Search(
                query=f'{date_query} AND ({cat_query})',
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                try:
                    # Calculate credibility score
                    credibility_score = self._calculate_credibility({
                        'title': result.title,
                        'authors': result.authors,
                        'categories': result.categories,
                        'journal_ref': result.journal_ref,
                        'comment': result.comment
                    })
                    
                    paper = {
                        'title': result.title,
                        'authors': [str(author) for author in result.authors],
                        'summary': result.summary,
                        'published': result.published.isoformat(),
                        'updated': result.updated.isoformat(),
                        'link': result.entry_id,
                        'pdf_url': result.pdf_url,
                        'categories': list(result.categories),
                        'source': 'arXiv',
                        'source_detail': f"arXiv - {', '.join(result.categories)}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Research Paper',
                            'bias': 'peer-reviewed-preprint'
                        },
                        'metadata': {
                            'doi': result.doi,
                            'journal_ref': result.journal_ref,
                            'primary_category': result.primary_category,
                            'comment': result.comment,
                            'authors': [str(author) for author in result.authors]
                        },
                        'scraped_at': time.time()
                    }
                    papers.append(paper)
                    
                except Exception as e:
                    logger.error(f"Error parsing arXiv paper: {e}")
                    continue
                    
            return papers
            
        except Exception as e:
            logger.error(f"Failed to get recent arXiv papers: {e}")
            return []
    
    def _calculate_credibility(self, paper: Dict[str, Any]) -> float:
        """Calculate credibility score based on paper metrics"""
        try:
            # Base score 90-98 for arXiv papers
            base_score = 90.0
            
            # Factors that increase credibility:
            # 1. Multiple authors
            if paper.get('authors') and len(paper.get('authors', [])) > 1:
                base_score += 1
            
            # 2. Has journal reference (published in peer-reviewed journal)
            if paper.get('journal_ref'):
                base_score += 3
            
            # 3. Multiple categories (interdisciplinary research)
            if paper.get('categories') and len(paper.get('categories', [])) > 1:
                base_score += 1
            
            # 4. Has detailed comment/abstract
            if paper.get('comment') and len(paper.get('comment', '')) > 200:
                base_score += 1
            
            return min(base_score, 98.0)  # Cap at 98
            
        except:
            return 90.0  # Default score for arXiv papers 