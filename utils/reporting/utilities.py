"""
Utility functions for report management and statistics.
"""

import os
import glob
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any


def cleanup_old_reports(max_age_days: int = 7, reports_dir: str = "output/reports") -> Tuple[int, List[str]]:
    """
    Clean up old report files.
    
    Args:
        max_age_days: Maximum age of reports to keep (in days)
        reports_dir: Directory containing report files
        
    Returns:
        Tuple of (deleted_count, deleted_files)
    """
    if not os.path.exists(reports_dir):
        return 0, []
    
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    deleted_files = []
    deleted_count = 0
    
    # Find all HTML files in the reports directory
    pattern = os.path.join(reports_dir, "*.html")
    for file_path in glob.glob(pattern, recursive=False):
        try:
            # Get file modification time
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Delete if older than cutoff
            if file_time < cutoff_time:
                os.remove(file_path)
                deleted_files.append(file_path)
                deleted_count += 1
        except (OSError, IOError):
            # Skip files that can't be accessed
            continue
    
    return deleted_count, deleted_files


def get_report_stats(reports_dir: str = "output/reports") -> Dict[str, Any]:
    """
    Get statistics about generated reports.
    
    Args:
        reports_dir: Directory containing report files
        
    Returns:
        Dictionary with report statistics
    """
    if not os.path.exists(reports_dir):
        return {
            'total_reports': 0,
            'oldest_report': None,
            'newest_report': None,
            'size_bytes': 0
        }
    
    # Find all HTML files
    pattern = os.path.join(reports_dir, "*.html")
    files = glob.glob(pattern, recursive=False)  # Don't search recursively to avoid duplicate counting
    
    if not files:
        return {
            'total_reports': 0,
            'oldest_report': None,
            'newest_report': None,
            'size_bytes': 0
        }
    
    total_size = 0
    oldest_time = None
    newest_time = None
    
    for file_path in files:
        try:
            # Get file stats
            stat = os.stat(file_path)
            file_time = datetime.fromtimestamp(stat.st_mtime)
            file_size = stat.st_size
            
            total_size += file_size
            
            # Track oldest and newest
            if oldest_time is None or file_time < oldest_time:
                oldest_time = file_time
            if newest_time is None or file_time > newest_time:
                newest_time = file_time
                
        except (OSError, IOError):
            # Skip files that can't be accessed
            continue
    
    return {
        'total_reports': len(files),
        'oldest_report': oldest_time,
        'newest_report': newest_time,
        'size_bytes': total_size
    } 