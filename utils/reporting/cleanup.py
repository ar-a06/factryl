"""
Cleanup utilities for managing report files.
"""

import os
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

def cleanup_old_reports(reports_dir: str, max_age_days: int = 7) -> Tuple[int, List[str]]:
    """
    Remove report files older than the specified age.
    
    Args:
        reports_dir: Directory containing report files
        max_age_days: Maximum age of reports in days
        
    Returns:
        Tuple containing:
            - Number of files deleted
            - List of deleted file paths
    """
    if not os.path.exists(reports_dir):
        return 0, []
        
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    deleted_files = []
    
    # Find all HTML report files
    report_files = glob.glob(os.path.join(reports_dir, "news_report_*.html"))
    
    for file_path in report_files:
        try:
            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Delete if older than cutoff
            if mod_time < cutoff_date:
                os.remove(file_path)
                deleted_files.append(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
            
    return len(deleted_files), deleted_files

def get_report_stats(reports_dir: str) -> Dict[str, int]:
    """
    Get statistics about report files.
    
    Args:
        reports_dir: Directory containing report files
        
    Returns:
        Dictionary containing:
            - total_reports: Total number of report files
            - total_size_mb: Total size of reports in MB
            - oldest_days: Age of oldest report in days
    """
    if not os.path.exists(reports_dir):
        return {
            'total_reports': 0,
            'total_size_mb': 0,
            'oldest_days': 0
        }
        
    report_files = glob.glob(os.path.join(reports_dir, "news_report_*.html"))
    
    if not report_files:
        return {
            'total_reports': 0,
            'total_size_mb': 0,
            'oldest_days': 0
        }
        
    total_size = 0
    oldest_timestamp = datetime.now().timestamp()
    
    for file_path in report_files:
        try:
            # Get file size
            total_size += os.path.getsize(file_path)
            
            # Update oldest timestamp
            mod_time = os.path.getmtime(file_path)
            oldest_timestamp = min(oldest_timestamp, mod_time)
        except Exception:
            continue
            
    oldest_days = (datetime.now() - datetime.fromtimestamp(oldest_timestamp)).days
    
    return {
        'total_reports': len(report_files),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'oldest_days': oldest_days
    } 