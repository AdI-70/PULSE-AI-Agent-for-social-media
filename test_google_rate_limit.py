#!/usr/bin/env python3
"""
Test script for Google Search API rate limiting.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the worker directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

from worker.adapters.news_fetcher import GoogleSearchFetcher


def test_google_rate_limiting():
    """Test the Google Search API rate limiting."""
    print("Testing Google Search API rate limiting...")
    
    # Create a Google Search fetcher instance
    fetcher = GoogleSearchFetcher()
    
    print(f"Fetcher is available: {fetcher.is_available()}")
    
    if not fetcher.is_available():
        print("Google Search API is not available. Check your API key and search engine ID.")
        return False
    
    # Test rate limiting by making multiple requests
    print("Making test requests...")
    
    try:
        # First request should succeed
        articles = fetcher.fetch_articles("technology", limit=2)
        print(f"First request successful. Found {len(articles)} articles.")
        
        # Check how many requests we can make before hitting the limit
        requests_made = 1
        while requests_made < 10:  # Limit test to 10 requests
            try:
                articles = fetcher.fetch_articles("technology", limit=2)
                requests_made += 1
                print(f"Request {requests_made} successful. Found {len(articles)} articles.")
            except Exception as e:
                print(f"Request {requests_made + 1} failed: {e}")
                break
        
        print(f"Made {requests_made} requests before hitting rate limit (if any).")
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return False


if __name__ == "__main__":
    success = test_google_rate_limiting()
    if success:
        print("\n✅ Google Search API rate limiting test completed!")
    else:
        print("\n❌ Google Search API rate limiting test failed!")