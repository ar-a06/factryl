# Factryl - Intelligent Search & Analysis Platform

Factryl is a comprehensive information aggregation and analysis system that generates intelligent search results from multiple data sources with **AI-powered insights**. When you search for any topic, the system scrapes available sources, analyzes the content with LLM technology, and produces ranked results with detailed analysis, AI-powered summaries, and visual insights.

## Live Demo

```bash
# Start the application
python app.py
```

Then visit `http://localhost:5000` to access the modern web interface with real-time AI analysis.

## Core Features

**Input**: Any search query (e.g., "artificial intelligence", "climate change", "discovery")  
**Output**: Comprehensive search results with:
- **Multi-source data aggregation** from news, search engines, knowledge bases
- **AI-powered intelligence reports** using local LLM technology
- **Smart article summaries** with individual content analysis
- **Content analysis** (sentiment, credibility, bias, relevance scoring)
- **Intelligent ranking** using composite scoring algorithms
- **Visual search interface** with related image results and video insights
- **Source credibility indicators** and bias detection
- **Real-time AI processing** with fallback systems

## AI-Powered Features

### Intelligence Reports
The system generates comprehensive intelligence summaries by analyzing multiple articles about a topic, providing:
- Key insights and trends across sources
- Source credibility analysis and cross-verification
- Sentiment analysis across multiple sources
- Temporal analysis of coverage patterns

### Article Summarization
Individual articles receive AI-powered summaries that:
- Extract key points and main arguments
- Maintain factual accuracy and source attribution
- Provide concise, readable summaries (50-120 words)
- Use local LLM processing for privacy and speed

### LLM Integration
- **Local Processing**: Uses Ollama + Llama 3.1 for privacy-first AI
- **Real-time Analysis**: Instant LLM processing for search results
- **Fallback Systems**: Graceful degradation when LLM unavailable
- **Performance Monitoring**: Built-in health checks and timing
- **Scalable Architecture**: Batch processing for efficiency

## System Architecture

### Core Components

1. **Factryl Engine** (`app/core/factryl_engine.py`)
   - Orchestrates the entire search pipeline
   - Manages scrapers, analyzers, and aggregators
   - Integrates LLM analysis into search results
   - Generates final ranked search results

2. **AI Integration** (`app/core/ollama_analyzer.py`)
   - Manages local LLM communication
   - Handles model loading and inference
   - Provides health checking and monitoring
   - Coordinates batch processing for efficiency

3. **Multi-Source Scrapers** (`app/scraper/`)
   - **News**: BBC News, TechCrunch, Google News
   - **Search**: DuckDuckGo, Bing, Safari, Edge
   - **Knowledge**: Wikipedia
   - **Dictionary**: Comprehensive word definitions and pronunciations
   - **Social**: Hacker News
   - **Video**: YouTube integration with metadata

4. **Content Analyzers** (`app/analyzer/`)
   - **Relevance**: TF-IDF and keyword matching
   - **Sentiment**: TextBlob + rule-based analysis
   - **Credibility**: Domain reputation and content quality
   - **Bias**: Political, emotional, and source bias detection

5. **Data Aggregators** (`app/aggregator/`)
   - **Content Combiner**: Standardizes data from multiple sources
   - **Deduplicator**: Removes similar content using similarity detection
   - **Content Scorer**: Ranks content using composite scoring

## Processing Pipeline

```
User Query → Multi-Source Scrapers → Content Combiner → LLM Analysis → Deduplicator → Analyzers → Scorer → AI-Enhanced Results
```

### Detailed Flow

1. **Data Collection**: Scrape multiple sources simultaneously using async processing
2. **Content Standardization**: Combine data into unified format with metadata
3. **AI Analysis**: Process content through local LLM for intelligent summaries
4. **Deduplication**: Remove similar/duplicate content using similarity detection
5. **Analysis**: Run sentiment, credibility, bias, and relevance analysis
6. **Scoring**: Calculate composite scores for intelligent ranking
7. **Results**: Return ranked search results with comprehensive AI analysis

## Quick Start

### Prerequisites
- Python 3.9 or higher
- 8GB+ RAM (recommended for local LLM)
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

3. **Optional: Setup Local LLM (for AI features)**:
```bash
# Install Ollama for AI-powered summaries
curl -fsSL https://ollama.com/install.sh | sh

# Pull the Llama model
ollama pull llama3.1:8b

# Start Ollama service
ollama serve
```

4. **Run the application**:
```bash
python app.py
```

5. **Access the interface**:
   - Open your browser to `http://localhost:5000`
   - Enter any search query and explore the AI-enhanced results!

### API Usage (Programmatic)

```python
from app.core.factryl_engine import FactrylEngine

# Initialize the engine with AI capabilities
engine = FactrylEngine()

# Process a search with AI analysis
result = await engine.search(
    query="artificial intelligence",
    max_results=50
)

# Access AI-enhanced results
print(f"Found {len(result['items'])} items")
print(f"AI Summary: {result['summary']}")
print(f"Processing time: {result['stats']['processing_time']:.2f}s")
print(f"Sources used: {result['stats']['successful_sources']}")

# Generate individual article summary
article = result['items'][0]
ai_summary = await engine.generate_article_summary(article)
print(f"AI Article Summary: {ai_summary}")
```

## Current Features

### Modern Web Interface
- Clean, responsive search interface with professional design
- Real-time search results with live AI processing
- Interactive result cards with smart summaries
- AI-powered intelligence reports and definitions
- Dictionary definitions with pronunciations
- Related image search and video insights integration
- Source credibility indicators and bias warnings
- Performance monitoring and health checks

