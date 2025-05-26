"""
Weather scraper module for fetching weather data from multiple providers.
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict, Any

class WeatherScraper:
    """Weather scraper that aggregates data from multiple weather providers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the weather scraper."""
        self.config = config
        self._session = None
        self.apis = config.get('apis', {})
        self.rate_limit = config.get('scraping', {}).get('rate_limit', {})
        self.last_request_time = None

    async def _init_session(self):
        """Initialize aiohttp session if not already created."""
        if not hasattr(self, 'session') or self.session is None:
            if self._session is None:
                self._session = aiohttp.ClientSession()
            self.session = self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
        if hasattr(self, 'session'):
            self.session = None

    async def _rate_limit_wait(self):
        """Implement rate limiting."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < 0.5:  # Minimum 0.5 seconds between requests
                await asyncio.sleep(0.5 - elapsed)
        self.last_request_time = datetime.now()

    async def _fetch_openweathermap(self, location: str) -> Dict[str, Any]:
        """Fetch weather data from OpenWeatherMap."""
        try:
            await self._rate_limit_wait()
            url = f"{self.apis['openweathermap']['base_url']}/weather"
            params = {
                'q': location,
                'units': self.apis['openweathermap']['units']
            }
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'provider': 'openweathermap',
                        'location': location,
                        'current': data,
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception:
            pass
        return None

    async def _fetch_weatherapi(self, location: str) -> Dict[str, Any]:
        """Fetch weather data from WeatherAPI."""
        try:
            await self._rate_limit_wait()
            url = f"{self.apis['weatherapi']['base_url']}/current.json"
            params = {
                'q': location,
                'days': self.apis['weatherapi']['days']
            }
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'provider': 'weatherapi',
                        'location': location,
                        'current': data,
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception:
            pass
        return None

    async def scrape(self, location: str) -> List[Dict[str, Any]]:
        """
        Fetch weather data for a given location from multiple providers.
        
        Args:
            location: City name and country code (e.g., "London,UK")
            
        Returns:
            List of weather data from different providers
        """
        await self._init_session()
        results = []
        
        # Fetch from multiple providers
        tasks = [
            self._fetch_openweathermap(location),
            self._fetch_weatherapi(location)
        ]
        
        for result in await asyncio.gather(*tasks):
            if result:
                results.append(result)
                
        return results 