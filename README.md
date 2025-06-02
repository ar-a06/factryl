# Factryl - Intelligent Search & Analysis Platform

Factryl is a comprehensive information aggregation and analysis system that generates intelligent search results from multiple data sources with **AI-powered insights** and **real-time YouTube video integration**. When you search for any topic, the system scrapes available sources, analyzes the content with LLM technology, and produces ranked results with detailed analysis, AI-powered summaries, visual insights, and integrated video content.

## Live Demo

```bash
# Start the application
python app.py
```

Then visit `http://localhost:5000` to access the modern web interface with real-time AI analysis and YouTube video integration.

## Core Features

**Input**: Any search query (e.g., "artificial intelligence", "Taylor Swift", "programming tutorials")  
**Output**: Comprehensive search results with:
- **Multi-source data aggregation** from news, search engines, knowledge bases
- **Real-time YouTube video integration** with authentic API data
- **AI-powered intelligence reports** using local LLM technology
- **Smart article summaries** with individual content analysis
- **Interactive video player** with navigation controls and detailed statistics
- **Content analysis** (sentiment, credibility, bias, relevance scoring)
- **Intelligent ranking** using composite scoring algorithms
- **Visual search interface** with related image results and video insights
- **Source credibility indicators** and bias detection
- **Real-time AI processing** with fallback systems

## YouTube Video Integration

### Real-Time Video Data
- **Authentic YouTube API Integration**: Uses YouTube Data API v3 for real video statistics
- **Real View Counts**: Displays actual YouTube view counts (millions, billions formatting)
- **Top 3 Most-Viewed Videos**: Shows the most popular videos for any search query
- **Live Statistics**: Real-time likes, comments, engagement rates from YouTube API

### Interactive Video Experience
- **Embedded Video Player**: Full YouTube video playback directly in the interface
- **Navigation Controls**: Previous/Next buttons with seamless looping (Video 1 ↔ 2 ↔ 3 ↔ 1)
- **Detailed Statistics Modal**: Click video info to see comprehensive video stats
- **Video Metadata**: Duration, published date, channel information, engagement metrics

### Video Statistics Features
- **Comprehensive Stats**: Views, likes, comments, duration, published date, engagement rate
- **Sentiment Analysis**: Overall sentiment indicators based on comments
- **Top Comments**: Featured comments with sentiment analysis and like counts
- **Consistent Data**: Matching view counts between video tiles and detailed stats
- **Compact Design**: Stats modal follows the same clean design as article stats

### Environment Setup for YouTube
```bash
# Required: YouTube API Key in config/.env
YOUTUBE_API_KEY=your_youtube_api_key_here
```

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
   - Coordinates YouTube API integration

2. **YouTube Integration** (`app.py`)
   - **Real YouTube API Integration**: Fetches authentic video data using YouTube Data API v3
   - **Two-Stage API Process**: Search API + Statistics API for complete data
   - **Fallback System**: Curated data when API unavailable
   - **Video Details Endpoint**: `/api/video-details` for comprehensive video information

3. **AI Integration** (`app/core/ollama_analyzer.py`)
   - Manages local LLM communication
   - Handles model loading and inference
   - Provides health checking and monitoring
   - Coordinates batch processing for efficiency

4. **Multi-Source Scrapers** (`app/scraper/`)
   - **News**: BBC News, TechCrunch, Google News
   - **Search**: DuckDuckGo, Bing, Safari, Edge
   - **Knowledge**: Wikipedia
   - **Dictionary**: Comprehensive word definitions and pronunciations
   - **Social**: Hacker News
   - **Video**: YouTube integration with real-time metadata

5. **Content Analyzers** (`app/analyzer/`)
   - **Relevance**: TF-IDF and keyword matching
   - **Sentiment**: TextBlob + rule-based analysis
   - **Credibility**: Domain reputation and content quality
   - **Bias**: Political, emotional, and source bias detection

## Processing Pipeline

```
User Query → Multi-Source Scrapers → YouTube API Integration → Content Combiner → LLM Analysis → Deduplicator → Analyzers → Scorer → AI-Enhanced Results with Video Content
```

### Detailed Flow

