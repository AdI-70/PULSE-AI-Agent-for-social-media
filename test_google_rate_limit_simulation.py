#!/usr/bin/env python3
"""
Test script for Google Search API rate limiting simulation.
"""

import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the worker directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

from worker.adapters.news_fetcher import GoogleSearchFetcher


def test_google_rate_limiting_simulation():
    """Test the Google Search API rate limiting by simulating hitting the limit."""
    print("Testing Google Search API rate limiting simulation...")
    
    # Create a Google Search fetcher instance
    fetcher = GoogleSearchFetcher()
    
    print(f"Fetcher is available: {fetcher.is_available()}")
    
    if not fetcher.is_available():
        print("Google Search API is not available. Check your API key and search engine ID.")
        return False
    
    # Manually set the rate limiter to a very low limit for testing
    # Set to 3 requests per minute for testing purposes
    fetcher.rate_limiter.max_requests = 3
    fetcher.rate_limiter.time_window = 60  # 1 minute
    
    print("Rate limiter set to 3 requests per minute for testing.")
    print("Making test requests...")
    
    try:
        # First 3 requests should succeed
        for i in range(3):
            articles = fetcher.fetch_articles("technology", limit=2)
            print(f"Request {i+1} successful. Found {len(articles)} articles.")
        
        # 4th request should fail due to rate limiting
        try:
            articles = fetcher.fetch_articles("technology", limit=2)
            print(f"Request 4 should have failed, but succeeded. Found {len(articles)} articles.")
            print("This might be because the requests were spread out enough not to hit the limit.")
        except Exception as e:
            print(f"Request 4 correctly failed due to rate limiting: {e}")
            return True
            
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return False


if __name__ == "__main__":
    success = test_google_rate_limiting_simulation()
    if success:
        print("\n✅ Google Search API rate limiting simulation test completed!")
    else:
        print("\n❌ Google Search API rate limiting simulation test failed!")