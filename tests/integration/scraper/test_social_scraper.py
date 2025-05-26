"""
Test script to try out the social media scraper.
"""

import asyncio
from app.scraper.social import SocialScraper
import json
from datetime import datetime
import os
from pathlib import Path

async def main():
    # Load configuration from file
    config_path = Path('config/social_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file {config_path}")
        return
    
    # Load API credentials from environment variables
    if 'auth' in config['social']:
        # LinkedIn credentials
        if 'linkedin' in config['social']['auth']:
            linkedin_auth = config['social']['auth']['linkedin']
            linkedin_auth['client_id'] = os.getenv('LINKEDIN_CLIENT_ID', linkedin_auth.get('client_id', ''))
            linkedin_auth['client_secret'] = os.getenv('LINKEDIN_CLIENT_SECRET', linkedin_auth.get('client_secret', ''))
            linkedin_auth['access_token'] = os.getenv('LINKEDIN_ACCESS_TOKEN', linkedin_auth.get('access_token', ''))
        
        # Facebook credentials
        if 'facebook' in config['social']['auth']:
            facebook_auth = config['social']['auth']['facebook']
            facebook_auth['access_token'] = os.getenv('FACEBOOK_ACCESS_TOKEN', facebook_auth.get('access_token', ''))
    
    # Initialize scraper
    scraper = SocialScraper(config)
    
    try:
        # Validate configuration
        is_valid = await scraper.validate()
        if not is_valid:
            print("Error: Scraper validation failed. Please check your API credentials.")
            return
            
        # Test search queries
        queries = [
            "artificial intelligence latest developments",
            "climate change solutions",
            "remote work trends"
        ]
        
        for query in queries:
            print(f"\nSearching for: {query}")
            print("-" * 50)
            
            results = await scraper.scrape(query)
            print(f"Found {len(results)} results\n")
            
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"Source: {result['source']}")
                print(f"Title: {result['title']}")
                print(f"Author: {result['author']}")
                print(f"Credibility Score: {result['credibility_info']['score']}")
                print(f"Engagement: {result['metadata']['likes']} likes, {result['metadata']['comments']} comments")
                print(f"URL: {result['url']}")
                print("-" * 30)
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"social_results_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {filename}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main()) 