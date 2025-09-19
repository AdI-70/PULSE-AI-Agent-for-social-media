from typing import List, Dict, Any, Optional
import requests
import structlog
import time
import os
from datetime import datetime, timedelta
import json
import redis

# Add import for metrics
try:
    from ..monitoring import metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None  # Define metrics as None to avoid unbound variable errors

logger = structlog.get_logger()


def _record_rate_limit_hit(service: str):
    """Record a rate limit hit if metrics are available."""
    if METRICS_AVAILABLE and metrics:
        metrics.rate_limit_hits_total.labels(service=service).inc()


def _record_news_fetch_metrics(source: str, niche: str, duration: float, status: str, error_type: Optional[str] = None):
    """Record news fetch metrics if metrics are available."""
    if METRICS_AVAILABLE and metrics:
        metrics.news_fetch_duration_seconds.labels(source=source).observe(duration)
        metrics.news_fetch_requests_total.labels(source=source, status=status).inc()
        if status == 'success':
            metrics.articles_fetched_total.labels(source=source, niche=niche).inc()
        if error_type:
            metrics.errors_total.labels(task_name=f'{source}_fetch', error_type=error_type).inc()


class RedisRateLimiter:
    """Rate limiter using Redis for distributed rate limiting."""
    
    def __init__(self, redis_url: str, max_requests: int, time_window: int = 86400):  # 86400 seconds = 24 hours
        self.redis_client = redis.from_url(redis_url)
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.prefix = "rate_limit"
    
    def _get_key(self, service: str) -> str:
        """Generate Redis key for rate limiting."""
        current_window = int(time.time() // self.time_window)
        return f"{self.prefix}:{service}:{current_window}"
    
    def can_make_request(self, service: str) -> bool:
        """Check if we can make a request without exceeding rate limit."""
        key = self._get_key(service)
        current_count = self.redis_client.get(key)
        if current_count is None:
            return True
        return int(current_count) < self.max_requests
    
    def record_request(self, service: str):
        """Record that a request was made."""
        key = self._get_key(service)
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.time_window)
        pipe.execute()
    
    def wait_time(self, service: str) -> float:
        """Return how long to wait before making the next request."""
        if self.can_make_request(service):
            return 0
        
        # Calculate time until the next window
        current_time = time.time()
        next_window = ((int(current_time) // self.time_window) + 1) * self.time_window
        return next_window - current_time


class GoogleSearchFetcher:
    """Google Search API integration for fetching news articles."""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None, redis_url: str = "redis://localhost:6379/0"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = os.getenv("GOOGLE_SEARCH_BASE_URL", "https://www.googleapis.com/customsearch/v1")
        # Initialize rate limiter for 90 requests per day
        self.rate_limiter = RedisRateLimiter(redis_url, max_requests=90, time_window=86400)  # 24 hours
        self.service_name = "google_search"
        # Debug logging
        logger.debug("GoogleSearchFetcher initialized", 
                    api_key_available=self.api_key is not None,
                    search_engine_id_available=self.search_engine_id is not None,
                    api_key_length=len(self.api_key) if self.api_key else 0,
                    search_engine_id=self.search_engine_id)
    
    def is_available(self) -> bool:
        available = self.api_key is not None and self.search_engine_id is not None
        logger.debug("GoogleSearchFetcher availability check", 
                    available=available,
                    api_key_set=self.api_key is not None,
                    search_engine_id_set=self.search_engine_id is not None)
        return available
    
    def fetch_articles(self, niche: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch articles from Google Search API for a specific niche."""
        if not self.is_available():
            raise Exception("Google Search API key or search engine ID not available")
        
        # Check rate limit
        if not self.rate_limiter.can_make_request(self.service_name):
            wait_time = self.rate_limiter.wait_time(self.service_name)
            logger.warning("Google Search API rate limit reached", wait_seconds=wait_time)
            _record_rate_limit_hit(self.service_name)
            raise Exception(f"Rate limit exceeded. Wait {wait_time:.0f} seconds.")
        
        # Map niches to search queries
        niche_queries = {
            "technology": "technology news site:techcrunch.com OR site:theverge.com OR site:wired.com",
            "artificial intelligence": "artificial intelligence news OR AI news site:ai.googleblog.com OR site:arxiv.org",
            "business": "business news site:wsj.com OR site:bloomberg.com OR site:cnbc.com",
            "science": "science news site:nature.com OR site:scientificamerican.com OR site:sciencenews.org",
            "health": "health news site:webmd.com OR site:mayoclinic.org OR site:healthline.com",
            "climate": "climate change news OR environment news site:grist.org OR site:insideclimatenews.org",
            "cybersecurity": "cybersecurity news site:darkreading.com OR site:threatpost.com OR site:securityweek.com",
            "fintech": "fintech news OR financial technology news site:coindesk.com OR site:finextra.com"
        }
        
        query = niche_queries.get(niche.lower(), f"{niche} news")
        
        # Clean up the query to ensure it's properly formatted
        query = query.replace(" OR ", " | ").replace(" | ", " OR ")
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(limit, 10)  # Google Custom Search API has a maximum of 10 results per request
        }
        
        start_time = time.time()
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            # Convert Google Search results to article format
            articles = []
            for item in items:
                # Extract published date from snippet or use current time
                published_at = item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time")
                if not published_at:
                    published_at = datetime.now().isoformat()
                
                article = {
                    "title": item.get("title", ""),
                    "description": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": {"name": item.get("displayLink", "Unknown")},
                    "publishedAt": published_at
                }
                articles.append(article)
            
            logger.info("Articles fetched from Google Search API", 
                       niche=niche, 
                       count=len(articles))
            
            # Record the successful request for rate limiting
            self.rate_limiter.record_request(self.service_name)
            
            # Record metrics
            duration = time.time() - start_time
            _record_news_fetch_metrics(self.service_name, niche, duration, 'success')
            
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error("Google Search API request failed", error=str(e), status_code=getattr(e.response, 'status_code', 'N/A'))
            duration = time.time() - start_time
            _record_news_fetch_metrics(self.service_name, niche, duration, 'failure', 'request')
            raise
        except Exception as e:
            logger.error("Google Search API processing failed", error=str(e))
            duration = time.time() - start_time
            _record_news_fetch_metrics(self.service_name, niche, duration, 'failure', 'processing')
            raise


class NewsAPIFetcher:
    """NewsAPI.org integration for fetching news articles."""
    
    def __init__(self, api_key: Optional[str] = None, redis_url: str = "redis://localhost:6379/0"):
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        self.base_url = "https://newsapi.org/v2"
        self.headers = {"X-API-Key": self.api_key} if self.api_key else {}
        self.rate_limiter = RedisRateLimiter(redis_url, max_requests=100, time_window=3600)  # 100 requests per hour
        self.service_name = "newsapi"
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def fetch_articles(self, niche: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch articles from NewsAPI for a specific niche."""
        if not self.is_available():
            raise Exception("NewsAPI key not available")
        
        # Check rate limit
        if not self.rate_limiter.can_make_request(self.service_name):
            wait_time = self.rate_limiter.wait_time(self.service_name)
            logger.warning("NewsAPI rate limit reached", wait_seconds=wait_time)
            _record_rate_limit_hit(self.service_name)
            raise Exception(f"Rate limit exceeded. Wait {wait_time:.0f} seconds.")
        
        # Map niches to search queries
        niche_queries = {
            "technology": "technology OR tech OR AI OR artificial intelligence OR software",
            "artificial intelligence": "artificial intelligence OR AI OR machine learning OR deep learning",
            "business": "business OR finance OR economy OR startup OR entrepreneur",
            "science": "science OR research OR discovery OR innovation",
            "health": "health OR medical OR healthcare OR medicine",
            "climate": "climate OR environment OR sustainability OR renewable energy",
            "cybersecurity": "cybersecurity OR security OR hacking OR data breach",
            "fintech": "fintech OR financial technology OR cryptocurrency OR blockchain"
        }
        
        query = niche_queries.get(niche.lower(), niche)
        
        # Get recent articles (last 24 hours)
        from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "popularity",
            "pageSize": limit,
            "language": "en"
        }
        
        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/everything",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            # Filter out articles without proper content
            filtered_articles = []
            for article in articles:
                if (article.get("title") and 
                    article.get("url") and 
                    not article.get("title").startswith("[Removed]")):
                    filtered_articles.append(article)
            
            logger.info("Articles fetched from NewsAPI", 
                       niche=niche, 
                       count=len(filtered_articles),
                       total_available=data.get("totalResults", 0))
            
            # Record the successful request for rate limiting
            self.rate_limiter.record_request(self.service_name)
            
            # Record metrics
            duration = time.time() - start_time
            _record_news_fetch_metrics(self.service_name, niche, duration, 'success')
            
            return filtered_articles
            
        except requests.exceptions.RequestException as e:
            logger.error("NewsAPI request failed", error=str(e))
            duration = time.time() - start_time
            _record_news_fetch_metrics(self.service_name, niche, duration, 'failure', 'request')
            raise
        except Exception as e:
            logger.error("NewsAPI processing failed", error=str(e))
            duration = time.time() - start_time
            _record_news_fetch_metrics(self.service_name, niche, duration, 'failure', 'processing')
            raise


class PlaywrightScraper:
    """Fallback web scraper using Playwright for JS-heavy sites."""
    
    def __init__(self):
        self._browser = None
        self._context = None
    
    async def _init_browser(self):
        """Initialize Playwright browser."""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self._browser = await self.playwright.chromium.launch(headless=True)
            self._context = await self._browser.new_context(
                user_agent="Pulse/1.0 (+https://pulse-news.example.com)"
            )
        except ImportError:
            logger.error("Playwright not installed")
            raise Exception("Playwright not available")
    
    async def scrape_article(self, url: str) -> Dict[str, Any]:
        """Scrape a single article from URL."""
        if not self._browser:
            await self._init_browser()
        
        # Check if context is initialized
        if not self._context:
            raise Exception("Playwright context not initialized")
        
        page = await self._context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Extract article content using common selectors
            title_selectors = [
                "h1",
                "[data-testid='headline']",
                ".article-title",
                ".post-title",
                ".entry-title"
            ]
            
            content_selectors = [
                "[data-testid='article-body']",
                ".article-content",
                ".post-content",
                ".entry-content",
                "article p",
                ".content p"
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title = await page.text_content(selector, timeout=5000)
                    if title:
                        break
                except:
                    continue
            
            content_elements = []
            for selector in content_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        if text and len(text.strip()) > 50:
                            content_elements.append(text.strip())
                    if content_elements:
                        break
                except:
                    continue
            
            content = " ".join(content_elements[:3])  # First 3 paragraphs
            
            # Get meta description as fallback
            description = None
            try:
                description = await page.get_attribute(
                    'meta[name="description"]', 'content', timeout=2000
                )
            except:
                pass
            
            # Extract images from the article
            images = []
            try:
                # Look for article images using common selectors
                image_selectors = [
                    "article img",
                    ".article-content img",
                    ".post-content img",
                    "img[data-src]",
                    "img[src]"
                ]
                
                for selector in image_selectors:
                    try:
                        image_elements = await page.query_selector_all(selector)
                        for img_element in image_elements:
                            # Get image source (try data-src first, then src)
                            src = await img_element.get_attribute("data-src") or await img_element.get_attribute("src")
                            alt = await img_element.get_attribute("alt") or ""
                            
                            if src and src.startswith(("http", "//")):
                                # Convert protocol-relative URLs
                                if src.startswith("//"):
                                    src = "https:" + src
                                
                                images.append({
                                    "url": src,
                                    "alt": alt
                                })
                        if images:
                            break
                    except:
                        continue
                
                # Limit to first 5 images to avoid overwhelming
                images = images[:5]
                
                # Download images if they're not too large
                downloaded_images = []
                for img in images:
                    try:
                        # Check image size before downloading
                        response = await page.request.head(img["url"])
                        content_length = response.headers.get("content-length")
                        
                        # Only download images smaller than 5MB
                        if content_length and int(content_length) < 5 * 1024 * 1024:
                            img_response = await page.request.get(img["url"])
                            img_data = await img_response.body()
                            
                            downloaded_images.append({
                                "url": img["url"],
                                "alt": img["alt"],
                                "data": img_data,  # Binary data of the image
                                "content_type": response.headers.get("content-type", "image/jpeg")
                            })
                    except Exception as e:
                        logger.warning("Failed to download image", url=img["url"], error=str(e))
                        # Still include the image URL even if we can't download it
                        downloaded_images.append(img)
                
                images = downloaded_images
                
            except Exception as e:
                logger.warning("Failed to extract images", error=str(e))
            
            article_data = {
                "title": title or "No title available",
                "description": description,
                "content": content or description or "No content available",
                "url": url,
                "source": {"name": page.url.split("//")[1].split("/")[0] if "//" in page.url else "Unknown"},
                "publishedAt": datetime.now().isoformat(),
                "images": images  # Include the downloaded images
            }
            
            logger.info("Article scraped successfully", url=url, title_length=len(title or ""), image_count=len(images))
            return article_data
            
        except Exception as e:
            logger.error("Article scraping failed", url=url, error=str(e))
            raise
        finally:
            await page.close()
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()


class MockNewsFetcher:
    """Mock news fetcher for testing without API keys."""
    
    def __init__(self):
        self.mock_articles = [
            {
                "title": "AI Breakthrough: New Model Achieves Human-Level Performance",
                "description": "Researchers announce significant advancement in artificial intelligence capabilities with new transformer architecture.",
                "content": "A team of researchers has developed a revolutionary AI model that demonstrates human-level performance across multiple cognitive tasks. The breakthrough represents a significant step forward in machine learning technology.",
                "url": f"https://mock-news.example.com/ai-breakthrough-{int(time.time())}",
                "source": {"name": "Tech News Daily"},
                "author": "Dr. Jane Smith",
                "publishedAt": datetime.now().isoformat()
            },
            {
                "title": "Cybersecurity Alert: New Vulnerability Discovered in Popular Software",
                "description": "Security researchers identify critical vulnerability affecting millions of users worldwide.",
                "content": "A critical security vulnerability has been discovered in widely-used software, prompting urgent updates from developers. The flaw could potentially allow unauthorized access to sensitive data.",
                "url": f"https://mock-news.example.com/security-alert-{int(time.time())}",
                "source": {"name": "Security Weekly"},
                "author": "John Doe",
                "publishedAt": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                "title": "Green Technology Investment Reaches Record High",
                "description": "Sustainable technology sector attracts unprecedented funding as climate concerns drive innovation.",
                "content": "Investment in green technology has reached a record high this quarter, with renewable energy and carbon capture technologies leading the way. The surge reflects growing corporate and government commitment to sustainability.",
                "url": f"https://mock-news.example.com/green-tech-investment-{int(time.time())}",
                "source": {"name": "Business Today"},
                "author": "Sarah Johnson",
                "publishedAt": (datetime.now() - timedelta(hours=4)).isoformat()
            },
            {
                "title": "Quantum Computing Milestone: 1000-Qubit Processor Unveiled",
                "description": "Major tech company reveals breakthrough quantum processor with unprecedented computational power.",
                "content": "A leading technology company has unveiled a quantum processor with over 1000 qubits, marking a significant milestone in quantum computing development. The advancement could accelerate solutions to complex problems.",
                "url": f"https://mock-news.example.com/quantum-milestone-{int(time.time())}",
                "source": {"name": "Science & Tech Journal"},
                "author": "Dr. Michael Chen",
                "publishedAt": (datetime.now() - timedelta(hours=6)).isoformat()
            },
            {
                "title": "Digital Health Platform Revolutionizes Patient Care",
                "description": "New telemedicine platform integrates AI diagnostics with remote monitoring capabilities.",
                "content": "A innovative digital health platform is transforming patient care by combining artificial intelligence diagnostics with comprehensive remote monitoring. The system has shown promising results in clinical trials.",
                "url": f"https://mock-news.example.com/digital-health-{int(time.time())}",
                "source": {"name": "Health Tech News"},
                "author": "Dr. Emily Brown",
                "publishedAt": (datetime.now() - timedelta(hours=8)).isoformat()
            }
        ]
    
    def is_available(self) -> bool:
        return True
    
    def fetch_articles(self, niche: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Return mock articles filtered by niche."""
        start_time = time.time()
        time.sleep(1)  # Simulate API delay
        
        # Filter articles based on niche keywords
        niche_keywords = {
            "technology": ["AI", "tech", "software", "quantum", "digital"],
            "artificial intelligence": ["AI", "machine learning", "model"],
            "cybersecurity": ["security", "vulnerability", "cybersecurity"],
            "business": ["investment", "funding", "business"],
            "health": ["health", "medical", "patient"],
            "science": ["research", "quantum", "breakthrough"]
        }
        
        keywords = niche_keywords.get(niche.lower(), [niche])
        filtered_articles = []
        
        for article in self.mock_articles:
            article_text = f"{article['title']} {article['description']}".lower()
            if any(keyword.lower() in article_text for keyword in keywords):
                # Create a copy with unique URL
                article_copy = article.copy()
                article_copy["url"] = f"{article['url']}-{niche}-{len(filtered_articles)}"
                filtered_articles.append(article_copy)
        
        # If no specific matches, return first few articles
        if not filtered_articles:
            filtered_articles = self.mock_articles[:limit]
        
        result = filtered_articles[:limit]
        logger.info("Mock articles fetched", niche=niche, count=len(result))
        
        # Record metrics
        duration = time.time() - start_time
        _record_news_fetch_metrics('mock', niche, duration, 'success')
        
        return result


class NewsFetcher:
    """Main news fetcher that tries multiple sources."""
    
    def __init__(self, mock_mode: bool = False, google_api_key: Optional[str] = None, google_search_engine_id: Optional[str] = None, newsapi_key: Optional[str] = None, redis_url: str = "redis://localhost:6379/0"):
        self.mock_mode = mock_mode
        self.newsapi = NewsAPIFetcher(api_key=newsapi_key, redis_url=redis_url)
        self.google_fetcher = GoogleSearchFetcher(api_key=google_api_key, search_engine_id=google_search_engine_id, redis_url=redis_url)
        self.scraper = None  # Initialize when needed
        self.mock_fetcher = MockNewsFetcher()
    
    def fetch_articles(self, niche: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch articles using the best available method."""
        if self.mock_mode:
            return self.mock_fetcher.fetch_articles(niche, limit)
        
        # Try Google Search API first (if available)
        if self.google_fetcher.is_available():
            try:
                logger.info("Fetching from Google Search API", niche=niche)
                return self.google_fetcher.fetch_articles(niche, limit)
            except Exception as e:
                logger.warning("Google Search API failed, trying NewsAPI", error=str(e))
        
        # Try NewsAPI next
        if self.newsapi.is_available():
            try:
                logger.info("Fetching from NewsAPI", niche=niche)
                return self.newsapi.fetch_articles(niche, limit)
            except Exception as e:
                logger.warning("NewsAPI failed, falling back to mock", error=str(e))
        
        # Fallback to mock data
        logger.info("Using mock data as fallback", niche=niche)
        return self.mock_fetcher.fetch_articles(niche, limit)