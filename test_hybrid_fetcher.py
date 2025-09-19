#!/usr/bin/env python3
"""
Test script for the hybrid news fetching approach.
This script demonstrates the hybrid approach with NewsAPI, Google Search API, and Playwright scraping.
"""

import sys
import os
import asyncio

# Add the worker directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

from worker.adapters.news_fetcher import NewsFetcher, GoogleSearchFetcher, PlaywrightScraper


def test_news_fetcher():
    """Test the NewsFetcher class with different configurations."""
    print("Testing NewsFetcher with mock mode...")
    
    # Test with mock mode
    fetcher = NewsFetcher(mock_mode=True)
    articles = fetcher.fetch_articles("technology", 3)
    print(f"Mock fetch returned {len(articles)} articles")
    
    # Test Google Search Fetcher availability
    google_fetcher = GoogleSearchFetcher()
    print(f"Google Search API available: {google_fetcher.is_available()}")
    
    print("Test completed successfully!")


async def test_playwright_scraper():
    """Test the Playwright scraper functionality."""
    print("Testing Playwright scraper...")
    
    # This would normally scrape a real URL, but we'll just show the functionality
    scraper = PlaywrightScraper()
    print("Playwright scraper initialized successfully")
    
    # In a real implementation, you would call:
    # article = await scraper.scrape_article("https://example.com/news-article")
    # print(f"Scraped article with {len(article.get('images', []))} images")
    
    print("Playwright test completed!")


if __name__ == "__main__":
    print("Testing hybrid news fetching approach...")
    test_news_fetcher()
    
    # Run async test
    asyncio.run(test_playwright_scraper())
    
    print("All tests completed!")