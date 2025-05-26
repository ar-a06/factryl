#!/usr/bin/env python3
"""
Scraper Report Generator - Uses existing test framework to generate comprehensive HTML reports
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import test configuration directly
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

try:
    from conftest import base_config, test_queries
except ImportError:
    # Fallback configuration if conftest is not available
    base_config = {
        "scrapers": {
            "blog": {"enabled": True},
            "weather": {"enabled": True, "api_key": "demo"},
            "news": {"enabled": True},
            "youtube": {"enabled": True, "api_key": "demo"}
        },
        "cache": {"enabled": False},
        "reporting": {"enabled": True}
    }
    test_queries = {
        "blog": "artificial intelligence",
        "weather": "New York",
        "news": "technology",
        "youtube": "AI developments"
    }
from app.scraper.blogs.blog import BlogScraper
from app.scraper.weather.weather import WeatherScraper
from app.scraper.news import NewsScraper
from app.scraper.media.youtube import YouTubeScraper

async def test_scraper_with_real_data(scraper_class, scraper_name: str, query: str, config: dict) -> Dict[str, Any]:
    """Test a scraper with real data and collect comprehensive results."""
    
    print(f"🔍 Testing {scraper_name} with query: '{query}'...")
    start_time = time.time()
    
    try:
        # Initialize scraper with real configuration
        scraper = scraper_class(config)
        
        # Get source information
        source_name = getattr(scraper, 'get_source_name', lambda: 'Unknown')()
        
        # Test validation
        validation_passed = True
        validation_error = None
        try:
            if hasattr(scraper, 'validate'):
                validation_passed = await asyncio.wait_for(scraper.validate(), timeout=10)
        except Exception as e:
            validation_passed = False
            validation_error = str(e)[:100]
        
        # Test scraping with timeout
        scrape_start = time.time()
        try:
            results = await asyncio.wait_for(scraper.scrape(query), timeout=30)
            scrape_duration = time.time() - scrape_start
            
            if results is None:
                results = []
            
            result_count = len(results)
            success = result_count > 0
            error_message = None if success else "No results returned"
            
            # Prepare sample results for display (first 3)
            sample_results = []
            if results and result_count > 0:
                for i, result in enumerate(results[:3]):
                    if isinstance(result, dict):
                        sample_results.append({
                            'title': result.get('title', 'No title'),
                            'url': result.get('url', result.get('link', '#')),
                            'source': result.get('source_name', result.get('source', source_name)),
                            'description': result.get('description', result.get('content', ''))[:150],
                            'date': result.get('date', result.get('publishedAt', 'N/A'))
                        })
            
        except asyncio.TimeoutError:
            scrape_duration = 30
            results = []
            result_count = 0
            success = False
            error_message = "Timeout after 30s"
            sample_results = []
            
        except Exception as e:
            scrape_duration = time.time() - scrape_start
            results = []
            result_count = 0
            success = False
            error_message = str(e)[:150]
            sample_results = []
        
        # Clean up
        if hasattr(scraper, 'close'):
            try:
                await scraper.close()
            except:
                pass
        
        total_duration = time.time() - start_time
        
        return {
            'name': scraper_name,
            'source': source_name,
            'query': query,
            'success': success,
            'validation_passed': validation_passed,
            'validation_error': validation_error,
            'result_count': result_count,
            'scrape_duration': round(scrape_duration, 2),
            'total_duration': round(total_duration, 2),
            'error_message': error_message,
            'sample_results': sample_results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        total_duration = time.time() - start_time
        return {
            'name': scraper_name,
            'source': 'Unknown',
            'query': query,
            'success': False,
            'validation_passed': False,
            'validation_error': None,
            'result_count': 0,
            'scrape_duration': 0,
            'total_duration': round(total_duration, 2),
            'error_message': str(e)[:150],
            'sample_results': [],
            'timestamp': datetime.now().isoformat()
        }

def generate_html_report(results: List[Dict[str, Any]], output_file: str = None):
    """Generate HTML report using the same format as before."""
    
    # Set default output file in the correct directory
    if output_file is None:
        os.makedirs("output/reports/scraper", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output/reports/scraper/scraper_report_{timestamp}.html"
    
    # Calculate statistics
    total_scrapers = len(results)
    working_scrapers = sum(1 for r in results if r['success'])
    validated_scrapers = sum(1 for r in results if r['validation_passed'])
    total_results = sum(r['result_count'] for r in results)
    total_duration = sum(r['total_duration'] for r in results)
    
    success_rate = (working_scrapers / total_scrapers * 100) if total_scrapers > 0 else 0
    validation_rate = (validated_scrapers / total_scrapers * 100) if total_scrapers > 0 else 0
    
    # Categorize results
    working = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Scraper System Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 700;
        }}
        .header .subtitle {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border-left: 4px solid;
        }}
        .stat-card.success {{ border-left-color: #27ae60; }}
        .stat-card.warning {{ border-left-color: #f39c12; }}
        .stat-card.danger {{ border-left-color: #e74c3c; }}
        .stat-card.info {{ border-left-color: #3498db; }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .scraper-grid {{
            display: grid;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .scraper-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }}
        .scraper-header {{
            padding: 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .scraper-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .status-badge {{
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-success {{
            background: #d4edda;
            color: #155724;
        }}
        .status-danger {{
            background: #f8d7da;
            color: #721c24;
        }}
        .scraper-details {{
            padding: 20px;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .detail-label {{
            font-weight: 600;
            color: #555;
            min-width: 120px;
        }}
        .detail-value {{
            color: #333;
            text-align: right;
        }}
        .query-text {{
            font-style: italic;
            color: #666;
        }}
        .error-message {{
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 5px;
            font-size: 0.9em;
            margin-top: 10px;
            border-left: 4px solid #dc3545;
        }}
        .results-section {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid #f0f0f0;
        }}
        .results-header {{
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
            font-size: 1.1em;
        }}
        .result-item {{
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 12px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }}
        .result-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 1.05em;
        }}
        .result-meta {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
        }}
        .result-description {{
            font-size: 0.9em;
            color: #555;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        .result-link {{
            color: #007bff;
            text-decoration: none;
            font-size: 0.85em;
            word-break: break-all;
        }}
        .result-link:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }}
        .performance-bar {{
            width: 100%;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }}
        .performance-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Comprehensive Scraper System Report</h1>
            <p class="subtitle">Real Data Collection & Performance Analysis</p>
            <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card success">
                <div class="stat-number">{total_scrapers}</div>
                <div class="stat-label">Total Scrapers</div>
            </div>
            <div class="stat-card {'success' if success_rate >= 75 else 'warning' if success_rate >= 50 else 'danger'}">
                <div class="stat-number">{working_scrapers}</div>
                <div class="stat-label">Working Scrapers</div>
            </div>
            <div class="stat-card info">
                <div class="stat-number">{total_results:,}</div>
                <div class="stat-label">Total Results</div>
            </div>
            <div class="stat-card {'success' if success_rate >= 75 else 'warning' if success_rate >= 50 else 'danger'}">
                <div class="stat-number">{success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>

        <div class="content">
            <div class="section">
                <h2>📊 System Performance Overview</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <h4>Success Rate</h4>
                        <div class="performance-bar">
                            <div class="performance-fill" style="width: {success_rate}%;"></div>
                        </div>
                        <p>{success_rate:.1f}% ({working_scrapers}/{total_scrapers} scrapers working)</p>
                    </div>
                    <div class="summary-card">
                        <h4>Validation Rate</h4>
                        <div class="performance-bar">
                            <div class="performance-fill" style="width: {validation_rate}%;"></div>
                        </div>
                        <p>{validation_rate:.1f}% ({validated_scrapers}/{total_scrapers} scrapers validated)</p>
                    </div>
                </div>
                <p><strong>Total Execution Time:</strong> {total_duration:.1f} seconds</p>
            </div>

            <div class="section">
                <h2>✅ Working Scrapers ({len(working)})</h2>
                <div class="scraper-grid">
"""

    # Add working scrapers with sample data
    for scraper in working:
        results_html = ""
        if scraper['sample_results']:
            results_html = f"""
                <div class="results-section">
                    <div class="results-header">📄 Sample Results ({len(scraper['sample_results'])} of {scraper['result_count']} total):</div>
"""
            for i, result in enumerate(scraper['sample_results'], 1):
                title = result.get('title', 'No title')
                description = result.get('description', '')
                if len(description) > 150:
                    description = description[:150] + '...'
                
                results_html += f"""
                    <div class="result-item">
                        <div class="result-title">{i}. {title}</div>
                        <div class="result-meta">Source: {result.get('source', 'Unknown')} | Date: {result.get('date', 'N/A')}</div>
                        {f'<div class="result-description">{description}</div>' if description else ''}
                        <a href="{result.get('url', '#')}" class="result-link" target="_blank">{result.get('url', '#')[:60]}{'...' if len(result.get('url', '')) > 60 else ''}</a>
                    </div>
"""
            results_html += "</div>"
        
        html_content += f"""
                    <div class="scraper-card">
                        <div class="scraper-header">
                            <div class="scraper-name">{scraper['name']}</div>
                            <div class="status-badge status-success">✅ Working</div>
                        </div>
                        <div class="scraper-details">
                            <div class="detail-row">
                                <span class="detail-label">Source:</span>
                                <span class="detail-value">{scraper['source']}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Query:</span>
                                <span class="detail-value query-text">"{scraper['query']}"</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Results Found:</span>
                                <span class="detail-value"><strong>{scraper['result_count']}</strong></span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Scrape Time:</span>
                                <span class="detail-value">{scraper['scrape_duration']}s</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Total Time:</span>
                                <span class="detail-value">{scraper['total_duration']}s</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Validation:</span>
                                <span class="detail-value">{'✓ Passed' if scraper['validation_passed'] else '✗ Failed'}</span>
                            </div>
                            {results_html}
                        </div>
                    </div>
"""

    # Add failed scrapers section
    html_content += f"""
                </div>
            </div>

            <div class="section">
                <h2>❌ Failed Scrapers ({len(failed)})</h2>
                <div class="scraper-grid">
"""

    for scraper in failed:
        html_content += f"""
                    <div class="scraper-card">
                        <div class="scraper-header">
                            <div class="scraper-name">{scraper['name']}</div>
                            <div class="status-badge status-danger">❌ Failed</div>
                        </div>
                        <div class="scraper-details">
                            <div class="detail-row">
                                <span class="detail-label">Source:</span>
                                <span class="detail-value">{scraper['source']}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Query:</span>
                                <span class="detail-value query-text">"{scraper['query']}"</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Duration:</span>
                                <span class="detail-value">{scraper['total_duration']}s</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Validation:</span>
                                <span class="detail-value">{'✓ Passed' if scraper['validation_passed'] else '✗ Failed'}</span>
                            </div>
                            {f'<div class="error-message"><strong>Error:</strong> {scraper["error_message"]}</div>' if scraper['error_message'] else ''}
                            {f'<div class="error-message"><strong>Validation Error:</strong> {scraper["validation_error"]}</div>' if scraper['validation_error'] else ''}
                        </div>
                    </div>
"""

    html_content += f"""
                </div>
            </div>
        </div>
        
        <div class="timestamp">
            Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            Total execution time: {total_duration:.1f}s | 
            {total_results:,} total results collected
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file

async def main():
    """Run comprehensive scraper tests using existing test framework."""
    print("🔍 COMPREHENSIVE SCRAPER TESTING WITH REAL DATA")
    print("=" * 60)
    
    # Use existing test configuration
    config = {
        'cache': {'enabled': False},
        'scraping': {
            'max_total_articles': 5,
            'min_credibility_score': 85,
            'rate_limit': {
                'requests_per_minute': 30,
                'concurrent_requests': 3
            }
        },
        'apis': {
            'openweathermap': {'base_url': 'https://api.openweathermap.org/data/2.5', 'units': 'metric'},
            'weatherapi': {'base_url': 'https://api.weatherapi.com/v1', 'days': 3},
            'youtube': {'base_url': 'https://www.googleapis.com/youtube/v3', 'max_results': 10}
        }
    }
    
    # Use existing test queries
    test_scenarios = [
        (WeatherScraper, "Weather Scraper", "London,UK"),
        (YouTubeScraper, "YouTube Scraper", "python tutorial"),
        (BlogScraper, "Blog Scraper", "artificial intelligence latest developments"),
        (NewsScraper, "News Scraper", "climate change impact"),
    ]
    
    results = []
    
    for scraper_class, name, query in test_scenarios:
        result = await test_scraper_with_real_data(scraper_class, name, query, config)
        results.append(result)
        
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {name}: {result['result_count']} results in {result['total_duration']}s")
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Generate reports
    print("\n📄 Generating reports...")
    html_file = generate_html_report(results)
    
    # Save JSON data in the same directory
    json_file = html_file.replace('.html', '_data.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Summary
    working_count = sum(1 for r in results if r['success'])
    total_results = sum(r['result_count'] for r in results)
    
    print(f"\n🎉 Testing Complete!")
    print(f"📄 HTML Report: {os.path.abspath(html_file)}")
    print(f"📊 JSON Data: {os.path.abspath(json_file)}")
    print(f"\n📊 Summary:")
    print(f"   Working scrapers: {working_count}/{len(results)}")
    print(f"   Total results: {total_results:,}")
    print(f"   Success rate: {working_count/len(results)*100:.1f}%")
    
    return html_file

if __name__ == "__main__":
    result_file = asyncio.run(main())
    print(f"\n🌐 View report: file://{os.path.abspath(result_file)}") 