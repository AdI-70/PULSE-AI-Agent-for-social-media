from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database - using SQLite for local development
    database_url: str = "sqlite:///./pulse.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # News API
    newsapi_key: Optional[str] = None
    newsapi_base_url: str = "https://newsapi.org/v2"
    
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
    mock_mode: bool = True
    mock_news_articles: bool = True
    mock_llm_responses: bool = True
    mock_x_posts: bool = True
    
    # Rate Limiting
    news_fetch_rate_limit: int = 100
    x_post_rate_limit: int = 50
    llm_request_rate_limit: int = 1000
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    class Config:
        env_file = ".env"


settings = Settings()