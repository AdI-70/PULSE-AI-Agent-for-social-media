import os
import time
import requests
import structlog
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Add import for metrics
try:
    from ..monitoring import metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None  # Define metrics as None to avoid unbound variable errors

logger = structlog.get_logger()


def _record_post_metrics(platform: str, duration: float, status: str, error_type: Optional[str] = None):
    """Record social media post metrics if metrics are available."""
    if METRICS_AVAILABLE and metrics:
        metrics.social_post_duration_seconds.labels(platform=platform).observe(duration)
        metrics.social_posts_total.labels(platform=platform, status=status).inc()
        if error_type:
            metrics.errors_total.labels(task_name=f'{platform}_post', error_type=error_type).inc()


def _record_rate_limit_hit(service: str):
    """Record a rate limit hit if metrics are available."""
    if METRICS_AVAILABLE and metrics:
        metrics.rate_limit_hits_total.labels(service=service).inc()


class RateLimiter:
    """Simple rate limiter to respect API limits."""
    
    def __init__(self, max_requests: int, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.requests = []
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding rate limit."""
        now = time.time()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Record that a request was made."""
        self.requests.append(time.time())
    
    def wait_time(self) -> float:
        """Return how long to wait before making the next request."""
        if self.can_make_request():
            return 0
        
        if self.requests:
            oldest_request = min(self.requests)
            return self.time_window - (time.time() - oldest_request)
        return 0


class XAPIClient:
    """X (Twitter) API v2 client with rate limiting and retry logic."""
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        } if self.bearer_token else {}
        
        # Rate limiter: 50 posts per hour as per requirements
        self.rate_limiter = RateLimiter(max_requests=50, time_window=3600)
    
    def is_available(self) -> bool:
        """Check if X API credentials are available."""
        return self.bearer_token is not None
    
    def post_tweet(self, text: str, retry_count: int = 3) -> Dict[str, Any]:
        """Post a tweet with retry logic and rate limiting."""
        if not self.is_available():
            raise Exception("X API credentials not available")
        
        # Check rate limit
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.wait_time()
            logger.warning("Rate limit reached, would need to wait", wait_seconds=wait_time)
            _record_rate_limit_hit('x')
            return {
                "success": False,
                "error": f"Rate limit exceeded. Wait {wait_time:.0f} seconds.",
                "retry_after": wait_time
            }
        
        # Validate tweet length
        if len(text) > 280:
            _record_post_metrics('x', 0, 'failure', 'content_too_long')
            return {
                "success": False,
                "error": f"Tweet too long: {len(text)} characters (max 280)"
            }
        
        payload = {"text": text}
        start_time = time.time()
        
        for attempt in range(retry_count):
            try:
                response = requests.post(
                    f"{self.base_url}/tweets",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                # Record the request for rate limiting
                self.rate_limiter.record_request()
                
                if response.status_code == 201:
                    # Success
                    data = response.json()
                    tweet_id = data.get("data", {}).get("id")
                    
                    logger.info("Tweet posted successfully", 
                               tweet_id=tweet_id, 
                               length=len(text))
                    
                    # Record metrics
                    duration = time.time() - start_time
                    _record_post_metrics('x', duration, 'success')
                    
                    return {
                        "success": True,
                        "post_id": tweet_id,
                        "text": text,
                        "posted_at": datetime.utcnow().isoformat()
                    }
                
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("retry-after", 900))  # Default 15 min
                    logger.warning("X API rate limited", retry_after=retry_after)
                    
                    if attempt < retry_count - 1:
                        time.sleep(min(retry_after, 60))  # Wait max 1 minute for retry
                        continue
                    
                    # Record metrics
                    duration = time.time() - start_time
                    _record_post_metrics('x', duration, 'failure', 'rate_limit')
                    
                    return {
                        "success": False,
                        "error": "Rate limited by X API",
                        "retry_after": retry_after
                    }
                
                elif response.status_code == 403:
                    # Forbidden - might be duplicate content or policy violation
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Forbidden by X API")
                    
                    logger.error("X API forbidden", error=error_msg, status_code=403)
                    
                    # Record metrics
                    duration = time.time() - start_time
                    _record_post_metrics('x', duration, 'failure', 'forbidden')
                    
                    return {
                        "success": False,
                        "error": f"Forbidden: {error_msg}"
                    }
                
                else:
                    # Other error
                    error_msg = f"X API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('detail', 'Unknown error')}"
                    except:
                        error_msg += f" - {response.text}"
                    
                    logger.error("X API request failed", 
                                status_code=response.status_code,
                                error=error_msg)
                    
                    if attempt < retry_count - 1:
                        # Exponential backoff
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                        time.sleep(wait_time)
                        continue
                    
                    # Record metrics
                    duration = time.time() - start_time
                    _record_post_metrics('x', duration, 'failure', 'api_error')
                    
                    return {
                        "success": False,
                        "error": error_msg
                    }
                    
            except requests.exceptions.Timeout:
                logger.warning("X API request timeout", attempt=attempt + 1)
                if attempt < retry_count - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                
                # Record metrics
                duration = time.time() - start_time
                _record_post_metrics('x', duration, 'failure', 'timeout')
                
                return {
                    "success": False,
                    "error": "Request timeout"
                }
                
            except requests.exceptions.RequestException as e:
                logger.error("X API request exception", error=str(e), attempt=attempt + 1)
                if attempt < retry_count - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                
                # Record metrics
                duration = time.time() - start_time
                _record_post_metrics('x', duration, 'failure', 'request_exception')
                
                return {
                    "success": False,
                    "error": f"Request failed: {str(e)}"
                }
        
        # Record metrics for max retries exceeded
        duration = time.time() - start_time
        _record_post_metrics('x', duration, 'failure', 'max_retries')
        
        return {
            "success": False,
            "error": "All retry attempts failed"
        }


