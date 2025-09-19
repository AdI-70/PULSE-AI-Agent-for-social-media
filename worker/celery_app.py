from celery import Celery
import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class WorkerSettings(BaseSettings):
    # Database
    database_url: str = "postgresql://pulse_user:pulse_password@localhost:5432/pulse_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # News API
    newsapi_key: Optional[str] = None
    newsapi_base_url: str = "https://newsapi.org/v2"
    
    # Google Search API
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    google_search_base_url: str = "https://www.googleapis.com/customsearch/v1"
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    hf_api_key: Optional[str] = None
    hf_model: str = "microsoft/DialoGPT-medium"
    
    # X API
    x_bearer_token: Optional[str] = None
    x_api_key: Optional[str] = None
    x_api_secret: Optional[str] = None
    x_access_token: Optional[str] = None
    x_access_token_secret: Optional[str] = None
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    jwt_secret_key: str = "your_jwt_secret_key_here"
    
    # Mock Mode
    mock_mode: bool = False
    mock_news_articles: bool = True
    mock_llm_responses: bool = True
    mock_x_posts: bool = True
    
    # Rate Limiting
    news_fetch_rate_limit: int = 100
    google_search_rate_limit: int = 90
    x_post_rate_limit: int = 50
    llm_request_rate_limit: int = 1000
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Scraping
    playwright_timeout: int = 30000
    user_agent: str = "Pulse/1.0 (+https://pulse-news.example.com)"
    
    # Optional MongoDB
    mongodb_url: Optional[str] = None
    enable_mongodb: bool = False
    
    # Advanced settings
    max_concurrent_tasks: int = 5
    task_timeout_seconds: int = 1800  # 30 minutes
    retry_attempts: int = 3
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Security
    encryption_key: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = WorkerSettings()

# Create Celery app
app = Celery('pulse_worker')

# Configure Celery
app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.task_timeout_seconds,
    task_soft_time_limit=settings.task_timeout_seconds - 300,  # 5 minutes less than hard limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    worker_concurrency=settings.max_concurrent_tasks,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)