"""
Research module for scraping academic papers and research content.
Includes support for Google Scholar, arXiv, IEEE Xplore, and research lab blogs.
"""

from .scholar import GoogleScholarScraper
from .arxiv import ArXivScraper
from .ieee import IEEEScraper
from .research_blogs import ResearchBlogScraper

__all__ = [
    'GoogleScholarScraper',
    'ArXivScraper',
    'IEEEScraper',
    'ResearchBlogScraper'
] 