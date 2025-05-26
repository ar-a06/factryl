"""
Unit tests for report generation functionality.
"""

import pytest
import os
from datetime import datetime, timedelta
from utils.reporting import generate_news_report, cleanup_old_reports, get_report_stats

@pytest.fixture
def sample_news_data():
    """Fixture providing sample news data for testing."""
    return [
        {
            "title": "Major Scientific Breakthrough in Quantum Computing",
            "source_detail": "Science Daily",
            "author": "Dr. Jane Smith",
            "url": "https://example.com/quantum-breakthrough",
            "category": "Science & Technology",
            "credibility_info": {
                "score": 95,
                "bias": "least"
            },
            "metadata": {
                "preview": "Scientists have achieved a major breakthrough in quantum computing..."
            }
        },
        {
            "title": "Global Markets React to Economic Policy Changes",
            "source_detail": "Financial Times",
            "author": "John Anderson",
            "url": "https://example.com/market-reaction",
            "category": "Business & Finance",
            "credibility_info": {
                "score": 92,
                "bias": "center"
            },
            "metadata": {
                "preview": "Global markets showed significant volatility today..."
            }
        }
    ]

@pytest.fixture
def test_output_dir(tmp_path):
    """Fixture providing a temporary directory for test outputs."""
    return tmp_path / "test_reports"

def test_generate_report(sample_news_data, test_output_dir):
    """Test report generation with sample data."""
    report_path = generate_news_report(
        news_data=sample_news_data,
        query="Test Query",
        output_dir=str(test_output_dir)
    )
    
    assert os.path.exists(report_path), "Report file should exist"
    assert report_path.endswith('.html'), "Report should be HTML format"
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Major Scientific Breakthrough" in content, "Report should contain article title"
        assert "Science Daily" in content, "Report should contain source"
        assert "Dr. Jane Smith" in content, "Report should contain author"

def test_cleanup_old_reports(test_output_dir):
    """Test cleanup of old reports."""
    # Create some test reports with different dates
    current_time = datetime.now()
    
    # Create reports with different dates
    dates = [
        current_time - timedelta(days=10),  # Old report
        current_time - timedelta(days=5),   # Recent report
        current_time                        # New report
    ]
    
    created_files = []
    for i, date in enumerate(dates):
        file_path = os.path.join(test_output_dir, f"report_{i}.html")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(f"Test report {i}")
        os.utime(file_path, (date.timestamp(), date.timestamp()))
        created_files.append(file_path)
    
    # Clean up reports older than 7 days
    deleted_count, deleted_files = cleanup_old_reports(max_age_days=7, reports_dir=str(test_output_dir))
    
    assert deleted_count == 1, "Should delete one old report"
    assert os.path.basename(deleted_files[0]) == "report_0.html", "Should delete the oldest report"
    assert not os.path.exists(created_files[0]), "Old report should be deleted"
    assert os.path.exists(created_files[1]), "Recent report should remain"
    assert os.path.exists(created_files[2]), "New report should remain"

def test_get_report_stats(test_output_dir, sample_news_data):
    """Test report statistics calculation."""
    # Generate a few reports
    for i in range(3):
        generate_news_report(
            news_data=sample_news_data,
            query=f"Test Query {i}",
            output_dir=str(test_output_dir)
        )
    
    stats = get_report_stats(reports_dir=str(test_output_dir))
    
    assert stats['total_reports'] == 3, "Should count all generated reports"
    assert isinstance(stats['oldest_report'], datetime), "Should identify oldest report time"
    assert isinstance(stats['newest_report'], datetime), "Should identify newest report time"
    assert stats['size_bytes'] > 0, "Should calculate total size"

def test_empty_report_generation(test_output_dir):
    """Test report generation with empty data."""
    report_path = generate_news_report(
        news_data=[],
        query="Empty Query",
        output_dir=str(test_output_dir)
    )
    
    assert os.path.exists(report_path), "Report should be generated even with empty data"
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "No results found" in content, "Report should indicate no results" 