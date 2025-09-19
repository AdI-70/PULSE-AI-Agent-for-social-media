#!/usr/bin/env python3
"""
Script to diagnose Google Custom Search API issues
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_vars():
    """Check if required environment variables are set."""
    print("Checking environment variables...")
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    print(f"GOOGLE_API_KEY loaded: {google_api_key is not None}")
    if google_api_key:
        print(f"API Key (last 5 chars): ...{google_api_key[-5:]}")
    
    print(f"GOOGLE_SEARCH_ENGINE_ID loaded: {search_engine_id is not None}")
    if search_engine_id:
        print(f"Search Engine ID: {search_engine_id}")
    
    return google_api_key, search_engine_id

def test_api_key_validity(api_key):
    """Test if the API key is valid by checking API key info."""
    print("\nTesting API key validity...")
    
    # This endpoint checks if the API key is valid
    url = f"https://content-customsearch.googleapis.com/v1/keyCheck?key={api_key}"
    
    try:
        response = requests.get(url)
        print(f"API Key check status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key appears to be valid")
            return True
        else:
            print(f"❌ API key check failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API key check failed with exception: {e}")
        return False

def test_cse_configuration(api_key, search_engine_id):
    """Test if the Custom Search Engine is properly configured."""
    print("\nTesting Custom Search Engine configuration...")
    
    # Try to get information about the search engine
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": "test",
        "num": 1
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"CSE configuration test status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Custom Search Engine appears to be properly configured")
            return True
        else:
            print(f"❌ CSE configuration test failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
            return False
    except Exception as e:
        print(f"❌ CSE configuration test failed with exception: {e}")
        return False

def check_api_restrictions(api_key):
    """Check if there are API restrictions on the key."""
    print("\nChecking for API restrictions...")
    print("This requires accessing Google Cloud Console, which we can't do programmatically.")
    print("Please manually check:")
    print("1. Go to Google Cloud Console > APIs & Services > Credentials")
    print("2. Find your API key")
    print("3. Check 'API restrictions' section")
    print("4. Ensure 'Custom Search API' is enabled or set to 'Don't restrict key'")
    
def main():
    print("Google Custom Search API Diagnosis Tool")
    print("=" * 40)
    
    # Check environment variables
    api_key, search_engine_id = check_env_vars()
    
    if not api_key or not search_engine_id:
        print("\n❌ Missing required environment variables")
        return
    
    # Test API key validity
    key_valid = test_api_key_validity(api_key)
    
    # Test CSE configuration
    cse_valid = test_cse_configuration(api_key, search_engine_id)
    
    # Check for API restrictions
    check_api_restrictions(api_key)
    
    print("\n" + "=" * 40)
    if key_valid and cse_valid:
        print("✅ All checks passed! Google Search API should work.")
    else:
        print("❌ Issues detected. Please address the issues above.")

if __name__ == "__main__":
    main()