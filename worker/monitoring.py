import structlog
import logging
import sys
from pythonjsonlogger.json import JsonFormatter
from prometheus_client import Counter, Histogram, Gauge

# Import settings properly
try:
    from .celery_app import settings
except ImportError:
    # Fallback for when running as a script
    from celery_app import settings


def setup_logging():
    """Setup structured logging with JSON formatter."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    formatter = JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    return structlog.get_logger()


class WorkerMetrics:
    """Prometheus metrics for the worker application."""
    
    def __init__(self):
        # Task metrics
        self.task_processed_total = Counter(
            'pulse_worker_tasks_processed_total',
            'Total worker tasks processed',
            ['task_name', 'status']
        )
        
        self.task_duration_seconds = Histogram(
            'pulse_worker_task_duration_seconds',
            'Worker task duration in seconds',
            ['task_name']
        )
        
        self.task_queue_time_seconds = Histogram(
            'pulse_worker_task_queue_time_seconds',
            'Time tasks spend in queue before processing',
            ['task_name']
        )
        
        # News fetching metrics
        self.news_fetch_requests_total = Counter(
            'pulse_worker_news_fetch_requests_total',
            'Total news fetch requests',
            ['source', 'status']
        )
        
        self.news_fetch_duration_seconds = Histogram(
            'pulse_worker_news_fetch_duration_seconds',
            'News fetch duration in seconds',
            ['source']
        )
        
        self.articles_fetched_total = Counter(
            'pulse_worker_articles_fetched_total',
            'Total articles fetched',
            ['source', 'niche']
        )
        
        # LLM metrics
        self.llm_requests_total = Counter(
            'pulse_worker_llm_requests_total',
            'Total LLM requests',
            ['provider', 'model', 'status']
        )
        
        self.llm_request_duration_seconds = Histogram(
            'pulse_worker_llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['provider', 'model']
        )
        
        # Social media posting metrics
        self.social_posts_total = Counter(
            'pulse_worker_social_posts_total',
            'Total social media posts',
            ['platform', 'status']
        )
        
        self.social_post_duration_seconds = Histogram(
            'pulse_worker_social_post_duration_seconds',
            'Social media post duration in seconds',
            ['platform']
        )
        
        # Rate limiting metrics
        self.rate_limit_hits_total = Counter(
            'pulse_worker_rate_limit_hits_total',
            'Total rate limit hits',
            ['service']
        )
        
        # Deduplication metrics
        self.duplicate_articles_skipped_total = Counter(
            'pulse_worker_duplicate_articles_skipped_total',
            'Total duplicate articles skipped'
        )
        
        # Error metrics
        self.errors_total = Counter(
            'pulse_worker_errors_total',
            'Total worker errors',
            ['task_name', 'error_type']
        )
        
        # System metrics
        self.active_tasks = Gauge(
            'pulse_worker_active_tasks',
            'Number of active worker tasks'
        )
        
        # Database metrics
        self.database_operations_total = Counter(
            'pulse_worker_database_operations_total',
            'Total database operations',
            ['operation', 'table', 'status']
        )
        
        # Security metrics
        self.failed_auth_attempts_total = Counter(
            'pulse_worker_failed_auth_attempts_total',
            'Total failed authentication attempts'
        )


# Global metrics instance
metrics = WorkerMetrics()