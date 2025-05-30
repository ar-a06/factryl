"""Social media scrapers module."""

try:
    from .twitter import TwitterScraper
except ImportError:
    TwitterScraper = None

try:
    from .reddit import RedditScraper
except ImportError:
    RedditScraper = None

try:
    from .hackernews import HackerNewsScraper
except ImportError:
    HackerNewsScraper = None

try:
    from .instagram import InstagramScraper
except ImportError:
    InstagramScraper = None

try:
    from .tiktok import TikTokScraper
except ImportError:
    TikTokScraper = None

__all__ = []

if TwitterScraper:
    __all__.append('TwitterScraper')
if RedditScraper:
    __all__.append('RedditScraper')
if HackerNewsScraper:
    __all__.append('HackerNewsScraper')
if InstagramScraper:
    __all__.append('InstagramScraper')
if TikTokScraper:
    __all__.append('TikTokScraper') 