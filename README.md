# Factryl - Intelligent Search & Analysis Platform

Factryl is a comprehensive information aggregation and analysis system that generates intelligent search results from multiple data sources. When you search for any topic, the system scrapes available sources, analyzes the content, and produces ranked results with detailed analysis, AI-powered summaries, and visual insights.

## Live Demo

```bash
# Start the application
python app.py
```

Then visit `http://localhost:5000` to access the modern web interface.

## Core Features

**Input**: Any search query (e.g., "artificial intelligence", "climate change", "discovery")  
**Output**: Comprehensive search results with:
- **Multi-source data aggregation** from news, search engines, knowledge bases
- **Content analysis** (sentiment, credibility, bias, relevance scoring)
- **Intelligent ranking** using composite scoring algorithms
- **AI-powered summaries** with dictionary definitions
- **Visual search interface** with related image results
- **Source credibility indicators** and bias detection

## System Architecture

### Core Components

1. **Factryl Engine** (`app/core/factryl_engine.py`)
   - Orchestrates the entire search pipeline
   - Manages scrapers, analyzers, and aggregators
   - Generates final ranked search results

2. **Multi-Source Scrapers** (`app/scraper/`)
   - **News**: BBC News, TechCrunch, Google News
   - **Search**: DuckDuckGo, Bing, Safari, Edge
   - **Knowledge**: Wikipedia
   - **Dictionary**: Comprehensive word definitions and pronunciations
   - **Social**: Hacker News

3. **Content Analyzers** (`app/analyzer/`)
   - **Relevance**: TF-IDF and keyword matching
   - **Sentiment**: TextBlob + rule-based analysis
   - **Credibility**: Domain reputation and content quality
   - **Bias**: Political, emotional, and source bias detection

4. **Data Aggregators** (`app/aggregator/`)
   - **Content Combiner**: Standardizes data from multiple sources
   - **Deduplicator**: Removes similar content using similarity detection
   - **Content Scorer**: Ranks content using composite scoring

## Processing Pipeline

```
User Query → Multi-Source Scrapers → Content Combiner → Deduplicator → Analyzers → Scorer → Ranked Results
```

### Detailed Flow

1. **Data Collection**: Scrape multiple sources simultaneously using async processing
2. **Content Standardization**: Combine data into unified format with metadata
3. **Deduplication**: Remove similar/duplicate content using similarity detection
4. **Analysis**: Run sentiment, credibility, bias, and relevance analysis
5. **Scoring**: Calculate composite scores for intelligent ranking
6. **Results**: Return ranked search results with comprehensive analysis

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation & Setup

1. **Clone and setup**:
```bash
git clone https://github.com/ar-a06/factryl.git
cd factryl
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
python app.py
```

4. **Access the interface**:
   - Open your browser to `http://localhost:5000`
   - Enter any search query and explore the results!

### API Usage (Programmatic)

```python
from app.core.factryl_engine import FactrylEngine

# Initialize the engine
engine = FactrylEngine()

# Process a search
result = await engine.search(
    query="artificial intelligence",
    max_results=50
)

# Access results
print(f"Found {len(result['items'])} items")
print(f"Processing time: {result['stats']['processing_time']:.2f}s")
print(f"Sources used: {result['stats']['successful_sources']}")
```

## Current Features

### Modern Web Interface
- Clean, responsive search interface
- Real-time search results with live updates
- Interactive result cards with source information
- AI-powered summaries and insights
- Dictionary definitions with pronunciations
- Related image search integration
- Source credibility indicators and bias warnings

### Available Data Sources
- **News**: BBC News, TechCrunch, Google News aggregation
- **Search Engines**: DuckDuckGo, Bing, Safari, Edge integration
- **Knowledge**: Wikipedia comprehensive coverage
- **Dictionary**: Word definitions, pronunciations, etymology
- **Social**: Hacker News community discussions

### Analysis Capabilities
- **Relevance Scoring**: TF-IDF vectorization and keyword matching
- **Sentiment Analysis**: Polarity (-1 to +1) and subjectivity measurement
- **Credibility Assessment**: Domain reputation and content quality metrics
- **Bias Detection**: Political, emotional, and source bias indicators

## Project Structure

```
factryl/
├── app.py                          # Main Flask application entry point
├── app/
│   ├── core/
│   │   └── factryl_engine.py      # Main search engine orchestrator
│   ├── scraper/
│   │   ├── base.py                # Base scraper classes
│   │   ├── news/                  # News source scrapers
│   │   ├── search/                # Search engine scrapers
│   │   ├── knowledge/             # Wikipedia and knowledge bases
│   │   ├── dictionary/            # Dictionary and definitions
│   │   └── social/                # Social media scrapers
│   ├── analyzer/
│   │   ├── relevance.py           # Relevance scoring algorithms
│   │   ├── sentiment.py           # Sentiment analysis
│   │   ├── credibility.py         # Credibility assessment
│   │   └── bias.py                # Bias detection
│   └── aggregator/
│       ├── combiner.py            # Content standardization
│       ├── deduplicator.py        # Duplicate removal
│       └── scorer.py              # Content scoring and ranking
├── templates/
│   └── simple_search.html         # Modern web interface
├── requirements.txt                # Python dependencies
└── README.md                      # This file
```

## Dependencies

Core dependencies include:
- **Flask**: Web framework for the interface
- **aiohttp**: Async HTTP client for scraping
- **BeautifulSoup4**: HTML parsing and web scraping
- **TextBlob**: Natural language processing and sentiment analysis
- **scikit-learn**: Machine learning for text analysis
- **transformers**: AI models for advanced analysis

See `requirements.txt` for the complete dependency list.

## Example Results

### Search Query: "discovery"
```
Results Summary:
- Sources: 4 active scrapers
- Items Found: 40 results
- Processing Time: ~1 second
- Features: AI summary, dictionary definition, related image

Analysis Breakdown:
- Sentiment: Mixed positive/neutral results
- Credibility: High credibility from reliable sources  
- Relevance: Ranked by composite scoring algorithm
- Sources: News articles, search results, knowledge bases
```

## Configuration

All configuration is handled in-memory within the `FactrylEngine` class:
- **Source credibility scores**: Predefined reputation ratings
- **Analysis parameters**: Scoring weights and thresholds
- **Scraper settings**: Rate limiting and timeout configurations

No external configuration files needed - everything works out of the box!

## Use Cases

1. **Research & Analysis**: Comprehensive multi-source topic research
2. **Market Intelligence**: Real-time market and trend analysis
3. **News Aggregation**: Intelligent news synthesis with bias detection
4. **Academic Research**: Multi-source literature review and fact-checking
5. **Business Intelligence**: Competitive analysis and market research
6. **General Knowledge**: Quick, comprehensive information gathering

## Key Advantages

- **Fast**: Sub-second processing for most queries
- **Intelligent**: Multi-dimensional analysis with AI integration
- **Comprehensive**: Multiple sources aggregated intelligently
- **Accurate**: Credibility scoring and bias detection
- **Modern**: Clean, responsive web interface
- **Efficient**: Async processing and smart caching
- **Extensible**: Modular architecture for easy enhancement

## Success Metrics

- **Multi-source Integration**: Successfully aggregates from 4+ live sources
- **Intelligent Analysis**: 4-dimensional analysis (relevance, sentiment, credibility, bias)
- **Fast Processing**: Sub-second processing for most queries
- **Modern Interface**: Beautiful, responsive web application
- **AI Integration**: LLM-powered summaries and insights
- **Production Ready**: Stable Flask application with error handling

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Factryl** - Transforming search queries into intelligent insights! 
