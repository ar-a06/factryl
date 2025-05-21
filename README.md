# Factryl

Factryl is a comprehensive information analysis system that scrapes, analyzes, and aggregates factual information from various online sources.

## Features

- Multi-source data scraping (News, Reddit, Twitter, Quora, YouTube, Blogs)
- Advanced text analysis (relevance, sentiment, credibility)
- Content clustering and summarization
- Multiple output formats (CLI, API, Web interface)
- Extensible plugin system for custom scrapers

## Project Structure

```
factryl/
├── app/
│   ├── core/           # Core engine and business logic
│   ├── scraper/        # Data collection from various sources
│   ├── analyzer/       # Text analysis and processing
│   ├── aggregator/     # Data aggregation and combination
│   ├── presenter/      # Output formatting and presentation
│   └── interface/      # User interfaces (CLI, API, Web)
├── data/               # Data storage
├── config/            # Configuration files
├── tests/             # Unit and integration tests
└── utils/             # Utility functions and helpers
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/factryl.git
cd factryl
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp config/secrets.env.example config/secrets.env
# Edit config/secrets.env with your API keys
```

## Usage

### CLI Interface
```bash
python -m app.interface.cli.main_cli --source news --query "your search query"
```

### API Server
```bash
uvicorn app.interface.api.main_api:app --reload
```

### Running Tests
```bash
pytest tests/
```

## Configuration

- `config/settings.yaml`: General application settings
- `config/secrets.env`: API keys and sensitive credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 