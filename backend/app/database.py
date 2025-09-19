from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any, Generator
import hashlib
import os

from .config import settings

# Database setup
# Use SQLite in-memory database for testing if PostgreSQL is not available
try:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    DATABASE_AVAILABLE = True
except Exception as e:
    print(f"Database connection failed: {e}")
    print("Using in-memory SQLite database for testing")
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


# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Failed to create tables: {e}")
        # Continue without database tables for testing
        pass