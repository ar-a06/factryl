"""
News module for scraping top news sites and tech publications.
Includes support for major tech news, business news, specialized tech publications,
sports news, education news, entertainment news, politics news, and economics news.
"""

from .tech_news import TechNewsScraper
from .business_news import BusinessNewsScraper
from .tech_publications import TechPublicationsScraper
from .sports_news import SportsNewsScraper
from .education_news import EducationNewsScraper
from .entertainment_news import EntertainmentNewsScraper
from .politics_news import PoliticsNewsScraper
from .economics_news import EconomicsNewsScraper
from .base import NewsScraper

__all__ = [
    'TechNewsScraper',
    'BusinessNewsScraper',
    'TechPublicationsScraper',
    'SportsNewsScraper',
    'EducationNewsScraper',
    'EntertainmentNewsScraper',
    'PoliticsNewsScraper',
    'EconomicsNewsScraper'
] 