1. **Data Collection**: Scrape multiple sources simultaneously using async processing
2. **YouTube Integration**: Fetch real video data from YouTube API v3 with statistics
3. **Content Standardization**: Combine data into unified format with metadata
4. **AI Analysis**: Process content through local LLM for intelligent summaries
5. **Video Processing**: Generate detailed video statistics and sentiment analysis
6. **Deduplication**: Remove similar/duplicate content using similarity detection
7. **Analysis**: Run sentiment, credibility, bias, and relevance analysis
8. **Scoring**: Calculate composite scores for intelligent ranking
9. **Results**: Return ranked search results with comprehensive AI analysis and video integration

## Quick Start

### Prerequisites
- Python 3.9 or higher
- 8GB+ RAM (recommended for local LLM)
- YouTube Data API v3 key (for video features)
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

3. **Setup YouTube API** (Required for video features):
```bash
# Create config/.env file
mkdir -p config
echo "YOUTUBE_API_KEY=your_youtube_api_key_here" > config/.env
```

4. **Optional: Setup Local LLM** (for AI features):
```bash
# Install Ollama for AI-powered summaries
curl -fsSL https://ollama.com/install.sh | sh

# Pull the Llama model
ollama pull llama3.1:8b

# Start Ollama service
ollama serve
```

5. **Run the application**:
```bash
python app.py
```

6. **Access the interface**:
   - Open your browser to `http://localhost:5000`
   - Enter any search query and explore the AI-enhanced results with YouTube videos!

### API Configuration

Create a `config/.env` file with your API keys:
```bash
# YouTube Data API v3 (Required for video features)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Optional: Ollama Configuration
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=llama3.1:8b
LLM_TIMEOUT=30
LLM_MAX_TOKENS=500
LLM_TEMPERATURE=0.7
```

## Current Features

### Modern Web Interface
- **Clean, responsive design** with professional YouTube-style video integration
- **Real-time search results** with live AI processing and video content
- **Interactive video player** with embedded YouTube videos
- **Navigation controls** for seamless video browsing (previous/next with looping)
- **Detailed video statistics** modal with comprehensive metrics
- **AI-powered intelligence reports** and definitions
- **Dictionary definitions** with pronunciations
- **Related image search** and video insights integration
- **Source credibility indicators** and bias warnings
- **Performance monitoring** and health checks

### YouTube Video Features
- **Real-Time Integration**: Authentic YouTube API v3 data with live statistics
- **Top 3 Videos**: Most-viewed videos for any search query
- **Interactive Player**: Full YouTube video embedding with controls
- **Navigation System**: Previous/Next buttons with seamless looping
- **Detailed Statistics**: Views, likes, comments, duration, published date, engagement rate
- **Sentiment Analysis**: Comment sentiment analysis with overall indicators
- **View Count Formatting**: Proper formatting for thousands (K), millions (M), billions (B)
- **Consistent Data**: Matching statistics between video tiles and detailed modals

### Available Data Sources
- **News**: BBC News, TechCrunch, Google News aggregation
- **Search Engines**: DuckDuckGo, Bing, Safari, Edge integration
- **Knowledge**: Wikipedia comprehensive coverage
- **Dictionary**: Word definitions, pronunciations, etymology
- **Social**: Hacker News community discussions
- **Video**: YouTube with real-time API integration and comprehensive metadata

### Analysis Capabilities
- **AI Intelligence Reports**: Multi-article analysis with LLM insights
- **Smart Article Summaries**: Individual content summarization
- **Video Content Analysis**: YouTube video statistics and sentiment analysis
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
├── app.py                          # Main Flask application with YouTube API integration
├── config/
│   └── .env                        # Environment variables (YouTube API key, etc.)
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
│   └── simple_search.html         # Modern web interface with YouTube integration
├── requirements.txt                # Python dependencies
└── README.md                      # This comprehensive guide
```

## API Endpoints

### Core Search API
- **`POST /api/search`**: Main search endpoint with AI analysis
- **`GET /api/sources`**: List available data sources
- **`GET /api/health`**: System health check
- **`GET /api/llm-health`**: LLM service health check

### YouTube Integration API
- **`POST /api/youtube-videos`**: Get top YouTube videos for a query
- **`POST /api/video-details`**: Get detailed video statistics and comments

### Content Analysis API
- **`POST /api/generate-summary`**: Generate AI summary for content
- **`POST /api/article-summary`**: Generate individual article summary
- **`POST /api/batch-article-summaries`**: Batch process multiple articles

### Visual Content API
- **`POST /api/image-search`**: Get related images for a query

## Example Results

### Search Query: "Taylor Swift"
```
Results Summary:
- Sources: 5+ active scrapers including YouTube
- Items Found: 40+ results with AI analysis
- YouTube Videos: Top 3 most-viewed Taylor Swift videos
- Processing Time: ~2-3 seconds (including AI processing)

