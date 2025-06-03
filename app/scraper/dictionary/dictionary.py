"""
Dictionary Scraper for Factryl Engine
Fetches word definitions and meanings from multiple dictionary sources.
"""

import asyncio
import aiohttp
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

class DictionaryScraper:
    """Scraper for dictionary definitions and word meanings."""
    
    def __init__(self):
        """Initialize the dictionary scraper."""
        self.name = "dictionary"
        self.base_urls = {
            'free_dictionary': 'https://api.dictionaryapi.dev/api/v2/entries/en/',
            'wordnik': 'https://api.wordnik.com/v4/word.json/',
            'merriam_webster': 'https://www.merriam-webster.com/dictionary/'
        }
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for dictionary definitions.
        
        Args:
            query: Word or phrase to look up
            max_results: Maximum number of definitions to return
            
        Returns:
            List of dictionary entries with definitions
        """
        logger.info(f"Dictionary lookup for: {query}")
        
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        
        results = []
        
        # Check if this is a person's name first
        if self._is_person_name(query):
            logger.info(f"Detected person name: '{query}'")
            person_results = self._get_person_info(query)
            if person_results:
                results.extend(person_results)
                logger.info(f"Found biographical information for: '{query}'")
                return results[:max_results]
        
        # STEP 1: Try the FULL query first (no cleaning/splitting)
        logger.info(f"Trying full query first: '{query}'")
        full_query_results = await asyncio.gather(
            self._search_free_dictionary(query),
            self._search_free_dictionary_alternative(query),
            self._search_wiktionary(query),
            return_exceptions=True
        )
        
        # Combine results from full query attempts
        for result in full_query_results:
            if isinstance(result, list) and result:  # Only add non-empty results
                results.extend(result)
        
        # If we found good results with the full query, return them
        if results:
            logger.info(f"Found {len(results)} definitions using full query")
            sorted_results = self._sort_and_limit_results(results, max_results)
            return sorted_results
        
        # STEP 2: Try proper nouns database for common entities
        logger.info(f"Full query failed, checking proper nouns database for: '{query}'")
        proper_noun_results = self._get_proper_noun_definitions(query)
        if proper_noun_results:
            logger.info(f"Found proper noun definition for: '{query}'")
            return proper_noun_results[:max_results]
        
        # STEP 3: Check if this is likely a proper noun that shouldn't be broken down
        if self._is_likely_proper_noun(query):
            logger.info(f"'{query}' appears to be a proper noun with no definition available - skipping fallback")
            return []  # Don't fall back to individual words for proper nouns
        
        # STEP 4: Only try with cleaned/split query as fallback for regular words
        clean_query = self._clean_query(query)
        if clean_query != query and len(query.split()) == 1:  # Only for single words that were cleaned
            logger.info(f"Full query and proper nouns failed, trying cleaned query: '{clean_query}'")
            
            cleaned_results = await asyncio.gather(
                self._search_free_dictionary(clean_query),
                self._search_free_dictionary_alternative(clean_query),
                self._search_wiktionary(clean_query),
                return_exceptions=True
            )
            
            # Combine results from cleaned query
            for result in cleaned_results:
                if isinstance(result, list):
                    results.extend(result)
        
        # STEP 5: Try partial word matching as last resort (only for single words)
        if not results and len(query.split()) == 1:
            logger.info(f"All previous attempts failed, trying partial matches for: '{query}'")
            partial_results = await self._search_partial_matches(query)
            results.extend(partial_results)
        
        # Sort by relevance and limit results
        sorted_results = self._sort_and_limit_results(results, max_results)
        
        logger.info(f"Dictionary search returned {len(sorted_results)} definitions")
        return sorted_results
    
    def _clean_query(self, query: str) -> str:
        """Clean query for dictionary lookup as fallback."""
        # Remove common articles and prepositions
        words_to_remove = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        
        # Split into words
        words = query.lower().split()
        
        # For single words, return as-is
        if len(words) == 1:
            return words[0]
        
        # For multi-word queries, try to extract the main noun/concept
        # Remove articles and common words
        filtered_words = [word for word in words if word not in words_to_remove]
        
        if filtered_words:
            # Return the first significant word for dictionary lookup
            return filtered_words[0]
        else:
            # Fallback to first word
            return words[0] if words else query
    
    async def _search_free_dictionary(self, query: str) -> List[Dict[str, Any]]:
        """Search the Free Dictionary API."""
        try:
            url = f"{self.base_urls['free_dictionary']}{quote(query)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_free_dictionary_response(data, query)
                else:
                    logger.warning(f"Free Dictionary API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Free Dictionary API error: {e}")
            return []
    
    def _parse_free_dictionary_response(self, data: List[Dict], query: str) -> List[Dict[str, Any]]:
        """Parse response from Free Dictionary API."""
        results = []
        
        for entry in data[:3]:  # Allow up to 3 entries (for different word forms)
            word = entry.get('word', query)
            phonetic = entry.get('phonetic', '')
            
            # Extract phonetics from multiple sources if main one is missing
            if not phonetic:
                phonetics = entry.get('phonetics', [])
                for p in phonetics:
                    if p.get('text'):
                        phonetic = p.get('text')
                        break
            
            meanings = entry.get('meanings', [])
            for meaning_index, meaning in enumerate(meanings):  # Get ALL meanings (noun, verb, etc.)
                part_of_speech = meaning.get('partOfSpeech', '')
                definitions = meaning.get('definitions', [])
                
                for def_index, definition in enumerate(definitions):  # Get ALL definitions per meaning
                    def_text = definition.get('definition', '')
                    example = definition.get('example', '')
                    
                    if def_text:
                        # Create a comprehensive title showing the different meanings
                        title = f"{word}"
                        if part_of_speech:
                            title += f" ({part_of_speech})"
                        if len(definitions) > 1:
                            title += f" - Definition {def_index + 1}"
                        
                        results.append({
                            'title': title,
                            'content': self._format_definition_content(def_text, example, phonetic),
                            'url': f"https://dictionaryapi.dev/define/{query}",
                            'source': 'dictionary',
                            'type': 'definition',
                            'word': word,
                            'part_of_speech': part_of_speech,
                            'definition': def_text,
                            'example': example,
                            'phonetic': phonetic,
                            'meaning_index': meaning_index,
                            'definition_index': def_index,
                            'relevance_score': 1.0 - (meaning_index * 0.1) - (def_index * 0.05),  # Prioritize first meanings and definitions
                            'timestamp': None
                        })
        
        return results
    
    async def _search_free_dictionary_alternative(self, query: str) -> List[Dict[str, Any]]:
        """Search Free Dictionary API with retry and better error handling."""
        try:
            # Try with different query formats
            queries_to_try = [query, query.lower(), query.capitalize()]
            
            for attempt_query in queries_to_try:
                url = f"{self.base_urls['free_dictionary']}{quote(attempt_query)}"
                
                try:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = self._parse_free_dictionary_response(data, query)
                            if results:
                                return results
                except Exception as e:
                    logger.debug(f"Attempt failed for '{attempt_query}': {e}")
                    continue
            
            return []
        except Exception as e:
            logger.error(f"Free Dictionary alternative search error: {e}")
            return []
    
    async def _search_wiktionary(self, query: str) -> List[Dict[str, Any]]:
        """Search Wiktionary for word definitions."""
        try:
            # Use Wiktionary API
            wiktionary_url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{quote(query)}"
            
            async with self.session.get(wiktionary_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_wiktionary_response(data, query)
                else:
                    logger.debug(f"Wiktionary API returned status {response.status} for '{query}'")
                    return []
        except Exception as e:
            logger.error(f"Wiktionary search error: {e}")
            return []
    
    def _format_definition_content(self, definition: str, example: str = "", phonetic: str = "") -> str:
        """Format definition content for display."""
        content = f"Definition: {definition}"
        
        if phonetic:
            content = f"Pronunciation: {phonetic}\n{content}"
        
        if example:
            content += f"\n\nExample: {example}"
        
        return content
    
    def _sort_and_limit_results(self, results: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        """Sort results by relevance and limit to max_results."""
        # Sort by relevance score (highest first)
        sorted_results = sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Remove duplicates based on definition
        seen_definitions = set()
        unique_results = []
        
        for result in sorted_results:
            definition = result.get('definition', '').lower()
            if definition not in seen_definitions:
                seen_definitions.add(definition)
                unique_results.append(result)
                
                if len(unique_results) >= max_results:
                    break
        
        return unique_results
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
    
    def __del__(self):
        """Destructor to ensure session is closed."""
        if hasattr(self, 'session') and self.session:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
                else:
                    loop.run_until_complete(self.session.close())
            except:
                pass  # Ignore errors during cleanup
    
    async def _search_partial_matches(self, query: str) -> List[Dict[str, Any]]:
        """Search for partial word matches using word root extraction."""
        results = []
        
        # Extract word roots and try simpler forms
        word_variants = self._generate_word_variants(query)
        
        for variant in word_variants:
            try:
                variant_results = await self._search_free_dictionary(variant)
                if variant_results:
                    # Adjust relevance score for partial matches
                    for result in variant_results:
                        result['relevance_score'] = result.get('relevance_score', 1.0) * 0.7
                        result['title'] = f"{query.title()} (related: {variant})"
                    results.extend(variant_results)
                    break  # Stop at first successful variant
            except Exception as e:
                logger.debug(f"Variant search failed for '{variant}': {e}")
                continue
        
        return results
    
    def _generate_word_variants(self, query: str) -> List[str]:
        """Generate word variants for partial matching."""
        variants = []
        query_clean = query.lower().strip()
        
        # For multi-word queries, try individual words
        words = query_clean.split()
        if len(words) > 1:
            variants.extend(words)
        
        # Try removing common suffixes
        suffixes = ['s', 'es', 'ed', 'ing', 'ly', 'er', 'est', 'tion', 'sion']
        for suffix in suffixes:
            if query_clean.endswith(suffix) and len(query_clean) > len(suffix) + 2:
                variants.append(query_clean[:-len(suffix)])
        
        # Try adding common prefixes/suffixes for root words
        if len(query_clean) > 3:
            variants.extend([
                query_clean + 's',
                query_clean + 'ing',
                query_clean + 'ed'
            ])
        
        return list(set(variants))  # Remove duplicates
    
    def _parse_wiktionary_response(self, data: Dict, query: str) -> List[Dict[str, Any]]:
        """Parse response from Wiktionary API."""
        results = []
        
        try:
            # Wiktionary API structure
            definitions = data.get('en', [])
            
            for i, lang_section in enumerate(definitions[:2]):  # Limit to first 2 language sections
                part_of_speech = lang_section.get('partOfSpeech', 'unknown')
                definitions_list = lang_section.get('definitions', [])
                
                for j, definition in enumerate(definitions_list[:3]):  # Limit to 3 definitions per section
                    def_text = definition.get('definition', '')
                    examples = definition.get('examples', [])
                    example = examples[0] if examples else ''
                    
                    if def_text:
                        # Clean up definition text (remove wiki markup)
                        clean_def = self._clean_wiktionary_text(def_text)
                        
                        results.append({
                            'title': f"{query.title()} ({part_of_speech})",
                            'content': self._format_definition_content(clean_def, example),
                            'url': f"https://en.wiktionary.org/wiki/{query}",
                            'source': 'dictionary',
                            'type': 'definition',
                            'word': query,
                            'part_of_speech': part_of_speech,
                            'definition': clean_def,
                            'example': example,
                            'phonetic': '',  # Wiktionary doesn't always provide phonetics in this API
                            'relevance_score': 0.9 - (i * 0.1) - (j * 0.05),
                            'timestamp': None
                        })
        except Exception as e:
            logger.error(f"Error parsing Wiktionary response: {e}")
        
        return results
    
    def _clean_wiktionary_text(self, text: str) -> str:
        """Clean Wiktionary text from markup."""
        import re
        
        # Remove wiki links [[word]] -> word
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        
        # Remove wiki links with display text [[word|display]] -> display
        text = re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]', r'\2', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _get_proper_noun_definitions(self, query: str) -> List[Dict[str, Any]]:
        """Get definitions for common proper nouns that may not be in regular dictionaries."""
        query_lower = query.lower().strip()
        
        # Common countries
        countries = {
            'australia': {
                'definition': 'A country and continent in the southern hemisphere, known for its unique wildlife and diverse landscapes.',
                'phonetic': '/ɒˈstreɪljə/',
                'type': 'Country'
            },
            'america': {
                'definition': 'Commonly refers to the United States of America, a federal republic in North America.',
                'phonetic': '/əˈmɛrɪkə/',
                'type': 'Country'
            },
            'canada': {
                'definition': 'A country in North America, known for its vast wilderness and multicultural society.',
                'phonetic': '/ˈkænədə/',
                'type': 'Country'
            },
            'india': {
                'definition': 'A country in South Asia, known for its diverse culture, languages, and ancient history.',
                'phonetic': '/ˈɪndiə/',
                'type': 'Country'
            },
            'china': {
                'definition': 'A country in East Asia, the most populous country in the world with a rich cultural heritage.',
                'phonetic': '/ˈtʃaɪnə/',
                'type': 'Country'
            },
            'japan': {
                'definition': 'An island country in East Asia, known for its technology, culture, and history.',
                'phonetic': '/dʒəˈpæn/',
                'type': 'Country'
            },
            'south korea': {
                'definition': 'A country in East Asia, officially known as the Republic of Korea, known for its technology, culture, and K-pop.',
                'phonetic': '/saʊθ kəˈriə/',
                'type': 'Country'
            },
            'north korea': {
                'definition': 'A country in East Asia, officially known as the Democratic People\'s Republic of Korea.',
                'phonetic': '/nɔːrθ kəˈriə/',
                'type': 'Country'
            },
            'united states': {
                'definition': 'A federal republic in North America, commonly known as the USA or America.',
                'phonetic': '/juˌnaɪtɪd ˈsteɪts/',
                'type': 'Country'
            },
            'united kingdom': {
                'definition': 'A sovereign country in Europe, comprising England, Scotland, Wales, and Northern Ireland.',
                'phonetic': '/juˌnaɪtɪd ˈkɪŋdəm/',
                'type': 'Country'
            },
            'europe': {
                'definition': 'A continent in the Northern Hemisphere, comprising many countries with diverse cultures and languages.',
                'phonetic': '/ˈjʊərəp/',
                'type': 'Continent'
            },
            'africa': {
                'definition': 'A continent known for its diverse wildlife, cultures, and as the birthplace of humanity.',
                'phonetic': '/ˈæfrɪkə/',
                'type': 'Continent'
            }
        }
        
        # Common cities
        cities = {
            'london': {
                'definition': 'The capital city of England and the United Kingdom, known for its history and culture.',
                'phonetic': '/ˈlʌndən/',
                'type': 'City'
            },
            'paris': {
                'definition': 'The capital city of France, known for its art, fashion, and the Eiffel Tower.',
                'phonetic': '/ˈpærɪs/',
                'type': 'City'
            },
            'tokyo': {
                'definition': 'The capital city of Japan, known for its technology, culture, and bustling urban life.',
                'phonetic': '/ˈtoʊkjoʊ/',
                'type': 'City'
            },
            'sydney': {
                'definition': 'The largest city in Australia, known for its harbor, Opera House, and bridge.',
                'phonetic': '/ˈsɪdni/',
                'type': 'City'
            },
            'new york': {
                'definition': 'The most populous city in the United States, known for its skyline, Broadway, and as a global financial center.',
                'phonetic': '/nuː jɔːrk/',
                'type': 'City'
            },
            'los angeles': {
                'definition': 'The largest city in California, known for Hollywood, entertainment industry, and diverse culture.',
                'phonetic': '/lɔːs ˈændʒələs/',
                'type': 'City'
            },
            'chicago': {
                'definition': 'The third-largest city in the United States, known for its architecture, deep-dish pizza, and lakefront.',
                'phonetic': '/ʃɪˈkɑːɡoʊ/',
                'type': 'City'
            },
            'san francisco': {
                'definition': 'A major city in California, known for the Golden Gate Bridge, tech industry, and steep hills.',
                'phonetic': '/sæn frənˈsɪskoʊ/',
                'type': 'City'
            }
        }
        
        # Common entities/brands
        entities = {
            'google': {
                'definition': 'A multinational technology company known for its search engine and various digital services.',
                'phonetic': '/ˈɡuːɡəl/',
                'type': 'Company'
            },
            'apple': {
                'definition': 'A multinational technology company known for consumer electronics like iPhone and Mac.',
                'phonetic': '/ˈæpəl/',
                'type': 'Company'
            },
            'microsoft': {
                'definition': 'A multinational technology company known for Windows, Office, and cloud services.',
                'phonetic': '/ˈmaɪkrəsɔːft/',
                'type': 'Company'
            }
        }
        
        # Check all categories
        all_entities = {**countries, **cities, **entities}
        
        if query_lower in all_entities:
            entity = all_entities[query_lower]
            return [{
                'title': f"{query.title()} ({entity['type']})",
                'content': self._format_definition_content(entity['definition'], "", entity['phonetic']),
                'url': f"https://en.wikipedia.org/wiki/{query}",
                'source': 'dictionary',
                'type': 'definition',
                'word': query,
                'part_of_speech': 'proper noun',
                'definition': entity['definition'],
                'example': '',
                'phonetic': entity['phonetic'],
                'relevance_score': 0.8,  # Slightly lower than API results
                'timestamp': None
            }]
        
        return []
    
    def _is_person_name(self, query: str) -> bool:
        """Check if the query appears to be a person's name."""
        query_words = query.strip().split()
        
        # Heuristics for person detection
        if len(query_words) >= 2:
            # Multiple words with proper capitalization
            if all(word[0].isupper() for word in query_words if word):
                return True
        
        # Known person patterns (including K-pop artists)
        person_indicators = [
            'kim seok jin', 'jin bts', 'park jimin', 'jimin bts', 'min yoon gi', 'suga bts', 'agust d',
            'jung ho seok', 'j-hope bts', 'kim nam joon', 'rm bts', 'kim tae hyung', 'v bts', 'jeon jung kook', 'jungkook bts',
            'taylor swift', 'elon musk', 'bill gates', 'steve jobs', 'donald trump', 'joe biden', 'barack obama', 
            'leonardo dicaprio', 'tom cruise', 'jennifer lawrence', 'brad pitt', 'angelina jolie',
            'cristiano ronaldo', 'lionel messi', 'lebron james', 'michael jordan', 'serena williams', 'roger federer',
            'ariana grande', 'justin bieber', 'selena gomez', 'dua lipa', 'billie eilish', 'ed sheeran',
            'robert downey jr', 'scarlett johansson', 'chris evans', 'chris hemsworth', 'mark zuckerberg',
            'jeff bezos', 'warren buffett', 'oprah winfrey', 'ellen degeneres', 'jimmy fallon'
        ]
        
        query_lower = query.lower().strip()
        if query_lower in person_indicators:
            return True
        
        # Check for common Korean name patterns
        korean_name_patterns = [
            'park ', 'kim ', 'lee ', 'choi ', 'jung ', 'shin ', 'han ', 'oh ', 'seo ', 'kang ', 'yoon ', 'jang ', 'lim ', 'min '
        ]
        if any(query_lower.startswith(pattern) for pattern in korean_name_patterns) and len(query_words) >= 2:
            return True
            
        return False
    
    def _get_person_info(self, query: str) -> List[Dict[str, Any]]:
        """Get biographical information for known people."""
        query_lower = query.lower().strip()
        
        # Known people database
        people_info = {
            'park jimin': {
                'name': 'Park Jimin',
                'description': 'South Korean singer, songwriter, and dancer, member of the world-renowned boy band BTS. Known for his exceptional vocals, contemporary dance skills, and charismatic stage presence.',
                'profession': 'Singer, Songwriter, Dancer',
                'nationality': 'South Korean',
                'birth_year': '1995',
                'notable_for': 'BTS member, solo artist, contemporary dance, vocal range'
            },
            'jimin bts': {
                'name': 'Park Jimin (BTS)',
                'description': 'South Korean singer, songwriter, and dancer, member of the world-renowned boy band BTS. Known for his exceptional vocals, contemporary dance skills, and charismatic stage presence.',
                'profession': 'Singer, Songwriter, Dancer',
                'nationality': 'South Korean',
                'birth_year': '1995',
                'notable_for': 'BTS member, solo artist, contemporary dance, vocal range'
            },
            'kim seok jin': {
                'name': 'Kim Seok-jin (Jin)',
                'description': 'South Korean singer, songwriter, and member of the boy band BTS. Known for his vocals and visual appeal, often called the "visual" of the group.',
                'profession': 'Singer, Songwriter',
                'nationality': 'South Korean',
                'birth_year': '1992',
                'notable_for': 'Member of BTS, solo music career'
            },
            'jin bts': {
                'name': 'Kim Seok-jin (Jin)',
                'description': 'South Korean singer, songwriter, and member of the boy band BTS. Known for his vocals and visual appeal, often called the "visual" of the group.',
                'profession': 'Singer, Songwriter',
                'nationality': 'South Korean',
                'birth_year': '1992',
                'notable_for': 'Member of BTS, solo music career'
            },
            'taylor swift': {
                'name': 'Taylor Swift',
                'description': 'American singer-songwriter known for narrative songwriting and multiple genre transitions from country to pop to folk.',
                'profession': 'Singer-songwriter',
                'nationality': 'American',
                'birth_year': '1989',
                'notable_for': 'Multiple Grammy winner, global pop icon'
            },
            'elon musk': {
                'name': 'Elon Musk',
                'description': 'Business magnate and entrepreneur known for founding and leading companies like Tesla, SpaceX, and formerly Twitter.',
                'profession': 'Entrepreneur, Business Magnate',
                'nationality': 'South African-American',
                'birth_year': '1971',
                'notable_for': 'CEO of Tesla and SpaceX, space exploration pioneer'
            },
            'leonardo dicaprio': {
                'name': 'Leonardo DiCaprio',
                'description': 'American actor and environmental activist known for his roles in films like Titanic, Inception, and The Revenant.',
                'profession': 'Actor, Environmental Activist',
                'nationality': 'American',
                'birth_year': '1974',
                'notable_for': 'Academy Award winner, environmental advocacy'
            },
            'bill gates': {
                'name': 'Bill Gates',
                'description': 'American business magnate, software developer, and philanthropist. Co-founder of Microsoft Corporation.',
                'profession': 'Business Magnate, Philanthropist',
                'nationality': 'American',
                'birth_year': '1955',
                'notable_for': 'Microsoft co-founder, global health initiatives'
            },
            'matthew perry': {
                'name': 'Matthew Perry',
                'description': 'American actor and comedian best known for his role as Chandler Bing on the television sitcom Friends.',
                'profession': 'Actor, Comedian',
                'nationality': 'American',
                'birth_year': '1969',
                'notable_for': 'Friends TV series, comedy acting'
            },
            'steve jobs': {
                'name': 'Steve Jobs', 
                'description': 'American business magnate and inventor, co-founder and former CEO of Apple Inc. Revolutionary figure in personal computing.',
                'profession': 'Entrepreneur, Inventor',
                'nationality': 'American',
                'birth_year': '1955',
                'notable_for': 'Apple co-founder, iPhone and iPad creator'
            }
        }
        
        if query_lower in people_info:
            person = people_info[query_lower]
            formatted_bio = f"""**{person['name']}**
Born: {person['birth_year']} | {person['nationality']}
Profession: {person['profession']}

{person['description']}

Notable for: {person['notable_for']}"""
            
            return [{
                'title': f"{person['name']} (Person)",
                'content': formatted_bio,
                'url': f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                'source': 'dictionary',
                'type': 'biography',
                'word': query,
                'part_of_speech': 'person',
                'definition': formatted_bio,
                'example': '',
                'phonetic': '',
                'relevance_score': 0.95,  # High relevance for person info
                'timestamp': None
            }]
        
        # Generic person template for unknown people
        name_parts = query.strip().split()
        formatted_name = ' '.join(word.capitalize() for word in name_parts)
        
        generic_bio = f"""**{formatted_name}**
{formatted_name} is a notable person. Specific biographical information is not available in our database."""
        
        return [{
            'title': f"{formatted_name} (Person)",
            'content': generic_bio,
            'url': f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            'source': 'dictionary',
            'type': 'biography',
            'word': query,
            'part_of_speech': 'person',
            'definition': generic_bio,
            'example': '',
            'phonetic': '',
            'relevance_score': 0.75,
            'timestamp': None
        }]
    
    def _is_likely_proper_noun(self, query: str) -> bool:
        """Check if the query appears to be a proper noun that shouldn't be broken down."""
        query_words = query.strip().split()
        
        # Heuristics for proper noun detection
        if len(query_words) >= 2:
            # Multiple words with proper capitalization
            if all(word[0].isupper() for word in query_words if word):
                return True
        
        # Known proper noun patterns (including K-pop artists and other entities)
        proper_noun_indicators = [
            # Cities and places
            'new york', 'los angeles', 'chicago', 'san francisco', 'london', 'paris', 'tokyo', 'sydney',
            # K-pop artists and celebrities
            'park jimin', 'jimin bts', 'kim seok jin', 'jin bts', 'min yoon gi', 'suga bts', 'agust d',
            'jung ho seok', 'j-hope bts', 'kim nam joon', 'rm bts', 'kim tae hyung', 'v bts', 'jeon jung kook', 'jungkook bts',
            'taylor swift', 'elon musk', 'leonardo dicaprio', 'bill gates', 'matthew perry', 'steve jobs', 
            'donald trump', 'joe biden', 'barack obama', 'cristiano ronaldo', 'lionel messi', 'lebron james', 'michael jordan',
            'ariana grande', 'justin bieber', 'selena gomez', 'dua lipa', 'billie eilish', 'ed sheeran',
            'robert downey jr', 'scarlett johansson', 'chris evans', 'chris hemsworth', 'mark zuckerberg',
            'jeff bezos', 'warren buffett', 'oprah winfrey', 'ellen degeneres', 'jimmy fallon'
        ]
        
        query_lower = query.lower().strip()
        if query_lower in proper_noun_indicators:
            return True
        
        # Check for common Korean name patterns
        korean_name_patterns = [
            'park ', 'kim ', 'lee ', 'choi ', 'jung ', 'shin ', 'han ', 'oh ', 'seo ', 'kang ', 'yoon ', 'jang ', 'lim ', 'min '
        ]
        if any(query_lower.startswith(pattern) for pattern in korean_name_patterns) and len(query_words) >= 2:
            return True
            
        return False 