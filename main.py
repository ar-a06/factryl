#!/usr/bin/env python3
"""
Factryl - Main Entry Point

This script serves as the main entry point for the Factryl application,
providing a unified interface to launch different interfaces (CLI, API, or Web).
"""

import os
import sys
import argparse
import yaml
from dotenv import load_dotenv
from loguru import logger

def load_config():
    """Load configuration from settings.yaml."""
    config_path = os.path.join('config', 'settings.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Factryl - Information Analysis System")
    parser.add_argument(
        '--interface',
        choices=['cli', 'api', 'web'],
        default='cli',
        help='Interface to launch (default: cli)'
    )
    parser.add_argument(
        '--config',
        default='config/settings.yaml',
        help='Path to configuration file'
    )
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Launch appropriate interface
    if args.interface == 'cli':
        from app.interface.cli.main_cli import run_cli
        run_cli(config)
    elif args.interface == 'api':
        from app.interface.api.main_api import run_api
        run_api(config)
    else:  # web interface
        logger.error("Web interface not implemented yet")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1) 