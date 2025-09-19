#!/usr/bin/env python3
"""
Comprehensive test script for all rate limiting functionality.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the worker directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

from worker.adapters.news_fetcher import GoogleSearchFetcher
from worker.adapters.x_poster import XAPIClient
from worker.celery_app import settings


def test_google_search_rate_limit_config():
    """Test that the Google Search rate limit is properly configured."""
    print("Testing Google Search rate limit configuration...")
    
    # Check that the setting is available in the worker settings
    if hasattr(settings, 'google_search_rate_limit'):
        print(f"✅ Google Search rate limit setting found: {settings.google_search_rate_limit}")
        return True
    else:
        print("❌ Google Search rate limit setting not found in worker settings")
        return False


def test_google_search_rate_limiting():
    """Test the Google Search API rate limiting functionality."""
    print("\nTesting Google Search API rate limiting...")
    
    # Create a Google Search fetcher instance
    fetcher = GoogleSearchFetcher()
    
    if not fetcher.is_available():
        print("Google Search API is not available. Check your API key and search engine ID.")
        return False
    
    # Check that the rate limiter is properly initialized
    if hasattr(fetcher, 'rate_limiter'):
        print(f"✅ Rate limiter initialized with {fetcher.rate_limiter.max_requests} requests per {fetcher.rate_limiter.time_window} seconds")
    else:
        print("❌ Rate limiter not found in GoogleSearchFetcher")
        return False
    
    # Test that the rate limiter is set to the correct values (90 requests per day)
    expected_max_requests = 90
    expected_time_window = 86400  # 24 hours in seconds
    
    if fetcher.rate_limiter.max_requests == expected_max_requests and fetcher.rate_limiter.time_window == expected_time_window:
        print(f"✅ Rate limiter configured correctly: {expected_max_requests} requests per {expected_time_window} seconds")
        return True
    else:
        print(f"❌ Rate limiter not configured correctly. Expected {expected_max_requests} requests per {expected_time_window} seconds, got {fetcher.rate_limiter.max_requests} requests per {fetcher.rate_limiter.time_window} seconds")
        return False


def test_environment_variables():
    """Test that the environment variables are properly set."""
    print("\nTesting environment variables...")
    
    google_search_rate_limit = os.getenv('GOOGLE_SEARCH_RATE_LIMIT')
    if google_search_rate_limit:
        print(f"✅ GOOGLE_SEARCH_RATE_LIMIT environment variable found: {google_search_rate_limit}")
        return True
    else:
        print("❌ GOOGLE_SEARCH_RATE_LIMIT environment variable not found")
        return False


def main():
    """Run all tests."""
    print("Running comprehensive rate limiting tests...\n")
    
    tests = [
        test_google_search_rate_limit_config,
        test_google_search_rate_limiting,
        test_environment_variables
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Rate limiting is properly implemented.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)