# Factryl - Intelligent Search & Analysis Platform

Factryl is a comprehensive information aggregation and analysis system that generates intelligent search results from multiple data sources with **AI-powered insights** and **real-time YouTube video integration**. The system uses advanced LLM technology, multi-source data aggregation, and intelligent analysis to provide comprehensive search results with detailed analysis, bias detection, and credibility scoring.

## Demo

[▶️ Watch Demo Video](static/images/docs/factrylDemo.mp4)

### Key Features Showcased in Demo:
1. **Intelligent Search**: Real-time search results with AI analysis
2. **Multi-source Integration**: Aggregated results from news, social media, and research sources
3. **YouTube Integration**: Seamless video content integration
4. **Advanced Analysis**: Bias detection, credibility scoring, and sentiment analysis

## Core Architecture

### 1. Factryl Engine (`app/core/factryl_engine.py`)
- **Multi-Source Integration**: Orchestrates data collection from 20+ sources
- **Intelligent Processing**: Coordinates analysis, scoring, and ranking
- **LLM Integration**: Multiple LLM options with fallback mechanisms
- **Smart Source Management**: Optimizes content prioritization
- **Real-time Processing**: Async operations for fast results
- **Health Monitoring**: Continuous system health checks

### 2. Analysis Components (`app/analyzer/`)

#### Relevance Analyzer
- TF-IDF vectorization with semantic matching
- Entity-aware relevance scoring
- Keyword density analysis
- Title match boosting
- Context-aware scoring

#### Credibility Analyzer
- Domain reputation scoring (0-1.0)
- Source type classification
- Content quality assessment
- Author credibility analysis
- Risk factor detection
- Comprehensive scoring model

#### Bias Analyzer
- Political bias detection
- Emotional language analysis
- Source bias evaluation
- Gender bias detection
- Loaded language identification
- Bias type classification

#### Sentiment Analyzer
- TextBlob-based analysis
- Rule-based enhancement
- Emotional keyword detection
- Confidence scoring
- Subjectivity assessment

### 3. Aggregation System (`app/aggregator/`)

#### Content Combiner
- Unified content format
- Source credibility integration
- Metadata preservation
- Smart sorting algorithms
- Source statistics tracking

#### Deduplicator
- Multi-stage deduplication
- URL similarity analysis
- Content similarity detection
- Metadata merging
- Configurable thresholds

#### Content Scorer
- Composite scoring system
- Entity-specific scoring
- Source-specific boosts
- Engagement metrics
- Temporal relevance
- Explanation generation

### 4. Data Sources

#### News & Media
- BBC News
- TechCrunch
- Google News
- Business News
- Economics News
- Education News
- Entertainment News
- Politics News
- Sports News
- Tech Publications

#### Search Engines
- DuckDuckGo
- Bing
- Safari
- Edge

#### Knowledge & Research
- Wikipedia
- ArXiv
- Research Blogs
- Google Scholar
- Dictionary Integration

#### Social & Community
- Reddit
- Quora
- Dev.to
- IndieHackers
- ProductHunt
- StackOverflow
- Hacker News

#### Blogs & Publishing
- Medium
- Substack
- Ghost Platform

#### Multimedia
- YouTube Integration
- Podcast Data
- Twitch Streams

#### Specialized Sources
- Government Data
- Weather Information
- E-commerce Data
- Event Aggregation

## Analysis Capabilities

### 1. Content Analysis
- **Relevance Scoring**: Advanced TF-IDF with semantic understanding
- **Credibility Assessment**: Multi-factor source and content evaluation
- **Bias Detection**: Comprehensive bias type identification
- **Sentiment Analysis**: Enhanced emotional content analysis

### 2. Source Analysis
- **Domain Reputation**: Extensive domain credibility database
- **Source Classification**: Intelligent source type identification
- **Content Quality**: Multi-dimensional quality assessment
- **Risk Detection**: Automated risk factor identification

### 3. Entity Analysis
- **Entity Recognition**: Known entity database
- **Context Understanding**: Entity-specific scoring
- **Relationship Mapping**: Entity connection analysis
- **Topic Classification**: Smart topic categorization

### 4. Engagement Analysis
- **Platform-Specific Metrics**: Custom scoring per platform
- **Temporal Analysis**: Time-based relevance scoring
- **User Interaction**: Engagement metric analysis
- **Content Depth**: Quality-based scoring

## Intelligent Features

### 1. Smart Processing
- **Async Operations**: Parallel data processing
- **Batch Processing**: Efficient content handling
- **Rate Limiting**: Intelligent API management
- **Cache Management**: Smart content caching

### 2. Content Enhancement
- **Full Text Extraction**: Advanced content parsing
- **Metadata Enhancement**: Rich metadata integration
- **Source Verification**: Automated source checking
- **Content Cleaning**: Smart text preprocessing

### 3. Deduplication System
- **Multi-Stage Process**: Progressive duplicate detection
- **Similarity Analysis**: Advanced content comparison
- **URL Normalization**: Smart URL processing
- **Metadata Merging**: Intelligent data combination

### 4. Scoring System
- **Composite Scoring**: Multi-factor evaluation
- **Dynamic Weighting**: Context-aware scoring
- **Source Boosting**: Intelligent source prioritization
- **Temporal Relevance**: Time-based adjustments

## API Endpoints

### Core Search
- `POST /api/search`: Main search endpoint
- `GET /api/sources`: Available sources
- `GET /api/health`: System health
- `GET /api/llm-health`: LLM service status

### Content Analysis
- `POST /api/generate-summary`: AI summary generation
- `POST /api/article-summary`: Single article summary
- `POST /api/batch-article-summaries`: Batch processing

### Media Integration
- `POST /api/youtube-videos`: YouTube video search
- `POST /api/video-details`: Detailed video info
- `POST /api/image-search`: Related image search

## Configuration

### Environment Setup
```bash
# Core Configuration
FLASK_ENV=development
DEBUG=True

# LLM Configuration
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=llama3.1:8b
LLM_TIMEOUT=30
LLM_MAX_TOKENS=500
LLM_TEMPERATURE=0.7

# API Keys
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### Performance Settings
- **Batch Size**: 10-15 articles per batch
- **Cache TTL**: 3600 seconds
- **Rate Limits**: Platform-specific
- **Timeout**: 8 seconds per source
- **Memory Usage**: 2-4GB during processing

## Project Structure

```
factryl/
├── app/
│   ├── core/
│   │   ├── factryl_engine.py     # Main orchestrator
│   │   ├── ollama_analyzer.py    # LLM integration
│   │   └── article_extractor.py  # Content extraction
│   ├── analyzer/
│   │   ├── relevance.py          # Relevance scoring
│   │   ├── credibility.py        # Source credibility
│   │   ├── bias.py              # Bias detection
│   │   └── sentiment.py         # Sentiment analysis
│   ├── aggregator/
│   │   ├── combiner.py          # Content combination
│   │   ├── deduplicator.py      # Duplicate removal
│   │   └── scorer.py            # Content scoring
│   └── scraper/                 # Source-specific scrapers
├── config/
│   └── config.json              # Configuration
└── templates/
    └── simple_search.html       # Web interface
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Factryl** - Transforming search queries into intelligent insights with comprehensive analysis and real-time integration!
