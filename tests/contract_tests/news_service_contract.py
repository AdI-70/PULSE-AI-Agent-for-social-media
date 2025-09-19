"""
Contract tests for Pulse News Service using Pact
"""

import pytest
from pact import Consumer, Provider
import requests
import json

# Define the pact between consumer and provider
pact = Consumer('PulseWorker').has_pact_with(Provider('NewsService'))

# Test data
EXPECTED_ARTICLE_STRUCTURE = {
    "articles": [
        {
            "id": 123,
            "title": "Sample Article Title",
            "description": "This is a sample article description",
            "content": "Full article content would go here...",
            "url": "https://example.com/article/123",
            "source": {"name": "Example News"},
            "author": "John Doe",
            "publishedAt": "2024-01-01T10:00:00Z"
        }
    ]
}


def test_fetch_articles_contract():
    """Test contract for fetching articles by niche."""
    expected = {
        "articles": [
            {
                "id": 123,
                "title": "Sample Article Title",
                "description": "This is a sample article description",
                "content": "Full article content would go here...",
                "url": "https://example.com/article/123",
                "source": {"name": "Example News"},
                "author": "John Doe",
                "publishedAt": "2024-01-01T10:00:00Z"
            }
        ]
    }
    
    (pact
     .given('Articles exist for technology niche')
     .upon_receiving('a request for tech articles')
     .with_request('GET', '/articles/technology')
     .will_respond_with(200, body=expected))
    
    with pact:
        response = requests.get(f"{pact.uri}/articles/technology")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert len(data["articles"]) > 0
        assert "title" in data["articles"][0]


def test_fetch_articles_with_limit_contract():
    """Test contract for fetching articles with limit parameter."""
    expected = {
        "articles": [
            {
                "id": 123,
                "title": "Sample Article Title",
                "description": "This is a sample article description",
                "content": "Full article content would go here...",
                "url": "https://example.com/article/123",
                "source": {"name": "Example News"},
                "author": "John Doe",
                "publishedAt": "2024-01-01T10:00:00Z"
            }
        ]
    }
    
    (pact
     .given('Articles exist for technology niche')
     .upon_receiving('a request for tech articles with limit')
     .with_request('GET', '/articles/technology', query={'limit': '5'})
     .will_respond_with(200, body=expected))
    
    with pact:
        response = requests.get(f"{pact.uri}/articles/technology", params={'limit': 5})
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert len(data["articles"]) <= 5


def test_fetch_articles_error_contract():
    """Test contract for error response when no articles found."""
    (pact
     .given('No articles exist for invalid niche')
     .upon_receiving('a request for invalid niche articles')
     .with_request('GET', '/articles/invalid_niche')
     .will_respond_with(404, body={"error": "No articles found for niche: invalid_niche"}))
    
    with pact:
        response = requests.get(f"{pact.uri}/articles/invalid_niche")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])