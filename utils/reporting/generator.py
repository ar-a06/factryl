"""
Report generator module for creating beautiful HTML reports from scraped news data.

This module provides functionality to generate visually appealing and interactive HTML reports
that include charts, statistics, and organized article presentations.
"""

import os
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader

class ReportGenerator:
    """
    A class to generate beautiful HTML reports from news data.
    
    This class handles the transformation of raw news data into an organized,
    visually appealing HTML report with charts and interactive elements.
    """

    def __init__(self, template_dir: str = None):
        """
        Initialize the report generator.
        
        Args:
            template_dir: Directory containing HTML templates. If None, uses the default
                        templates directory in the reporting package.
        """
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template("report_template.html")

    def _process_news_data(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process raw news data into template-ready format.
        
        Args:
            news_data: List of news articles with their metadata
            
        Returns:
            Dict containing processed data ready for template rendering
        """
        categories = defaultdict(list)
        source_counts = defaultdict(int)
        credibility_scores = defaultdict(list)

        # Process news data
        for article in news_data:
            category = article.get("category", "Uncategorized")
            categories[category].append(article)
            source = article.get("source_detail", "Unknown")
            source_counts[source] += 1
            credibility_scores[source].append(
                article.get("credibility_info", {}).get("score", 0)
            )

        # Calculate statistics
        total_articles = len(news_data)
        source_labels = list(source_counts.keys())
        source_data = [source_counts[source] for source in source_labels]
        
        # Calculate average credibility per source
        credibility_data = [
            sum(credibility_scores[source]) / len(credibility_scores[source])
            if credibility_scores[source] else 0
            for source in source_labels
        ]

        # Calculate overall average credibility
        all_scores = [score for scores in credibility_scores.values() for score in scores]
        avg_credibility = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0

        return {
            "categories": dict(categories),
            "source_labels": source_labels,
            "source_data": source_data,
            "credibility_data": credibility_data,
            "total_articles": total_articles,
            "source_count": len(source_counts),
            "avg_credibility": avg_credibility
        }

    def generate_report(self, news_data: List[Dict[str, Any]], query: str, output_path: str) -> None:
        """
        Generate an HTML report from the news data.
        
        Args:
            news_data: List of news articles with their metadata
            query: The search query used to gather the news
            output_path: Path where the HTML report should be saved
        """
        # Process the news data
        template_data = self._process_news_data(news_data)
        
        # Add additional template data
        template_data.update({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query
        })

        # Generate HTML
        html_content = self.template.render(**template_data)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write the report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)


def generate_news_report(news_data: List[Dict[str, Any]], query: str, output_dir: str = "output/reports") -> str:
    """
    Convenience function to generate an HTML report from news data.
    
    Args:
        news_data: List of news articles with their metadata
        query: The search query used to gather the news
        output_dir: Directory to save the report
    
    Returns:
        str: Path to the generated report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"news_report_{timestamp}.html")
    
    generator = ReportGenerator()
    generator.generate_report(news_data, query, output_path)
    
    return output_path 