class MockXAPIClient:
    """Mock X API client for testing without real API access."""
    
    def __init__(self):
        self.posted_tweets = []
        self.rate_limiter = RateLimiter(max_requests=50, time_window=3600)
    
    def is_available(self) -> bool:
        return True
    
    def post_tweet(self, text: str, retry_count: int = 3) -> Dict[str, Any]:
        """Simulate posting a tweet."""
        start_time = time.time()
        
        # Simulate rate limiting
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.wait_time()
            _record_rate_limit_hit('x_mock')
            # Record metrics
            duration = time.time() - start_time
            _record_post_metrics('x', duration, 'failure', 'rate_limit')
            return {
                "success": False,
                "error": f"Rate limit exceeded. Wait {wait_time:.0f} seconds.",
                "retry_after": wait_time
            }
        
        # Validate tweet length
        if len(text) > 280:
            # Record metrics
            duration = time.time() - start_time
            _record_post_metrics('x', duration, 'failure', 'content_too_long')
            return {
                "success": False,
                "error": f"Tweet too long: {len(text)} characters (max 280)"
            }
        
        # Simulate API delay
        time.sleep(0.5)
        
        # Record request
        self.rate_limiter.record_request()
        
        # Generate mock tweet ID
        tweet_id = f"mock_tweet_{int(time.time())}_{len(self.posted_tweets)}"
        
        tweet_data = {
            "id": tweet_id,
            "text": text,
            "posted_at": datetime.utcnow().isoformat(),
            "mock": True
        }
        
        self.posted_tweets.append(tweet_data)
        
        logger.info("Mock tweet posted", 
                   tweet_id=tweet_id, 
                   length=len(text),
                   total_posted=len(self.posted_tweets))
        
        # Record metrics
        duration = time.time() - start_time
        _record_post_metrics('x', duration, 'success')
        
        return {
            "success": True,
            "post_id": tweet_id,
            "text": text,
            "posted_at": tweet_data["posted_at"],
            "mock": True
        }


class XPoster:
    """Main X poster that handles both real and mock posting."""
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        
        if mock_mode:
            self.client = MockXAPIClient()
        else:
            self.client = XAPIClient()
            # If real API not available, fall back to mock
            if not self.client.is_available():
                logger.warning("X API credentials not available, using mock mode")
                self.client = MockXAPIClient()
                self.mock_mode = True
    
    def post_tweet(self, text: str) -> Dict[str, Any]:
        """Post a tweet using the configured client."""
        logger.info("Posting tweet", 
                   mock_mode=self.mock_mode,
                   length=len(text))
        
        return self.client.post_tweet(text)
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.mock_mode