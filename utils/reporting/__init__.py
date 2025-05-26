"""
Reporting module for generating beautiful HTML reports from scraped data.
"""

from .generator import generate_news_report
from .utilities import cleanup_old_reports, get_report_stats

__all__ = ['generate_news_report', 'cleanup_old_reports', 'get_report_stats'] 