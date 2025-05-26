"""
Scraper package for collecting data from various sources.

This package is organized into the following modules:

Core:
- base: Base scraper classes and utilities
- plugin_loader: Dynamic scraper loading functionality

Content Sources:
- news: News article scrapers
- blogs: Blog and article scrapers  
- media: YouTube, podcast, and media scrapers
- social: Social media scrapers (Twitter, Reddit, Quora)
- communities: Community and forum scrapers (Stack Overflow, Dev.to, Product Hunt, IndieHackers)
- research: Academic and research content scrapers
- shopping: E-commerce and product scrapers
- events: Event and conference scrapers
- government: Government data scrapers
- weather: Weather information scrapers

Usage:
    from app.scraper.news import NewsScraper
    from app.scraper.media.youtube import YouTubeScraper
    from app.scraper.social.twitter import TwitterScraper
    from app.scraper.communities import StackOverflowScraper
"""

from .plugin_loader import BaseScraper, load_scrapers
from .news import NewsScraper

__all__ = ['BaseScraper', 'load_scrapers', 'NewsScraper']
