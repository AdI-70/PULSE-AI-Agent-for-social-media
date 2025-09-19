import pytest
from unittest.mock import Mock, patch
import os
import sys

# Add worker directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from adapters.news_fetcher import NewsAPIFetcher, MockNewsFetcher, NewsFetcher


class TestMockNewsFetcher:
    def test_is_available(self):
        fetcher = MockNewsFetcher()
        assert fetcher.is_available() is True
    
    def test_fetch_articles(self):
        fetcher = MockNewsFetcher()
        
        articles = fetcher.fetch_articles("technology", limit=3)
        
        assert isinstance(articles, list)
        assert len(articles) <= 3
        assert len(articles) > 0
        
        # Check article structure
        for article in articles:
            assert "title" in article
            assert "url" in article
            assert "source" in article
            assert "publishedAt" in article
    
    def test_niche_filtering(self):
        fetcher = MockNewsFetcher()
        
        tech_articles = fetcher.fetch_articles("technology", limit=5)
        ai_articles = fetcher.fetch_articles("artificial intelligence", limit=5)
        
        # Should return different articles for different niches
        tech_urls = [a["url"] for a in tech_articles]
        ai_urls = [a["url"] for a in ai_articles]
        
        # URLs should be different due to niche-specific filtering
        assert tech_urls != ai_urls
    
    def test_limit_respected(self):
        fetcher = MockNewsFetcher()
        
        articles = fetcher.fetch_articles("business", limit=2)
        
        assert len(articles) <= 2


class TestNewsAPIFetcher:
    def test_is_available_without_key(self):
        fetcher = NewsAPIFetcher(api_key=None)
        assert fetcher.is_available() is False
    
    def test_is_available_with_key(self):
        fetcher = NewsAPIFetcher(api_key="test-key")
        assert fetcher.is_available() is True
    
    @patch('adapters.news_fetcher.requests.get')
    def test_fetch_articles_success(self, mock_get):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 100,
            "articles": [
                {
                    "title": "Test Article 1",
                    "description": "Test description 1",
                    "url": "https://example.com/1",
                    "source": {"name": "Test Source"},
                    "author": "Test Author",
                    "publishedAt": "2024-01-01T00:00:00Z"
                },
                {
                    "title": "Test Article 2",
                    "description": "Test description 2",
                    "url": "https://example.com/2",
                    "source": {"name": "Test Source 2"},
                    "author": "Test Author 2",
                    "publishedAt": "2024-01-01T01:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        fetcher = NewsAPIFetcher(api_key="test-key")
        articles = fetcher.fetch_articles("technology", limit=5)
        
        assert len(articles) == 2
        assert articles[0]["title"] == "Test Article 1"
        assert articles[1]["title"] == "Test Article 2"
        
        # Check API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "everything" in call_args[0][0]
    
    @patch('adapters.news_fetcher.requests.get')
    def test_fetch_articles_filters_removed(self, mock_get):
        # Mock API response with [Removed] articles
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "[Removed]",
                    "url": "https://example.com/removed",
                    "source": {"name": "Test Source"}
                },
                {
                    "title": "Valid Article",
                    "url": "https://example.com/valid",
                    "source": {"name": "Test Source"}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        fetcher = NewsAPIFetcher(api_key="test-key")
        articles = fetcher.fetch_articles("technology", limit=5)
        
        # Should only return valid articles
        assert len(articles) == 1
        assert articles[0]["title"] == "Valid Article"
    
    def test_fetch_articles_without_key(self):
        fetcher = NewsAPIFetcher(api_key=None)
        
        with pytest.raises(Exception, match="NewsAPI key not available"):
            fetcher.fetch_articles("technology", limit=5)


class TestNewsFetcher:
    def test_mock_mode(self):
        fetcher = NewsFetcher(mock_mode=True)
        
        articles = fetcher.fetch_articles("technology", limit=3)
        
        assert isinstance(articles, list)
        assert len(articles) > 0
        assert len(articles) <= 3
    
    @patch('adapters.news_fetcher.NewsAPIFetcher')
    def test_newsapi_priority(self, mock_newsapi_class):
        # Mock NewsAPI to be available and working
        mock_newsapi = Mock()
        mock_newsapi.is_available.return_value = True
        mock_newsapi.fetch_articles.return_value = [{"title": "NewsAPI Article"}]
        mock_newsapi_class.return_value = mock_newsapi
        
        fetcher = NewsFetcher(mock_mode=False)
        articles = fetcher.fetch_articles("technology", limit=5)
        
        # Should use NewsAPI if available
        mock_newsapi.fetch_articles.assert_called_once_with("technology", 5)
        assert articles == [{"title": "NewsAPI Article"}]
    
    @patch('adapters.news_fetcher.NewsAPIFetcher')
    def test_fallback_to_mock(self, mock_newsapi_class):
        # Mock NewsAPI to be unavailable
        mock_newsapi = Mock()
        mock_newsapi.is_available.return_value = False
        mock_newsapi_class.return_value = mock_newsapi
        
        fetcher = NewsFetcher(mock_mode=False)
        articles = fetcher.fetch_articles("technology", limit=3)
        
        # Should fallback to mock
        assert isinstance(articles, list)
        assert len(articles) > 0
        # Mock should not be called since it's not available
        mock_newsapi.fetch_articles.assert_not_called()