"""
Scraper package for collecting data from various sources.
"""

from .plugin_loader import BaseScraper, load_scrapers
from .news import NewsScraper

__all__ = ['BaseScraper', 'load_scrapers', 'NewsScraper']
