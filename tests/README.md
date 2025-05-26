# Factryl Tests

This directory contains the test suite for the Factryl project. The tests are organized into different categories and use pytest as the testing framework.

## Directory Structure

```
tests/
├── conftest.py           # Common test fixtures and configuration
├── integration/          # Integration tests
│   ├── test_news_scraper.py
│   ├── test_social_scraper.py
│   ├── test_reddit_scraper.py
│   ├── test_twitter_scraper.py
│   └── test_quora_scraper.py
└── unit/                # Unit tests
    ├── test_aggregator.py
    ├── test_engine.py
    ├── test_report.py
    ├── test_analyzer.py
    └── test_scraper.py
```

## Test Categories

1. **Unit Tests** (`tests/unit/`):
   - Tests for individual components in isolation
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration/`):
   - Tests multiple components working together
   - May interact with external services
   - Slower execution

## Running Tests

### Prerequisites
- Python 3.9 or higher
- Install test dependencies: `pip install -r requirements.txt`

### Running All Tests
```bash
pytest
```

### Running Specific Test Categories
```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run a specific test file
pytest tests/integration/test_news_scraper.py
```

### Test Configuration
- Common test fixtures are defined in `conftest.py`
- Environment variables can be set in `.env` file
- Mock responses and test data are stored in `tests/data/`

## Writing Tests

1. Use the appropriate test category (unit/integration)
2. Follow the existing test structure and naming conventions
3. Use fixtures from `conftest.py` when possible
4. Include docstrings explaining test purpose
5. Mock external services in unit tests

## Test Coverage
To generate a test coverage report:
```bash
pytest --cov=app tests/
``` 