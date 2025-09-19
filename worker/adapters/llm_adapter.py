from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import structlog
import time
import json
import os

# Add import for metrics
try:
    from ..monitoring import metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None  # Define metrics as None to avoid unbound variable errors

logger = structlog.get_logger()


def _record_llm_metrics(provider: str, model: str, duration: float, status: str, error_type: Optional[str] = None):
    """Record LLM metrics if metrics are available."""
    if METRICS_AVAILABLE and metrics:
        metrics.llm_request_duration_seconds.labels(provider=provider, model=model).observe(duration)
        metrics.llm_requests_total.labels(provider=provider, model=model, status=status).inc()
        if error_type:
            metrics.errors_total.labels(task_name=f'{provider}_llm', error_type=error_type).inc()


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters."""
    
    @abstractmethod
    def summarize_article(self, title: str, content: str, tone: str = "professional") -> str:
        """Summarize an article with the specified tone."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available."""
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI GPT adapter for article summarization."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package not installed")
    
    def is_available(self) -> bool:
        return self.api_key is not None and self._client is not None
    
    def summarize_article(self, title: str, content: str, tone: str = "professional") -> str:
        if not self.is_available():
            raise Exception("OpenAI adapter not available")
        
        tone_instructions = {
            "professional": "in a professional, business-oriented tone",
            "casual": "in a casual, conversational tone", 
            "creative": "in a creative, engaging tone"
        }
        
        tone_instruction = tone_instructions.get(tone, "in a professional tone")
        
        prompt = f"""Summarize this news article {tone_instruction}. Keep it concise (max 200 characters) and suitable for social media posting:

Title: {title}
Content: {content[:1000]}  # Limit content to avoid token limits

Requirements:
- Maximum 200 characters
- Focus on key insights
- Suitable for X/Twitter
- No hashtags
- No quotes around the summary"""
        
        start_time = time.time()
        try:
            if self._client is None:
                raise Exception("OpenAI client not initialized")
                
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a skilled social media content creator who summarizes news articles concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            # Safely extract content from response
            content = ""
            if (response.choices and 
                len(response.choices) > 0 and 
                hasattr(response.choices[0], 'message') and 
                response.choices[0].message and 
                hasattr(response.choices[0].message, 'content') and 
                response.choices[0].message.content):
                content = response.choices[0].message.content
            
            if not content:
                raise Exception("OpenAI API returned empty content")
            
            summary = content.strip()
            
            # Remove quotes if present
            if summary.startswith('"') and summary.endswith('"'):
                summary = summary[1:-1]
            
            logger.info("OpenAI summary generated", model=self.model, length=len(summary))
            
            # Record metrics
            duration = time.time() - start_time
            _record_llm_metrics('openai', self.model, duration, 'success')
            
            return summary
            
        except Exception as e:
            logger.error("OpenAI summarization failed", error=str(e))
            # Record metrics
            duration = time.time() - start_time
            _record_llm_metrics('openai', self.model, duration, 'failure', 'api_error')
            raise


class HuggingFaceAdapter(BaseLLMAdapter):
    """Hugging Face adapter for article summarization."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "microsoft/DialoGPT-medium"):
        self.api_key = api_key or os.getenv("HF_API_KEY")
        self.model = model
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def summarize_article(self, title: str, content: str, tone: str = "professional") -> str:
        if not self.is_available():
            raise Exception("Hugging Face adapter not available")
        
        import requests
        
        # Simple summarization prompt
        text = f"Summarize this news article in one sentence: {title}. {content[:500]}"
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"inputs": text, "parameters": {"max_length": 50, "min_length": 10}}
        
        start_time = time.time()
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Handle different response formats
            summary = ""
            if isinstance(result, list) and len(result) > 0:
                item = result[0]
                if isinstance(item, dict):
                    summary = item.get("summary_text", "") or item.get("generated_text", "") or ""
            elif isinstance(result, dict):
                summary = result.get("summary_text", "") or result.get("generated_text", "") or ""
            
            summary = summary.strip()
            
            logger.info("Hugging Face summary generated", model=self.model, length=len(summary))
            
            # Record metrics
            duration = time.time() - start_time
            _record_llm_metrics('huggingface', self.model, duration, 'success')
            
            return summary
            
        except Exception as e:
            logger.error("Hugging Face summarization failed", error=str(e))
            # Record metrics
            duration = time.time() - start_time
            _record_llm_metrics('huggingface', self.model, duration, 'failure', 'api_error')
            raise


class MockLLMAdapter(BaseLLMAdapter):
    """Mock LLM adapter for testing without API keys."""
    
    def __init__(self):
        self.mock_summaries = [
            "Breaking: New AI breakthrough promises to revolutionize industry efficiency and automation.",
            "Tech giant announces major update with enhanced security features and improved user experience.",
            "Researchers discover innovative solution that could transform renewable energy sector.",
            "Market analysis reveals significant growth trends in emerging technology sectors.",
            "Expert analysis shows promising developments in sustainable technology adoption."
        ]
    
    def is_available(self) -> bool:
        return True
    
    def summarize_article(self, title: str, content: str, tone: str = "professional") -> str:
        start_time = time.time()
        
        # Simulate API delay
        time.sleep(0.5)
        
        # Select summary based on title hash for consistency
        import hashlib
        title_hash = hashlib.md5(title.encode()).hexdigest()
        summary_index = int(title_hash[:2], 16) % len(self.mock_summaries)
        
        summary = self.mock_summaries[summary_index]
        
        # Adjust tone
        if tone == "casual":
            summary = summary.replace("Breaking:", "Check this out:").replace("announces", "just announced")
        elif tone == "creative":
            summary = "🚀 " + summary + " 🔥"
        
        logger.info("Mock summary generated", tone=tone, length=len(summary))
        
        # Record metrics
        duration = time.time() - start_time
        _record_llm_metrics('mock', 'default', duration, 'success')
        
        return summary


class LLMAdapter:
    """Main LLM adapter that tries multiple providers in order."""
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.adapters = []
        
        if mock_mode:
            self.adapters.append(MockLLMAdapter())
        else:
            # Initialize adapters in priority order
            openai_adapter = OpenAIAdapter()
            if openai_adapter.is_available():
                self.adapters.append(openai_adapter)
            
            hf_adapter = HuggingFaceAdapter()
            if hf_adapter.is_available():
                self.adapters.append(hf_adapter)
            
            # Always include mock as fallback
            self.adapters.append(MockLLMAdapter())
    
    def summarize_article(self, title: str, content: str, tone: str = "professional") -> str:
        """Summarize article using the first available adapter."""
        last_error = None
        
        for adapter in self.adapters:
            try:
                logger.info("Attempting summarization", adapter=adapter.__class__.__name__)
                return adapter.summarize_article(title, content, tone)
            except Exception as e:
                last_error = e
                logger.warning("Adapter failed, trying next", 
                             adapter=adapter.__class__.__name__, 
                             error=str(e))
                continue
        
        # If all adapters fail, use a simple fallback
        logger.error("All LLM adapters failed", last_error=str(last_error))
        
        # Simple fallback summary
        fallback = f"{title[:100]}..." if len(title) > 100 else title
        return fallback