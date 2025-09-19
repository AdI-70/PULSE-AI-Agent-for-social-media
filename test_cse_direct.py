#!/usr/bin/env python3
"""
Direct test of Google Custom Search Engine.
This script tests if we can access the CSE directly.
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_cse_direct():
    """Test direct access to Google Custom Search Engine."""
    print("Testing direct access to Google Custom Search Engine...")
    
    # Get the credentials
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    print(f"GOOGLE_API_KEY loaded: {google_api_key is not None}")
    print(f"GOOGLE_SEARCH_ENGINE_ID loaded: {google_search_engine_id is not None}")
    
    if not google_api_key or not google_search_engine_id:
        print("ERROR: Missing Google API credentials!")
        return False
    
    # Test a simple search query directly on the CSE
    query = "technology news"
    
    # Build the URL for the CSE
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_search_engine_id,
        "q": query,
        "num": 3
    }
    
    print(f"Making request to: {base_url}")
    print(f"Query: {query}")
    print(f"API Key: {google_api_key[:10]}...{google_api_key[-5:]}")
    print(f"CSE ID: {google_search_engine_id}")
    
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
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response content: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to make request: {e}")
        return False


def test_cse_status():
    """Test the status of the Custom Search API."""
    print("\nTesting Custom Search API status...")
    
    google_api_key = os.getenv('GOOGLE_API_KEY')
    
    # Check API key info
    api_key_url = f"https://content-api.googleapis.com/v1/apiKeys?key={google_api_key}"
    
    try:
        response = requests.get(api_key_url, timeout=30)
        print(f"API Key info status: {response.status_code}")
        if response.status_code == 200:
            print("API Key is valid")
        else:
            print("API Key may be invalid or restricted")
    except Exception as e:
        print(f"Could not check API key status: {e}")


if __name__ == "__main__":
    success = test_cse_direct()
    test_cse_status()
    
    if success:
        print("\n✅ Google Custom Search Engine is working!")
    else:
        print("\n❌ Google Custom Search Engine has issues.")
        print("\nPossible solutions:")
        print("1. Verify that the Custom Search API is enabled in your Google Cloud project")
        print("2. Check that your API key has permissions for the Custom Search API")
        print("3. Make sure your Custom Search Engine is properly configured")
        print("4. Wait a few more minutes for changes to propagate")