YouTube Integration:
- Video 1: "Anti-Hero" - 1.2B views
- Video 2: "Shake It Off" - 3.2B views  
- Video 3: "Look What You Made Me Do" - 3.1B views
- Features: Interactive player, navigation controls, detailed stats

AI Analysis:
- Intelligence Report: Comprehensive multi-source analysis
- Article Summaries: 50-120 word intelligent summaries per article
- Video Sentiment: Positive engagement across all videos
- Credibility: High credibility from reliable entertainment sources
```

## Configuration Options

### Environment Variables
```bash
# YouTube API (Required)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Ollama LLM Configuration
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=llama3.1:8b
LLM_TIMEOUT=30
LLM_MAX_TOKENS=500
LLM_TEMPERATURE=0.7

# Application Settings
FLASK_ENV=development
DEBUG=True
```

### YouTube API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Add the API key to `config/.env`

### Model Options for LLM
- **llama3.1:8b** (Recommended): Best balance of speed and quality
- **llama3.1:70b**: Higher quality, requires more resources
- **mistral:7b**: Faster processing, good for high-volume
- **codellama:13b**: Specialized for technical content

## Performance & Hardware

### System Requirements

**Minimum Requirements:**
- 8GB RAM
- 4 CPU cores
- 10GB free disk space
- Stable internet connection
- YouTube Data API v3 key

**Recommended Requirements:**
- 16GB+ RAM
- 8+ CPU cores
- SSD storage
- High-speed internet
- Valid YouTube API quota

### Performance Metrics
- **Search Results**: Sub-second for basic queries
- **YouTube Integration**: 1-2 seconds for video data
- **AI Intelligence Reports**: 2-5 seconds per comprehensive analysis
- **Article Summaries**: 0.5-2 seconds per article
- **Video Statistics**: Instant loading from cached API data
- **Memory Usage**: 2-4GB during active AI processing

## Use Cases

1. **Entertainment Research**: Find top videos and comprehensive coverage of celebrities, movies, music
2. **Educational Content**: Discover most-viewed educational videos with detailed analysis
3. **Market Intelligence**: Real-time market analysis with video content insights
4. **News Aggregation**: Intelligent news synthesis with video reports and AI analysis
5. **Academic Research**: Multi-source literature review with video content integration
6. **Business Intelligence**: Competitive analysis with video marketing insights
7. **Content Discovery**: Find trending videos and comprehensive topic coverage

## Key Advantages

- **Real YouTube Integration**: Authentic video data with live statistics
- **AI-Powered**: Local LLM integration for intelligent analysis
- **Interactive Video Experience**: Seamless navigation and detailed statistics
- **Fast**: Sub-second processing for most queries, 1-2s for video integration
- **Intelligent**: Multi-dimensional analysis with AI integration
- **Comprehensive**: Multiple sources aggregated intelligently including video content
- **Accurate**: Credibility scoring and bias detection with real API data
- **Modern**: Clean, responsive web interface with YouTube-style video integration
- **Efficient**: Async processing and smart caching with API optimization
- **Private**: Local AI processing for data privacy
- **Extensible**: Modular architecture for easy enhancement

## Recent Updates

### YouTube Video Integration (Latest)
- **Real YouTube API Integration**: Authentic video data from YouTube Data API v3
- **Interactive Video Player**: Full YouTube video embedding with controls
- **Navigation Controls**: Previous/Next buttons with seamless looping
- **Detailed Video Statistics**: Comprehensive stats modal with real data
- **View Count Formatting**: Proper billions (B), millions (M), thousands (K) formatting
- **Published Date Display**: Real video publication dates in stats modal
- **Consistent Data**: Matching view counts between tiles and detailed stats
- **Sentiment Analysis**: Comment-based sentiment indicators

### UI/UX Improvements
- **Compact Stats Modal**: Matches article stats design with dotted separators
- **Working Close Buttons**: Fixed modal close functionality with proper event handling
- **Search Focus Styling**: Customizable search input focus border (currently dark gray)
- **Responsive Video Layout**: Professional YouTube-style video integration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Factryl** - Transforming search queries into intelligent insights with AI-powered analysis and real-time YouTube video integration!
