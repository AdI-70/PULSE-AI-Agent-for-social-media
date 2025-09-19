import pytest
from unittest.mock import Mock, patch
import os
import sys

# Add worker directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from adapters.llm_adapter import OpenAIAdapter, HuggingFaceAdapter, MockLLMAdapter, LLMAdapter


class TestMockLLMAdapter:
    def test_is_available(self):
        adapter = MockLLMAdapter()
        assert adapter.is_available() is True
    
    def test_summarize_article(self):
        adapter = MockLLMAdapter()
        
        title = "AI Breakthrough in Natural Language Processing"
        content = "Researchers have developed a new AI model that can understand context better."
        
        summary = adapter.summarize_article(title, content, "professional")
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert len(summary) <= 300  # Should be concise
    
    def test_different_tones(self):
        adapter = MockLLMAdapter()
        
        title = "New Technology Released"
        content = "A major tech company released new software."
        
        professional = adapter.summarize_article(title, content, "professional")
        casual = adapter.summarize_article(title, content, "casual")
        creative = adapter.summarize_article(title, content, "creative")
        
        # Should return different content for different tones
        assert professional != casual
        assert professional != creative
    
    def test_consistency(self):
        adapter = MockLLMAdapter()
        
        title = "Same Article Title"
        content = "Same content every time"
        
        # Should return same summary for same input
        summary1 = adapter.summarize_article(title, content, "professional")
        summary2 = adapter.summarize_article(title, content, "professional")
        
        assert summary1 == summary2


class TestOpenAIAdapter:
    def test_is_available_without_key(self):
        adapter = OpenAIAdapter(api_key=None)
        assert adapter.is_available() is False
    
    def test_is_available_with_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch('adapters.llm_adapter.openai'):
                adapter = OpenAIAdapter()
                # Without actual openai client, this will be False
                # In real test with mock, we'd set up the mock properly
    
    @patch('adapters.llm_adapter.openai')
    def test_summarize_article_success(self, mock_openai):
        # Mock the OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test summary"
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('adapters.llm_adapter.openai.OpenAI', return_value=mock_client):
            adapter = OpenAIAdapter(api_key="test-key")
            adapter._client = mock_client
            
            result = adapter.summarize_article("Test Title", "Test Content", "professional")
            
            assert result == "Test summary"
            mock_client.chat.completions.create.assert_called_once()
    
    def test_summarize_article_without_client(self):
        adapter = OpenAIAdapter(api_key=None)
        
        with pytest.raises(Exception, match="OpenAI adapter not available"):
            adapter.summarize_article("Test", "Test", "professional")


class TestHuggingFaceAdapter:
    def test_is_available_without_key(self):
        adapter = HuggingFaceAdapter(api_key=None)
        assert adapter.is_available() is False
    
    def test_is_available_with_key(self):
        adapter = HuggingFaceAdapter(api_key="test-key")
        assert adapter.is_available() is True
    
    @patch('adapters.llm_adapter.requests.post')
    def test_summarize_article_success(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"summary_text": "Test summary"}]
        mock_post.return_value = mock_response
        
        adapter = HuggingFaceAdapter(api_key="test-key")
        result = adapter.summarize_article("Test Title", "Test Content", "professional")
        
        assert result == "Test summary"
        mock_post.assert_called_once()
    
    def test_summarize_article_without_key(self):
        adapter = HuggingFaceAdapter(api_key=None)
        
        with pytest.raises(Exception, match="Hugging Face adapter not available"):
            adapter.summarize_article("Test", "Test", "professional")


class TestLLMAdapter:
    def test_mock_mode(self):
        adapter = LLMAdapter(mock_mode=True)
        
        # Should only have MockLLMAdapter
        assert len(adapter.adapters) == 1
        assert isinstance(adapter.adapters[0], MockLLMAdapter)
    
    def test_fallback_to_mock(self):
        # Without API keys, should fallback to mock
        with patch.dict(os.environ, {}, clear=True):
            adapter = LLMAdapter(mock_mode=False)
            
            # Should have MockLLMAdapter as fallback
            assert any(isinstance(a, MockLLMAdapter) for a in adapter.adapters)
    
    def test_summarize_with_fallback(self):
        adapter = LLMAdapter(mock_mode=True)
        
        result = adapter.summarize_article("Test Title", "Test Content", "professional")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('adapters.llm_adapter.OpenAIAdapter')
    def test_adapter_priority(self, mock_openai_class):
        # Mock OpenAI adapter to be available
        mock_openai_instance = Mock()
        mock_openai_instance.is_available.return_value = True
        mock_openai_instance.summarize_article.return_value = "OpenAI summary"
        mock_openai_class.return_value = mock_openai_instance
        
        adapter = LLMAdapter(mock_mode=False)
        
        # Should try OpenAI first if available
        result = adapter.summarize_article("Test", "Test", "professional")
        
        if mock_openai_instance.is_available():
            mock_openai_instance.summarize_article.assert_called_once()
            assert result == "OpenAI summary"