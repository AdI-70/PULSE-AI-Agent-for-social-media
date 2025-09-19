#!/usr/bin/env python3
"""
Simple test script for Google Search API integration.
This script tests the basic Google Search API functionality.
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_simple_google_search():
    """Test the basic Google Search API functionality."""
    print("Testing basic Google Search API functionality...")
    
    # Get the credentials
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    print(f"GOOGLE_API_KEY loaded: {google_api_key is not None}")
    print(f"GOOGLE_SEARCH_ENGINE_ID loaded: {google_search_engine_id is not None}")
    
    if not google_api_key or not google_search_engine_id:
        print("ERROR: Missing Google API credentials!")
        return False
    
    # Simple search query
    query = "technology news"
    
    # Build the URL
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_search_engine_id,
        "q": query,
        "num": 3
    }
    
    print(f"Making request to: {base_url}")
    print(f"Query: {query}")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response received successfully!")
            print(f"Total results: {data.get('searchInformation', {}).get('totalResults', 'N/A')}")
            
            items = data.get("items", [])
            print(f"Found {len(items)} items")
            
            for i, item in enumerate(items, 1):
                print(f"\nItem {i}:")
                print(f"  Title: {item.get('title', 'N/A')}")
                print(f"  URL: {item.get('link', 'N/A')}")
                print(f"  Snippet: {item.get('snippet', 'N/A')[:100]}...")
            
            return True
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response content: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to make request: {e}")
        return False


if __name__ == "__main__":
    success = test_simple_google_search()
    if success:
        print("\n✅ Basic Google Search API functionality is working!")
    else:
        print("\n❌ Basic Google Search API functionality has issues.")