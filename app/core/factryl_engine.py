"""
Factryl Engine - Core processing module for the Factryl system.
"""
from typing import List, Dict, Any, Optional
import asyncio
from loguru import logger

from ..scraper.plugin_loader import load_scrapers
from ..analyzer.relevance import RelevanceAnalyzer
from ..analyzer.sentiment import SentimentAnalyzer
from ..analyzer.credibility import CredibilityAnalyzer
from ..analyzer.clustering import ClusterAnalyzer
from ..analyzer.summarizer import TextSummarizer
from ..aggregator.aggregator import DataAggregator
from ..presenter.markdown_report import MarkdownReporter
from ..presenter.pdf_report import PDFReporter
from ..presenter.json_export import JSONExporter
from ..utils.logger import setup_logging
from ..utils.rate_limiter import RateLimiter

class FactrylEngine:
    """Main engine class that orchestrates the entire information processing pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Factryl engine.
        
        Args:
            config: Configuration dictionary from settings.yaml
        """
        self.config = config
        setup_logging(config['logging'])
        
        # Initialize components
        self.scrapers = load_scrapers()
        self.relevance_analyzer = RelevanceAnalyzer(config['analysis']['relevance'])
        self.sentiment_analyzer = SentimentAnalyzer(config['analysis']['sentiment'])
        self.credibility_analyzer = CredibilityAnalyzer(config['analysis']['credibility'])
        self.cluster_analyzer = ClusterAnalyzer(config['analysis']['clustering'])
        self.summarizer = TextSummarizer()
        self.aggregator = DataAggregator()
        
        # Initialize presenters
        self.presenters = {
            'markdown': MarkdownReporter(),
            'pdf': PDFReporter(),
            'json': JSONExporter()
        }
        
        # Rate limiting
        self.rate_limiters = {
            source: RateLimiter(rate=limit)
            for source, limit in config['scraping']['rate_limits'].items()
        }

    async def process_query(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        output_format: str = 'markdown'
    ) -> Dict[str, Any]:
        """
        Process a search query through the entire pipeline.
        
        Args:
            query: The search query string
            sources: List of sources to search (default: all available)
            output_format: Desired output format (markdown/pdf/json)
            
        Returns:
            Dictionary containing processed results and metadata
        """
        logger.info(f"Processing query: {query}")
        
        # Use all sources if none specified
        if sources is None:
            sources = list(self.scrapers.keys())
            
        # 1. Gather raw data
        raw_data = await self._gather_data(query, sources)
        
        # 2. Analyze content
        analyzed_data = await self._analyze_content(raw_data)
        
        # 3. Aggregate results
        aggregated_data = self.aggregator.aggregate(analyzed_data)
        
        # 4. Generate output
        if output_format not in self.presenters:
            raise ValueError(f"Unsupported output format: {output_format}")
            
        result = self.presenters[output_format].generate(
            query=query,
            data=aggregated_data,
            config=self.config['output']
        )
        
        logger.info("Query processing completed successfully")
        return result

    async def _gather_data(self, query: str, sources: List[str]) -> List[Dict[str, Any]]:
        """Gather data from all specified sources."""
        tasks = []
        for source in sources:
            if source not in self.scrapers:
                logger.warning(f"Unsupported source: {source}")
                continue
                
            scraper = self.scrapers[source]
            rate_limiter = self.rate_limiters.get(source)
            
            tasks.append(self._safe_scrape(scraper, query, rate_limiter))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and flatten results
        data = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scraping error: {result}")
                continue
            data.extend(result)
            
        return data

    async def _safe_scrape(self, scraper, query: str, rate_limiter: Optional[RateLimiter] = None):
        """Safely execute a scraping operation with rate limiting."""
        try:
            if rate_limiter:
                await rate_limiter.acquire()
            return await scraper.scrape(query)
        except Exception as e:
            logger.error(f"Error in scraper {scraper.__class__.__name__}: {e}")
            raise
        finally:
            if rate_limiter:
                rate_limiter.release()

    async def _analyze_content(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run all analysis steps on the gathered content."""
        for item in raw_data:
            try:
                # Add analysis results to each item
                item['relevance'] = await self.relevance_analyzer.analyze(item['content'])
                item['sentiment'] = await self.sentiment_analyzer.analyze(item['content'])
                item['credibility'] = await self.credibility_analyzer.analyze(item)
                
                # Generate summary
                item['summary'] = await self.summarizer.summarize(item['content'])
            except Exception as e:
                logger.error(f"Analysis error for item {item.get('id', 'unknown')}: {e}")
                
        # Perform clustering on the entire dataset
        clusters = await self.cluster_analyzer.cluster(raw_data)
        
        # Add cluster information to items
        for item in raw_data:
            item['cluster'] = next(
                (i for i, cluster in enumerate(clusters) if item['id'] in cluster),
                None
            )
            
        return raw_data 