#!/usr/bin/env python3
"""
Test script for Google Search API integration.
This script tests the Google Search API with your provided credentials.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the worker directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

from worker.adapters.news_fetcher import GoogleSearchFetcher


def test_google_search_api():
    """Test the Google Search API integration."""
    print("Testing Google Search API integration...")
    
    # Print the loaded environment variables for debugging
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    print(f"GOOGLE_API_KEY loaded: {google_api_key is not None}")
    print(f"GOOGLE_SEARCH_ENGINE_ID loaded: {google_search_engine_id is not None}")
    
    if google_api_key:
        print("Google API Key: ***" + google_api_key[-5:])  # Show last 5 characters for verification
    if google_search_engine_id:
        print(f"Google Search Engine ID: {google_search_engine_id}")
    
    # Create a Google Search fetcher instance with explicit credentials
    fetcher = GoogleSearchFetcher(
        api_key=google_api_key,
        search_engine_id=google_search_engine_id
    )
    
    # Check if the API is available
    is_available = fetcher.is_available()
    print(f"Google Search API available: {is_available}")
    
    if not is_available:
        print("ERROR: Google Search API is not properly configured!")
        print("Please check your GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID in the .env file")
        return False
    
    try:
        # Test fetching articles for a sample niche
        print("Fetching sample articles about 'technology'...")
        articles = fetcher.fetch_articles("technology", 3)
        
        print(f"Successfully fetched {len(articles)} articles")
        
        # Display information about the fetched articles
        for i, article in enumerate(articles, 1):
            print(f"\nArticle {i}:")
            print(f"  Title: {article.get('title', 'N/A')}")
            print(f"  URL: {article.get('url', 'N/A')}")
            print(f"  Source: {article.get('source', {}).get('name', 'N/A')}")
            print(f"  Description: {article.get('description', 'N/A')[:100]}...")
            
        print("\nGoogle Search API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to fetch articles from Google Search API: {e}")
        return False


if __name__ == "__main__":
    success = test_google_search_api()
    if success:
        print("\n✅ Google Search API integration is working correctly!")
    else:
        print("\n❌ Google Search API integration has issues that need to be addressed.")