#!/usr/bin/env python3
"""
Debug script for Google Search Fetcher
"""

import os
import sys
from dotenv import load_dotenv

# Add the worker directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker'))

# Load environment variables
load_dotenv()

def debug_google_fetcher():
    """Debug the Google Search Fetcher."""
    print("Debugging Google Search Fetcher...")
    
    # Print environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    print(f"GOOGLE_API_KEY: {google_api_key}")
    print(f"GOOGLE_SEARCH_ENGINE_ID: {search_engine_id}")
    
    # Import and test the fetcher
    from worker.adapters.news_fetcher import GoogleSearchFetcher
    
    fetcher = GoogleSearchFetcher()
    print(f"Fetcher API key: {fetcher.api_key}")
    print(f"Fetcher search engine ID: {fetcher.search_engine_id}")
    print(f"Fetcher is available: {fetcher.is_available()}")
    
    # Test with explicit parameters
    if google_api_key and search_engine_id:
        fetcher2 = GoogleSearchFetcher(google_api_key, search_engine_id)
        print(f"Fetcher2 API key: {fetcher2.api_key}")
        print(f"Fetcher2 search engine ID: {fetcher2.search_engine_id}")
        print(f"Fetcher2 is available: {fetcher2.is_available()}")

if __name__ == "__main__":
    debug_google_fetcher()