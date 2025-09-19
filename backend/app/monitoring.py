import structlog
import logging
import sys
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, Gauge
from .config import settings


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
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    return structlog.get_logger()


class Metrics:
    """Prometheus metrics for the application."""
    
    def __init__(self):
        # HTTP metrics
        self.http_requests_total = Counter(
            'pulse_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration_seconds = Histogram(
            'pulse_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Pipeline metrics
        self.pipeline_jobs_total = Counter(
            'pulse_pipeline_jobs_total',
            'Total pipeline jobs',
            ['niche', 'status']
        )
        
        self.pipeline_job_duration_seconds = Histogram(
            'pulse_pipeline_job_duration_seconds',
            'Pipeline job duration in seconds',
            ['niche']
        )
        
        # Article metrics
        self.articles_fetched_total = Counter(
            'pulse_articles_fetched_total',
            'Total articles fetched',
            ['source', 'niche']
        )
        
        self.articles_posted_total = Counter(
            'pulse_articles_posted_total',
            'Total articles posted',
            ['platform', 'niche']
        )
        
        # LLM metrics
        self.llm_requests_total = Counter(
            'pulse_llm_requests_total',
            'Total LLM requests',
            ['provider', 'model']
        )
        
        self.llm_request_duration_seconds = Histogram(
            'pulse_llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['provider', 'model']
        )
        
        # Rate limiting metrics
        self.rate_limit_hits_total = Counter(
            'pulse_rate_limit_hits_total',
            'Total rate limit hits',
            ['service']
        )
        
        # System metrics
        self.active_jobs = Gauge(
            'pulse_active_jobs',
            'Number of active pipeline jobs'
        )


# Global metrics instance
metrics = Metrics()