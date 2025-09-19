#!/usr/bin/env python3
"""
Final test for Google Search API integration
"""

import os
import sys
from dotenv import load_dotenv

# Add the worker directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker'))

# Load environment variables
load_dotenv()

def test_google_search_api():
    """Test the Google Search API integration."""
    print("Testing Google Search API integration...")
    
    # Import and test the fetcher
    from worker.adapters.news_fetcher import GoogleSearchFetcher
    
    fetcher = GoogleSearchFetcher()
    print(f"Google Search Fetcher available: {fetcher.is_available()}")
    
    if not fetcher.is_available():
        print("❌ Google Search Fetcher is not available")
        return
    
    try:
        print("Attempting to fetch articles about 'technology'...")
        articles = fetcher.fetch_articles("technology", 3)
        print(f"✅ Successfully fetched {len(articles)} articles")
        for i, article in enumerate(articles):
            print(f"  {i+1}. {article['title']}")
            print(f"     URL: {article['url']}")
            print(f"     Source: {article['source']['name']}")
            print()
    except Exception as e:
        print(f"❌ Failed to fetch articles: {e}")
        print("This is expected if the API key doesn't have proper permissions.")
        print("Please follow the instructions in GOOGLE_API_FIX_INSTRUCTIONS.md")

if __name__ == "__main__":
    test_google_search_api()