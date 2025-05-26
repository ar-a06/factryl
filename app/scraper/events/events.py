"""Events scraper for conferences, meetups, webinars, and other events."""

from ..base import WebBasedScraper
from typing import List, Dict, Any
import re
import time
import logging
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EventsScraper(WebBasedScraper):
    """Scraper for event platforms and conference sites"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Event platforms configuration
        self.platforms = self.config.get('platforms', [
            {
                'name': 'Meetup',
                'domain': 'meetup.com',
                'search_url': 'https://www.meetup.com/find/?keywords={query}',
                'type': 'meetups',
                'credibility_base': 80,
                'selectors': {
                    'event': '.event-card',
                    'title': '.event-title',
                    'date': '.event-date',
                    'location': '.event-location',
                    'attendees': '.attendee-count',
                    'link': 'a'
                }
            },
            {
                'name': 'Eventbrite',
                'domain': 'eventbrite.com',
                'search_url': 'https://www.eventbrite.com/d/online/{query}/',
                'type': 'conferences',
                'credibility_base': 85,
                'selectors': {
                    'event': '.search-event-card',
                    'title': '.event-title',
                    'date': '.event-date',
                    'price': '.event-price',
                    'organizer': '.event-organizer',
                    'link': 'a'
                }
            },
            {
                'name': 'TechCrunch Events',
                'domain': 'techcrunch.com',
                'base_url': 'https://techcrunch.com/events/',
                'type': 'tech_conferences',
                'credibility_base': 90,
                'selectors': {
                    'event': '.event-item',
                    'title': '.event-title',
                    'date': '.event-date',
                    'description': '.event-description',
                    'link': '.event-link'
                }
            },
            {
                'name': 'Conference Alerts',
                'domain': 'conferencealerts.com',
                'search_url': 'https://conferencealerts.com/topic.php?cat={query}',
                'type': 'academic_conferences',
                'credibility_base': 88,
                'selectors': {
                    'event': '.conf-box',
                    'title': '.conf-title',
                    'date': '.conf-date',
                    'location': '.conf-location',
                    'link': '.conf-link'
                }
            }
        ])
        
        self.max_events = self.config.get('max_events', 40)
        self.time_range_days = self.config.get('time_range_days', 365)  # Look ahead 1 year
        self.include_virtual = self.config.get('include_virtual', True)
        self.event_types = self.config.get('event_types', ['conference', 'meetup', 'workshop', 'webinar'])

    def get_source_name(self) -> str:
        """Get the name of this scraper's source."""
        return "events"

    async def validate(self) -> bool:
        """Validate the scraper configuration."""
        try:
            # Test basic connectivity
            test_url = "https://www.meetup.com"
            soup = await self.get_soup_async(test_url)
            return soup is not None
        except Exception as e:
            logger.error(f"Events scraper validation failed: {str(e)}")
            return False

    def _parse_event_date(self, date_text: str) -> Dict[str, str]:
        """Parse event date from various formats."""
        if not date_text:
            return {'date': '', 'formatted_date': ''}
            
        # Clean up the text
        date_text = re.sub(r'\s+', ' ', date_text.strip())
        
        # Common date patterns
        patterns = [
            r'(\w+ \d{1,2}, \d{4})',  # Month DD, YYYY
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\w+ \d{1,2}-\d{1,2}, \d{4})',  # Month DD-DD, YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_text)
            if match:
                return {
                    'date': match.group(1),
                    'formatted_date': date_text,
                    'raw_text': date_text
                }
        
        return {
            'date': date_text,
            'formatted_date': date_text,
            'raw_text': date_text
        }

    def _is_future_event(self, date_text: str) -> bool:
        """Check if event is in the future."""
        if not date_text:
            return True  # Assume unknown dates are future
            
        try:
            # Try to parse common date formats
            for fmt in ['%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d']:
                try:
                    event_date = datetime.strptime(date_text, fmt)
                    return event_date.date() >= datetime.now().date()
                except ValueError:
                    continue
            
            # If we can't parse the date, assume it's future
            return True
            
        except Exception:
            return True

    def _calculate_event_credibility(self, event_data: Dict[str, Any]) -> float:
        """Calculate credibility score for an event."""
        try:
            base_score = 60.0
            
            platform = event_data.get('platform', '').lower()
            
            # Platform credibility
            if 'techcrunch' in platform:
                base_score = 90.0
            elif 'eventbrite' in platform:
                base_score = 85.0
            elif 'meetup' in platform:
                base_score = 80.0
            elif 'conferencealerts' in platform:
                base_score = 88.0
            
            # Event type credibility
            event_type = event_data.get('type', '').lower()
            if 'conference' in event_type:
                base_score += 10
            elif 'workshop' in event_type:
                base_score += 8
            elif 'meetup' in event_type:
                base_score += 5
            
            # Attendee count factor
            attendees = event_data.get('attendees', 0)
            if isinstance(attendees, str):
                attendee_match = re.search(r'(\d+)', attendees)
                attendees = int(attendee_match.group(1)) if attendee_match else 0
            
            if attendees > 1000:
                base_score += 15
            elif attendees > 500:
                base_score += 10
            elif attendees > 100:
                base_score += 5
            
            # Recency factor (events happening soon are more relevant)
            date_text = event_data.get('date', '')
            if date_text:
                try:
                    # Events happening within 3 months get bonus
                    if any(month in date_text.lower() for month in ['january', 'february', 'march', 'april', 'may', 'june']):
                        base_score += 5
                except:
                    pass
            
            return min(100.0, max(0.0, base_score))
            
        except Exception:
            return 70.0

    async def _scrape_platform(self, platform_config: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Scrape individual event platform."""
        try:
            name = platform_config['name']
            domain = platform_config['domain']
            platform_type = platform_config['type']
            
            # Handle different URL patterns
            if 'search_url' in platform_config:
                search_url = platform_config['search_url'].format(query=query.replace(' ', '+'))
            elif 'base_url' in platform_config:
                search_url = platform_config['base_url']
            else:
                logger.warning(f"No URL configuration for platform {name}")
                return []
            
            soup = await self.get_soup_async(search_url)
            
            if not soup:
                return []
            
            events = []
            selectors = platform_config.get('selectors', {})
            
            # Find event containers
            event_selector = selectors.get('event', '.event')
            event_containers = soup.select(event_selector)
            
            for container in event_containers[:self.max_events]:
                try:
                    # Extract event information
                    title_elem = container.select_one(selectors.get('title', 'h2'))
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    if not title or query.lower() not in title.lower():
                        continue
                    
                    # Get link
                    link_elem = container.select_one(selectors.get('link', 'a'))
                    link = link_elem.get('href', '') if link_elem else ''
                    if link and not link.startswith('http'):
                        link = f"https://{domain}{link}"
                    
                    # Get date
                    date_elem = container.select_one(selectors.get('date', '.date'))
                    date_info = self._parse_event_date(date_elem.get_text(strip=True) if date_elem else '')
                    
                    # Skip past events
                    if not self._is_future_event(date_info['date']):
                        continue
                    
                    # Get location
                    location_elem = container.select_one(selectors.get('location', '.location'))
                    location = location_elem.get_text(strip=True) if location_elem else 'Online'
                    
                    # Get attendees/price/organizer
                    attendees_elem = container.select_one(selectors.get('attendees', '.attendees'))
                    attendees = attendees_elem.get_text(strip=True) if attendees_elem else ''
                    
                    price_elem = container.select_one(selectors.get('price', '.price'))
                    price = price_elem.get_text(strip=True) if price_elem else 'Free'
                    
                    organizer_elem = container.select_one(selectors.get('organizer', '.organizer'))
                    organizer = organizer_elem.get_text(strip=True) if organizer_elem else ''
                    
                    # Get description
                    desc_elem = container.select_one(selectors.get('description', '.description'))
                    description = desc_elem.get_text(strip=True)[:200] + "..." if desc_elem else ''
                    
                    # Calculate credibility
                    credibility_score = self._calculate_event_credibility({
                        'title': title,
                        'platform': name,
                        'type': platform_type,
                        'attendees': attendees,
                        'date': date_info['date'],
                        'organizer': organizer
                    })
                    
                    event = {
                        'title': title,
                        'link': link,
                        'description': description,
                        'date': date_info['formatted_date'],
                        'location': location,
                        'attendees': attendees,
                        'price': price,
                        'organizer': organizer,
                        'source': platform_type,
                        'source_name': name,
                        'type': 'Event',
                        'source_detail': f"Events - {name}",
                        'credibility_info': {
                            'score': credibility_score,
                            'category': 'Events',
                            'bias': 'community-driven'
                        },
                        'metadata': {
                            'platform': name,
                            'domain': domain,
                            'event_type': platform_type,
                            'date': date_info['date'],
                            'location': location,
                            'organizer': organizer,
                            'attendees': attendees,
                            'price': price,
                            'is_virtual': 'online' in location.lower() or 'virtual' in location.lower()
                        },
                        'scraped_at': time.time()
                    }
                    events.append(event)
                    
                except Exception as e:
                    logger.error(f"Error parsing event from {name}: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to scrape event platform {platform_config['name']}: {e}")
            return []

    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        """Scrape event platforms for events matching the query."""
        logger.info(f"Scraping events for: {query}")
        
        all_events = []
        
        for platform_config in self.platforms:
            events = await self._scrape_platform(platform_config, query)
            all_events.extend(events)
        
        # Sort by date (upcoming first) and credibility
        sorted_events = sorted(
            all_events,
            key=lambda x: (x['credibility_info']['score'], x.get('date', '')),
            reverse=True
        )
        
        return sorted_events[:self.max_events] 