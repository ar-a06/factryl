"""
Blogs module for scraping various blog platforms and publications.
Includes support for Medium, Substack, Ghost blogs, and other platforms.
"""

from .medium import MediumScraper
from .substack import SubstackScraper
from .ghost import GhostBlogScraper
from .blog import BlogScraper

__all__ = [
    'MediumScraper',
    'SubstackScraper',
    'GhostBlogScraper',
    'BlogScraper'
] 