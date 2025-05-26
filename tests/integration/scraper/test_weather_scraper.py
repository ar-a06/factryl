"""
Integration tests for the weather scraper.
"""

import pytest
from app.scraper.weather import WeatherScraper

@pytest.mark.asyncio
class TestWeatherScraper:
    """Integration tests for the weather scraper."""
    
    @pytest.fixture
    async def weather_scraper(self, base_config):
        """Create a weather scraper instance."""
        scraper = WeatherScraper(base_config)
        yield scraper
        await scraper.close()
    
    async def test_scrape_with_valid_location(self, weather_scraper):
        """Test scraping with valid location."""
        locations = [
            "London,UK",
            "New York,US",
            "Tokyo,JP",
            "Sydney,AU"
        ]
        
        for location in locations:
            results = await weather_scraper.scrape(location)
            assert isinstance(results, list)
            
            for result in results:
                assert isinstance(result, dict)
                assert 'provider' in result
                assert 'location' in result
                assert 'current' in result
                assert 'timestamp' in result
                
                if result['provider'] == 'openweathermap':
                    assert isinstance(result['current'], dict)
                    if 'forecast' in result:
                        assert isinstance(result['forecast'], dict)
                    if 'air_quality' in result:
                        assert isinstance(result['air_quality'], dict)
                        
                elif result['provider'] == 'weatherapi':
                    assert isinstance(result['current'], dict)
                    if 'forecast' in result:
                        assert isinstance(result['forecast'], dict)
                        
                elif result['provider'] == 'noaa':
                    if result['current']:
                        assert isinstance(result['current'], dict)
                    if result['forecast']:
                        assert isinstance(result['forecast'], list)
    
    async def test_scrape_with_invalid_location(self, weather_scraper):
        """Test scraping with invalid location."""
        results = await weather_scraper.scrape("InvalidCity123,XX")
        assert isinstance(results, list)
        assert len(results) == 0  # Should return empty list for invalid location
    
    async def test_validate_configuration(self, weather_scraper):
        """Test configuration validation."""
        is_valid = await weather_scraper.validate()
        assert isinstance(is_valid, bool) 