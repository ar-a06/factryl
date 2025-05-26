"""
Test script for YouTube scraper functionality.
"""

import asyncio
import json
from datetime import datetime
import os
from pathlib import Path
from loguru import logger
from app.scraper.media.youtube import YouTubeScraper
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import statistics
import webbrowser

# Configure logger to show debug messages
logger.remove()
logger.add(lambda msg: print(msg), level="DEBUG")

def format_number(value):
    """Format numbers with commas for thousands."""
    try:
        return "{:,}".format(value)
    except (ValueError, TypeError):
        return value

async def generate_report(results, query, time_filter):
    """Generate HTML report from results."""
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader('app/scraper/templates'))
    env.filters['format_number'] = format_number
    template = env.get_template('report_template.html')
    
    # Calculate average credibility
    credibility_scores = [r['credibility_info']['score'] for r in results]
    avg_credibility = statistics.mean(credibility_scores) if credibility_scores else 0
    
    # Render template
    html_content = template.render(
        source_name="YouTube",
        source_color="#FF0000",
        query=query,
        results=results,
        time_filter=time_filter,
        avg_credibility=avg_credibility,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Save report in the new scraper directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path('output/reports/scraper/youtube')
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"youtube_report_{timestamp}.html"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"\nReport generated: {report_path}")
    
    # Open report in default browser
    abs_path = os.path.abspath(str(report_path))
    webbrowser.open('file://' + abs_path)
    
    return str(report_path)

async def main():
    # Load configuration from file
    config_path = Path('config/config.json')
    try:
        with open(config_path, 'r') as f:
            full_config = json.load(f)
            # Extract YouTube-specific config
            config = {
                "scrapers": {
                    "youtube": full_config["scrapers"]["youtube"]
                },
                "cache": full_config["cache"],
                "reporting": full_config["reporting"]
            }
            logger.debug(f"Loaded config from {config_path}")
            logger.debug(f"YouTube config: {json.dumps(config['scrapers']['youtube'], indent=2)}")
    except FileNotFoundError:
        logger.error(f"Error: Configuration file not found at {config_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error: Invalid JSON in configuration file {config_path}")
        return
    
    # Load API key from environment variable
    load_dotenv()
    
    # Initialize scraper
    scraper = YouTubeScraper(config)
    
    try:
        # Validate configuration
        logger.info("Validating YouTube API configuration...")
        is_valid = await scraper.validate()
        if not is_valid:
            logger.error("Scraper validation failed. Please check your API key.")
            return
            
        # Test search queries
        queries = [
            "artificial intelligence latest developments",
            "climate change solutions 2024",
            "breaking news technology"
        ]
        
        all_results = []
        for query in queries:
            logger.info(f"\nSearching YouTube for: {query}")
            print("-" * 50)
            
            results = await scraper.scrape(query)
            all_results.extend(results)
            logger.info(f"Found {len(results)} results\n")
            
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"Title: {result['title']}")
                print(f"Channel: {result['channel_name']}")
                print(f"Duration: {result['duration']}")
                print(f"Views: {result['metadata']['views']:,}")
                print(f"Likes: {result['metadata']['likes']:,}")
                print(f"Comments: {result['metadata']['comments']:,}")
                print(f"Credibility Score: {result['credibility_info']['score']:.1f}")
                print(f"URL: {result['url']}")
                print("-" * 30)
        
        # Generate combined report for all results
        report_path = await generate_report(
            all_results,
            "Multiple Queries: " + ", ".join(queries),
            config['scrapers']['youtube']['time_filter']
        )
            
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main()) 