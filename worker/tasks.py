from celery import current_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import structlog
import time
import json
import asyncio

from .celery_app import app, settings
from .adapters.news_fetcher import NewsFetcher, PlaywrightScraper
from .adapters.llm_adapter import LLMAdapter
from .adapters.x_poster import XPoster
from .utils.deduplication import DeduplicationService
from .monitoring import metrics, setup_logging

# Setup logging
logger = setup_logging()

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Import database models (we'll need to share these or recreate them)
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    niche = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    result = Column(JSON)


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
    content_hash = Column(String, unique=True, index=True)
    # Add a field to store image information
    images = Column(JSON)  # Store image URLs and metadata as JSON


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    platform = Column(String, default="x")
    post_id = Column(String)
    status = Column(String, default="pending")
    posted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    error_message = Column(Text)
    engagement_stats = Column(JSON)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, we'll close it manually


@app.task(bind=True, name='fetch_and_post')
def fetch_and_post(self, niche: str, job_id: str, preview_mode: bool = False):
    """
    Main pipeline task: fetch articles, summarize, and post to X.
    
    Args:
        niche: The niche/topic to fetch articles for
        job_id: Unique job identifier
        preview_mode: If True, don't actually post to X
    """
    db = get_db()
    task_id = self.request.id
    
    # Initialize job as None
    job = None
    
    # Record task start for metrics
    start_time = time.time()
    metrics.active_tasks.inc()
    
    try:
        logger.info("Starting pipeline task", job_id=job_id, task_id=task_id, niche=niche)
        
        # Update job status
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            setattr(job, 'status', "running")
            setattr(job, 'started_at', datetime.utcnow())
            db.commit()
        
        # Initialize services
        news_fetcher = NewsFetcher(
            mock_mode=settings.mock_news_articles,
            google_api_key=settings.google_api_key,
            google_search_engine_id=settings.google_search_engine_id,
            newsapi_key=settings.newsapi_key
        )
        llm_adapter = LLMAdapter(mock_mode=settings.mock_llm_responses)
        x_poster = XPoster(mock_mode=settings.mock_x_posts)
        dedup_service = DeduplicationService(db)
        
        results = {
            "articles_fetched": 0,
            "articles_processed": 0,
            "posts_created": 0,
            "posts_published": 0,
            "errors": []
        }
        
        # Step 1: Fetch articles
        logger.info("Fetching articles", niche=niche)
        fetch_start_time = time.time()
        articles = news_fetcher.fetch_articles(niche=niche, limit=5)
        fetch_duration = time.time() - fetch_start_time
        
        # Record fetch metrics
        metrics.news_fetch_duration_seconds.labels(source='newsapi').observe(fetch_duration)
        metrics.articles_fetched_total.labels(source='newsapi', niche=niche).inc(len(articles))
        metrics.news_fetch_requests_total.labels(source='newsapi', status='success').inc()
        
        results["articles_fetched"] = len(articles)
        
        if not articles:
            logger.warning("No articles found", niche=niche)
            metrics.task_processed_total.labels(task_name='fetch_and_post', status='warning').inc()
            raise Exception(f"No articles found for niche: {niche}")
        
        # Step 2: Process each article
        for article_data in articles:
            try:
                # Check for duplicates
                if dedup_service.is_duplicate(article_data):
                    logger.info("Skipping duplicate article", url=article_data.get("url"))
                    metrics.duplicate_articles_skipped_total.inc()
                    continue
                
                # Save article to database (including images)
                article = Article(
                    title=article_data["title"],
                    description=article_data.get("description"),
                    content=article_data.get("content"),
                    url=article_data["url"],
                    source=article_data.get("source", {}).get("name"),
                    author=article_data.get("author"),
                    published_at=datetime.fromisoformat(article_data["publishedAt"].replace("Z", "+00:00")) if article_data.get("publishedAt") else None,
                    niche=niche,
                    content_hash=dedup_service.generate_content_hash(article_data),
                    images=article_data.get("images", [])  # Store images in the database
                )
                db.add(article)
                db.commit()
                db.refresh(article)
                
                # Handle images if they exist
                images = article_data.get("images", [])
                if images:
                    logger.info("Processing images", image_count=len(images), article_id=article.id)
                    # Here you would save images to storage or process them as needed
                    # For now, we'll just log that we have images
                    for img in images:
                        logger.info("Image found", url=img.get("url"), alt=img.get("alt"))
                
                # Step 3: Generate summary
                logger.info("Generating summary", article_id=article.id)
                llm_start_time = time.time()
                summary = llm_adapter.summarize_article(
                    title=str(article.title),
                    content=str(article.description or article.content or ""),
                    tone="professional"  # TODO: Get from config
                )
                llm_duration = time.time() - llm_start_time
                
                # Record LLM metrics
                metrics.llm_request_duration_seconds.labels(provider='default', model='default').observe(llm_duration)
                metrics.llm_requests_total.labels(provider='default', model='default', status='success').inc()
                
                # Step 4: Create post content
                post_content = f"{summary}\n\nSource: {article.url}"
                
                # Truncate to X limits (280 characters)
                if len(post_content) > 280:
                    available_chars = 280 - len(f"\n\nSource: {article.url}") - 3  # 3 for "..."
                    truncated_summary = summary[:available_chars] + "..."
                    post_content = f"{truncated_summary}\n\nSource: {article.url}"
                
                # Save post
                post = Post(
                    article_id=article.id,
                    content=post_content,
                    summary=summary,
                    platform="x",
                    status="pending"
                )
                db.add(post)
                db.commit()
                db.refresh(post)
                
                results["posts_created"] += 1
                
                # Step 5: Publish to X (if not preview mode)
                if not preview_mode:
                    logger.info("Publishing to X", post_id=post.id)
                    post_start_time = time.time()
                    post_result = x_poster.post_tweet(post_content)
                    post_duration = time.time() - post_start_time
                    
                    # Record posting metrics
                    post_status = 'success' if post_result.get("success") else 'failure'
                    metrics.social_post_duration_seconds.labels(platform='x').observe(post_duration)
                    metrics.social_posts_total.labels(platform='x', status=post_status).inc()
                    
                    if post_result.get("success"):
                        setattr(post, 'status', "posted")
                        setattr(post, 'post_id', post_result.get("post_id") or "")
                        setattr(post, 'posted_at', datetime.utcnow())
                        results["posts_published"] += 1
                    else:
                        setattr(post, 'status', "failed")
                        setattr(post, 'error_message', post_result.get("error") or "")
                        results["errors"].append(f"Failed to post: {post_result.get('error')}")
                    
                    db.commit()
                else:
                    logger.info("Preview mode: skipping X posting", post_id=post.id)
                
                results["articles_processed"] += 1
                
            except Exception as e:
                error_msg = f"Error processing article: {str(e)}"
                logger.error(error_msg, article_url=article_data.get("url"))
                results["errors"].append(error_msg)
                metrics.errors_total.labels(task_name='fetch_and_post', error_type='article_processing').inc()
                continue
        
        # Update job status
        if job:
            setattr(job, 'status', "completed")
            setattr(job, 'completed_at', datetime.utcnow())
            setattr(job, 'result', results)
            db.commit()
        
        logger.info("Pipeline task completed", job_id=job_id, results=results)
        metrics.task_processed_total.labels(task_name='fetch_and_post', status='success').inc()
        return results
        
    except Exception as e:
        error_msg = str(e)
        logger.error("Pipeline task failed", job_id=job_id, error=error_msg)
        metrics.task_processed_total.labels(task_name='fetch_and_post', status='failure').inc()
        metrics.errors_total.labels(task_name='fetch_and_post', error_type='pipeline').inc()
        
        # Update job status
        if job:
            setattr(job, 'status', "failed")
            setattr(job, 'completed_at', datetime.utcnow())
            setattr(job, 'error_message', error_msg)
            db.commit()
        
        # Re-raise the exception for Celery
        raise
        
    finally:
        # Record task duration and decrement active tasks
        task_duration = time.time() - start_time
        metrics.task_duration_seconds.labels(task_name='fetch_and_post').observe(task_duration)
        metrics.active_tasks.dec()
        db.close()


@app.task(bind=True, name='fetch_and_post_async')
async def fetch_and_post_async(self, niche: str, job_id: str, preview_mode: bool = False):
    """
    Async version of the main pipeline task: fetch articles with images, summarize, and post to X.
    
    Args:
        niche: The niche/topic to fetch articles for
        job_id: Unique job identifier
        preview_mode: If True, don't actually post to X
    """
    db = get_db()
    task_id = self.request.id
    
    # Initialize job as None
    job = None
    scraper = None
    
    # Record task start for metrics
    start_time = time.time()
    metrics.active_tasks.inc()
    
    try:
        logger.info("Starting async pipeline task", job_id=job_id, task_id=task_id, niche=niche)
        
        # Update job status
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            setattr(job, 'status', "running")
            setattr(job, 'started_at', datetime.utcnow())
            db.commit()
        
        # Initialize services
        news_fetcher = NewsFetcher(
            mock_mode=settings.mock_news_articles,
            google_api_key=settings.google_api_key,
            google_search_engine_id=settings.google_search_engine_id,
            newsapi_key=settings.newsapi_key
        )
        llm_adapter = LLMAdapter(mock_mode=settings.mock_llm_responses)
        x_poster = XPoster(mock_mode=settings.mock_x_posts)
        dedup_service = DeduplicationService(db)
        
        # Initialize Playwright scraper for async operation
        scraper = PlaywrightScraper()
        
        results = {
            "articles_fetched": 0,
            "articles_processed": 0,
            "posts_created": 0,
            "posts_published": 0,
            "errors": []
        }
        
        # Step 1: Fetch articles using NewsAPI or fallback to scraping
        logger.info("Fetching articles", niche=niche)
        fetch_start_time = time.time()
        articles = []
        
        # Try NewsAPI first
        if not settings.mock_news_articles and news_fetcher.newsapi.is_available():
            try:
                articles = news_fetcher.newsapi.fetch_articles(niche=niche, limit=5)
                # Record fetch metrics
                fetch_duration = time.time() - fetch_start_time
                metrics.news_fetch_duration_seconds.labels(source='newsapi').observe(fetch_duration)
                metrics.articles_fetched_total.labels(source='newsapi', niche=niche).inc(len(articles))
                metrics.news_fetch_requests_total.labels(source='newsapi', status='success').inc()
            except Exception as e:
                logger.warning("NewsAPI failed, falling back to scraping", error=str(e))
                metrics.news_fetch_requests_total.labels(source='newsapi', status='failure').inc()
                metrics.errors_total.labels(task_name='fetch_and_post_async', error_type='newsapi_fetch').inc()
        
        # If no articles from NewsAPI, use scraping
        if not articles and not settings.mock_news_articles:
            try:
                # For demonstration, we'll scrape a few mock URLs
                # In a real implementation, you'd want to search for URLs first
                mock_urls = [
                    "https://example-news-site.com/article1",
                    "https://example-news-site.com/article2",
                    "https://example-news-site.com/article3"
                ]
                
                for url in mock_urls[:3]:  # Limit to 3 for demo
                    try:
                        article = await scraper.scrape_article(url)
                        articles.append(article)
                        if len(articles) >= 5:  # Limit to 5 articles
                            break
                    except Exception as e:
                        logger.warning("Failed to scrape article", url=url, error=str(e))
                        metrics.errors_total.labels(task_name='fetch_and_post_async', error_type='scraping').inc()
                        continue
                        
            except Exception as e:
                logger.error("Scraping failed", error=str(e))
                metrics.errors_total.labels(task_name='fetch_and_post_async', error_type='scraping_general').inc()
        
        # Fallback to mock data if needed
        if not articles:
            articles = news_fetcher.mock_fetcher.fetch_articles(niche=niche, limit=5)
            metrics.news_fetch_requests_total.labels(source='mock', status='success').inc()
            
        results["articles_fetched"] = len(articles)
        
        if not articles:
            logger.warning("No articles found", niche=niche)
            metrics.task_processed_total.labels(task_name='fetch_and_post_async', status='warning').inc()
            raise Exception(f"No articles found for niche: {niche}")
        
        # Step 2: Process each article
        for article_data in articles:
            try:
                # Check for duplicates
                if dedup_service.is_duplicate(article_data):
                    logger.info("Skipping duplicate article", url=article_data.get("url"))
                    metrics.duplicate_articles_skipped_total.inc()
                    continue
                
                # Save article to database (including images)
                article = Article(
                    title=article_data["title"],
                    description=article_data.get("description"),
                    content=article_data.get("content"),
                    url=article_data["url"],
                    source=article_data.get("source", {}).get("name"),
                    author=article_data.get("author"),
                    published_at=datetime.fromisoformat(article_data["publishedAt"].replace("Z", "+00:00")) if article_data.get("publishedAt") else None,
                    niche=niche,
                    content_hash=dedup_service.generate_content_hash(article_data),
                    images=article_data.get("images", [])  # Store images in the database
                )
                db.add(article)
                db.commit()
                db.refresh(article)
                
                # Handle images if they exist
                images = article_data.get("images", [])
                if images:
                    logger.info("Processing images", image_count=len(images), article_id=article.id)
                    # Here you would save images to storage or process them as needed
                    # For now, we'll just log that we have images
                    for img in images:
                        logger.info("Image found", url=img.get("url"), alt=img.get("alt"))
                
                # Step 3: Generate summary
                logger.info("Generating summary", article_id=article.id)
                llm_start_time = time.time()
                summary = llm_adapter.summarize_article(
                    title=str(article.title),
                    content=str(article.description or article.content or ""),
                    tone="professional"  # TODO: Get from config
                )
                llm_duration = time.time() - llm_start_time
                
                # Record LLM metrics
                metrics.llm_request_duration_seconds.labels(provider='default', model='default').observe(llm_duration)
                metrics.llm_requests_total.labels(provider='default', model='default', status='success').inc()
                
                # Step 4: Create post content
                post_content = f"{summary}\n\nSource: {article.url}"
                
                # Truncate to X limits (280 characters)
                if len(post_content) > 280:
                    available_chars = 280 - len(f"\n\nSource: {article.url}") - 3  # 3 for "..."
                    truncated_summary = summary[:available_chars] + "..."
                    post_content = f"{truncated_summary}\n\nSource: {article.url}"
                
                # Save post
                post = Post(
                    article_id=article.id,
                    content=post_content,
                    summary=summary,
                    platform="x",
                    status="pending"
                )
                db.add(post)
                db.commit()
                db.refresh(post)
                
                results["posts_created"] += 1
                
                # Step 5: Publish to X (if not preview mode)
                if not preview_mode:
                    logger.info("Publishing to X", post_id=post.id)
                    post_start_time = time.time()
                    post_result = x_poster.post_tweet(post_content)
                    post_duration = time.time() - post_start_time
                    
                    # Record posting metrics
                    post_status = 'success' if post_result.get("success") else 'failure'
                    metrics.social_post_duration_seconds.labels(platform='x').observe(post_duration)
                    metrics.social_posts_total.labels(platform='x', status=post_status).inc()
                    
                    if post_result.get("success"):
                        setattr(post, 'status', "posted")
                        setattr(post, 'post_id', post_result.get("post_id") or "")
                        setattr(post, 'posted_at', datetime.utcnow())
                        results["posts_published"] += 1
                    else:
                        setattr(post, 'status', "failed")
                        setattr(post, 'error_message', post_result.get("error") or "")
                        results["errors"].append(f"Failed to post: {post_result.get('error')}")
                    
                    db.commit()
                else:
                    logger.info("Preview mode: skipping X posting", post_id=post.id)
                
                results["articles_processed"] += 1
                
            except Exception as e:
                error_msg = f"Error processing article: {str(e)}"
                logger.error(error_msg, article_url=article_data.get("url"))
                results["errors"].append(error_msg)
                metrics.errors_total.labels(task_name='fetch_and_post_async', error_type='article_processing').inc()
                continue
        
        # Update job status
        if job:
            setattr(job, 'status', "completed")
            setattr(job, 'completed_at', datetime.utcnow())
            setattr(job, 'result', results)
            db.commit()
        
        logger.info("Pipeline task completed", job_id=job_id, results=results)
        metrics.task_processed_total.labels(task_name='fetch_and_post_async', status='success').inc()
        return results
        
    except Exception as e:
        error_msg = str(e)
        logger.error("Pipeline task failed", job_id=job_id, error=error_msg)
        metrics.task_processed_total.labels(task_name='fetch_and_post_async', status='failure').inc()
        metrics.errors_total.labels(task_name='fetch_and_post_async', error_type='pipeline').inc()
        
        # Update job status
        if job:
            setattr(job, 'status', "failed")
            setattr(job, 'completed_at', datetime.utcnow())
            setattr(job, 'error_message', error_msg)
            db.commit()
        
        # Re-raise the exception for Celery
        raise
        
    finally:
        # Record task duration and decrement active tasks
        task_duration = time.time() - start_time
        metrics.task_duration_seconds.labels(task_name='fetch_and_post_async').observe(task_duration)
        metrics.active_tasks.dec()
        db.close()
        # Clean up scraper if it was used
        if scraper is not None:
            try:
                await scraper.cleanup()
            except:
                pass
