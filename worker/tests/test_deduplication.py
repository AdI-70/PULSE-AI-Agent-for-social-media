import os
import pytest
import sys
from unittest.mock import Mock, patch

# Add worker directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))

from utils.deduplication import DeduplicationService


class TestDeduplicationService:
    def test_generate_content_hash(self):
        """Test content hash generation."""
        # Mock database session
        mock_db = Mock()
        service = DeduplicationService(mock_db)
        
        article_data = {
            "title": "Test Article Title",
            "description": "Test article description"
        }
        
        hash1 = service.generate_content_hash(article_data)
        hash2 = service.generate_content_hash(article_data)
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length
    
    def test_different_content_different_hash(self):
        """Test that different content produces different hashes."""
        mock_db = Mock()
        service = DeduplicationService(mock_db)
        
        article1 = {"title": "Title 1", "description": "Description 1"}
        article2 = {"title": "Title 2", "description": "Description 2"}
        
        hash1 = service.generate_content_hash(article1)
        hash2 = service.generate_content_hash(article2)
        
        assert hash1 != hash2
    
    @patch('utils.deduplication.Article')
    def test_is_duplicate_by_url(self, mock_article_class):
        """Test duplicate detection by URL."""
        mock_db = Mock()
        
        # Mock existing article found by URL
        mock_existing_article = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_article
        
        service = DeduplicationService(mock_db)
        
        article_data = {
            "url": "https://example.com/existing-article",
            "title": "Test Title",
            "description": "Test Description"
        }
        
        result = service.is_duplicate(article_data)
        
        assert result is True
        # Should have checked for URL duplicate
        mock_db.query.assert_called()
    
    @patch('utils.deduplication.Article')
    def test_is_duplicate_by_content_hash(self, mock_article_class):
        """Test duplicate detection by content hash."""
        mock_db = Mock()
        
        # Mock no URL duplicate but content hash duplicate
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No URL duplicate
            Mock()  # Content hash duplicate found
        ]
        
        service = DeduplicationService(mock_db)
        
        article_data = {
            "url": "https://example.com/new-url",
            "title": "Same Title",
            "description": "Same Description"
        }
        
        result = service.is_duplicate(article_data)
        
        assert result is True
    
    @patch('utils.deduplication.Article')
    def test_is_not_duplicate(self, mock_article_class):
        """Test when article is not a duplicate."""
        mock_db = Mock()
        
        # Mock no duplicates found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        service = DeduplicationService(mock_db)
        
        article_data = {
            "url": "https://example.com/unique-article",
            "title": "Unique Title",
            "description": "Unique Description"
        }
        
        result = service.is_duplicate(article_data)
        
        assert result is False
    
    def test_empty_content_handling(self):
        """Test handling of empty content."""
        mock_db = Mock()
        service = DeduplicationService(mock_db)
        
        article_data = {
            "title": "",
            "description": ""
        }
        
        # Should not crash and should produce a hash
        hash_result = service.generate_content_hash(article_data)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64
    
    def test_missing_fields_handling(self):
        """Test handling of missing fields."""
        mock_db = Mock()
        service = DeduplicationService(mock_db)
        
        article_data = {}  # No title or description
        
        # Should not crash
        hash_result = service.generate_content_hash(article_data)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64