# Hybrid News Fetching Approach

The Pulse system implements a hybrid news fetching approach that combines multiple sources for maximum reliability and content richness.

## Approach Overview

The system uses the following hierarchy for news fetching:

1. **Google Search API** (Primary fallback) - Uses Google's Custom Search API to find relevant news articles
2. **NewsAPI** (Secondary fallback) - Traditional news API for structured news content
3. **Playwright Scraping** (Final fallback) - Browser-based scraping with image downloading
4. **Mock Data** (Development only) - Simulated data for testing

## Configuration

To use the hybrid approach, configure the following environment variables in your `.env` file:

```env
# Google Search API (recommended as primary fallback)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# NewsAPI (traditional fallback)
NEWSAPI_KEY=your_newsapi_key_here

# For development/testing
MOCK_NEWS_ARTICLES=false
```

## Google Search API Setup

1. Create a Google Cloud Project and enable the Custom Search API
2. Create a Custom Search Engine at https://cse.google.com/
3. Add your API key and Search Engine ID to the configuration

## Image Downloading

The Playwright scraper now includes image downloading capabilities:

- Downloads up to 5 relevant images per article
- Filters images by size (max 5MB)
- Stores both image URLs and binary data
- Preserves alt text for accessibility

## Usage

The system automatically uses the best available method based on your configuration. The hybrid approach ensures:

- **Reliability**: Multiple fallback options
- **Rich Content**: Images included with articles
- **Performance**: API calls are faster than scraping
- **Flexibility**: Works with or without API keys

## Testing

Run the test script to verify the implementation:

```bash
python test_hybrid_fetcher.py
```