"""
Plugin loader module for scraper implementations.
Provides base classes and utility decorators for scrapers.
"""

import os
import importlib
import inspect
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Type, List, Any
import time
from functools import wraps
from loguru import logger

def rate_limited(max_per_second: float):
    """
    Decorator to rate limit method calls.
    
    Args:
        max_per_second: Maximum number of calls allowed per second
    """
    min_interval = 1.0 / max_per_second
    
    def decorator(func):
        last_time_called = 0.0
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_time_called
            elapsed = time.time() - last_time_called
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
                
            last_time_called = time.time()
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator

class BaseScraper(ABC):
    """Base class for all scraper implementations."""
    
    def __init__(self, config: dict):
        """
        Initialize base scraper with configuration.
        
        Args:
            config: Dictionary containing scraper configuration
        """
        self.config = config
        
        # Get common scraping settings
        scraping_config = config.get('scraping', {})
        self.timeout = scraping_config.get('default_timeout', 30)
        self.max_retries = scraping_config.get('max_retries', 3)
        self.user_agents = scraping_config.get('user_agents', [])
        
        # Get cache settings
        cache_config = config.get('cache', {})
        self.cache_enabled = cache_config.get('enabled', True)
        self.cache_ttl = cache_config.get('ttl', 3600)
        
        # Get analysis settings
        analysis_config = config.get('analysis', {})
        self.min_relevance = analysis_config.get('relevance', {}).get('min_score', 0.6)
        self.min_credibility = analysis_config.get('credibility', {}).get('min_score', 0.5)
        
        # Initialize state
        self._initialized = False
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """
        Validate the scraper configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """
        Scrape content matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of dictionaries containing scraped data
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Clean up any resources used by the scraper."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    def _get_user_agent(self) -> str:
        """Get a random user agent from the configured list."""
        if not self.user_agents:
            return "Factryl/1.0"
        return self.user_agents[int(time.time()) % len(self.user_agents)]
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from successful function call
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = (2 ** attempt) + (time.time() % 1)  # Add jitter
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {str(e)}")
                    await asyncio.sleep(delay)
                    
        logger.error(f"All {self.max_retries} attempts failed")
        raise last_error

def load_scrapers(config: dict = None) -> Dict[str, BaseScraper]:
    """
    Dynamically load all scraper plugins from the scraper directory.
    
    Args:
        config: Configuration dictionary to pass to scrapers
        
    Returns:
        Dictionary mapping source names to scraper instances
    """
    scrapers = {}
    scraper_dir = os.path.dirname(__file__)
    
    # Get all Python files in the scraper directory
    for filename in os.listdir(scraper_dir):
        if not filename.endswith('.py') or filename == '__init__.py' or filename == os.path.basename(__file__):
            continue
            
        module_name = filename[:-3]  # Remove .py extension
        try:
            # Import the module
            module = importlib.import_module(f'.{module_name}', package='app.scraper')
            
            # Find scraper classes in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseScraper) and 
                    obj != BaseScraper):
                    try:
                        # Instantiate the scraper
                        scraper = obj(config)
                        source_name = scraper.get_source_name()
                        
                        # Validate the scraper
                        if asyncio.run(scraper.validate()):
                            scrapers[source_name] = scraper
                            logger.info(f"Loaded scraper for {source_name}")
                        else:
                            logger.warning(f"Scraper validation failed for {source_name}")
                    except Exception as e:
                        logger.error(f"Error instantiating scraper {name}: {e}")
                        
        except Exception as e:
            logger.error(f"Error loading scraper module {module_name}: {e}")
            
    if not scrapers:
        logger.warning("No valid scrapers found")
        
    return scrapers 