### Available Data Sources
- **News**: BBC News, TechCrunch, Google News aggregation
- **Search Engines**: DuckDuckGo, Bing, Safari, Edge integration
- **Knowledge**: Wikipedia comprehensive coverage
- **Dictionary**: Word definitions, pronunciations, etymology
- **Social**: Hacker News community discussions
- **Video**: YouTube integration with most-viewed content

### Analysis Capabilities
- **AI Intelligence Reports**: Multi-article analysis with LLM insights
- **Smart Article Summaries**: Individual content summarization
- **Relevance Scoring**: TF-IDF vectorization and keyword matching
- **Sentiment Analysis**: Polarity (-1 to +1) and subjectivity measurement
- **Credibility Assessment**: Domain reputation and content quality metrics
- **Bias Detection**: Political, emotional, and source bias indicators

### LLM Features
- **Local Processing**: Privacy-first AI with Ollama integration
- **Real-time Analysis**: Instant intelligent summaries
- **Fallback Systems**: Graceful degradation for reliability
- **Batch Processing**: Efficient multi-article analysis
- **Health Monitoring**: Real-time LLM status and performance tracking

## Project Structure

```
factryl/
├── app.py                          # Main Flask application entry point
├── app/
│   ├── core/
│   │   ├── factryl_engine.py      # Main search engine orchestrator
│   │   └── ollama_analyzer.py     # LLM integration and AI analysis
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
│   └── simple_search.html         # Modern web interface with AI features
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
- **ollama**: Local LLM integration for AI features
- **transformers**: AI models for advanced analysis

See `requirements.txt` for the complete dependency list.

## LLM Configuration

### Environment Variables
```bash
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=llama3.1:8b
LLM_TIMEOUT=30
LLM_MAX_TOKENS=500
LLM_TEMPERATURE=0.7
```

### Model Options
- **llama3.1:8b** (Recommended): Best balance of speed and quality
- **llama3.1:70b**: Higher quality, requires more resources
- **mistral:7b**: Faster processing, good for high-volume
- **codellama:13b**: Specialized for technical content

## Example Results

### Search Query: "artificial intelligence"
```
Results Summary:
- Sources: 5+ active scrapers including YouTube
- Items Found: 40 results with AI analysis
- Processing Time: ~2-3 seconds (including AI processing)
- Features: AI intelligence report, individual summaries, video insights

AI Analysis:
- Intelligence Report: Comprehensive multi-source analysis
- Article Summaries: 50-120 word intelligent summaries per article
- Sentiment: Mixed positive/neutral results across sources
- Credibility: High credibility from reliable sources  
- Video Insights: Most viewed videos with metadata analysis
```

## Performance & Hardware

### System Requirements

**Minimum Requirements:**
- 8GB RAM
- 4 CPU cores
- 10GB free disk space
- Stable internet connection

**Recommended Requirements:**
- 16GB+ RAM
- 8+ CPU cores
- SSD storage
- High-speed internet

### Performance Metrics
- **Search Results**: Sub-second for basic queries
- **AI Intelligence Reports**: 2-5 seconds per comprehensive analysis
- **Article Summaries**: 0.5-2 seconds per article
- **Batch Processing**: 10-50 articles per minute
- **Memory Usage**: 2-4GB during active AI processing

## Configuration

All configuration is handled in-memory within the `FactrylEngine` class:
- **Source credibility scores**: Predefined reputation ratings
- **Analysis parameters**: Scoring weights and thresholds
- **Scraper settings**: Rate limiting and timeout configurations
- **LLM settings**: Model selection, temperature, token limits

No external configuration files needed - everything works out of the box!

## Use Cases

1. **Research & Analysis**: Comprehensive multi-source topic research with AI insights
2. **Market Intelligence**: Real-time market and trend analysis with intelligent summaries
3. **News Aggregation**: Intelligent news synthesis with bias detection and AI analysis
4. **Academic Research**: Multi-source literature review with AI-powered fact-checking
5. **Business Intelligence**: Competitive analysis and market research with smart insights
6. **General Knowledge**: Quick, comprehensive information gathering with AI enhancement

## Key Advantages

- **AI-Powered**: Local LLM integration for intelligent analysis
- **Fast**: Sub-second processing for most queries, 2-5s for AI analysis
- **Intelligent**: Multi-dimensional analysis with AI integration
- **Comprehensive**: Multiple sources aggregated intelligently
- **Accurate**: Credibility scoring and bias detection
- **Modern**: Clean, responsive web interface with professional design
- **Efficient**: Async processing and smart caching
- **Private**: Local AI processing for data privacy
- **Extensible**: Modular architecture for easy enhancement

## Success Metrics

- **AI Integration**: Local LLM processing with intelligent summaries
- **Multi-source Integration**: Successfully aggregates from 5+ live sources
- **Intelligent Analysis**: Multi-dimensional analysis with AI enhancement
- **Fast Processing**: Sub-second basic processing, 2-5s for AI analysis
- **Modern Interface**: Beautiful, responsive web application
- **Video Integration**: YouTube insights with metadata analysis
- **Production Ready**: Stable Flask application with comprehensive error handling

## Best Practices

### Performance Optimization
1. **Batch Processing**: Process multiple articles together
2. **Caching**: Cache frequently requested summaries
3. **Async Operations**: Use async/await for non-blocking operations
4. **Resource Monitoring**: Monitor RAM and CPU usage

### Content Quality
1. **Input Validation**: Ensure clean, well-formatted input text
2. **Length Management**: Optimize input length for best results
3. **Context Preservation**: Maintain article context and source attribution
4. **Fact Checking**: Implement validation for generated content

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Factryl** - Transforming search queries into intelligent insights with AI-powered analysis! 
