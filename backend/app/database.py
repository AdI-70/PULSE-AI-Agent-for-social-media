from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from sqlalchemy.pool import QueuePool
from datetime import datetime
from typing import Optional, List, Dict, Any, Generator
import hashlib
import os
import time
import structlog

from .config import settings
from .monitoring import metrics

logger = structlog.get_logger()

# Database setup
# Use SQLite in-memory database for testing if PostgreSQL is not available
try:
    # Enhanced connection pooling
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=40,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=False
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    DATABASE_AVAILABLE = True
except Exception as e:
    logger.error("Database connection failed", error=str(e))
    logger.info("Using in-memory SQLite database for testing")
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    DATABASE_AVAILABLE = False


class PipelineConfig(Base):
    __tablename__ = "pipeline_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    niches = Column(JSON)  # List of selected niches
    frequency = Column(String)  # hourly, daily, etc.
    tone = Column(String)  # professional, casual, creative
    auto_post = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text)
    url = Column(String, nullable=False, unique=True)
    source = Column(String)
    author = Column(String)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, server_default=func.now())
    niche = Column(String)
    content_hash = Column(String, unique=True, index=True)  # For deduplication
    
    def generate_content_hash(self) -> str:
        """Generate a hash for deduplication based on title and content."""
        content_to_hash = f"{self.title}{self.description or ''}"
        return hashlib.sha256(content_to_hash.encode()).hexdigest()


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Generated post content
    summary = Column(Text)  # Article summary
    platform = Column(String, default="x")  # x, linkedin, etc.
    post_id = Column(String)  # Platform-specific post ID
    status = Column(String, default="pending")  # pending, posted, failed
    posted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    error_message = Column(Text)
    engagement_stats = Column(JSON)  # likes, retweets, etc.


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)  # Celery task ID
    niche = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    result = Column(JSON)  # Job results and metadata


# Dependency to get DB session with monitoring
def get_db() -> Generator[Session, None, None]:
    start_time = time.time()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        duration = time.time() - start_time
        metrics.database_query_duration_seconds.labels(query_type='session').observe(duration)


# Create all tables
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error("Failed to create tables", error=str(e))
        # Continue without database tables for testing
        pass