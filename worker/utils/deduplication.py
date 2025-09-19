import hashlib
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog

# Add import for metrics
try:
    from ..monitoring import metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None  # Define metrics as None to avoid unbound variable errors

logger = structlog.get_logger()


def _record_duplicate_skipped():
    """Record a duplicate article skipped if metrics are available."""
    if METRICS_AVAILABLE and metrics:
        metrics.duplicate_articles_skipped_total.inc()


class DeduplicationService:
    """Service for preventing duplicate article processing and posting."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def generate_content_hash(self, article_data: Dict[str, Any]) -> str:
        """Generate a hash for deduplication based on title and description."""
        content_to_hash = f"{article_data.get('title', '')}{article_data.get('description', '')}"
        return hashlib.sha256(content_to_hash.encode()).hexdigest()
    
    def is_duplicate(self, article_data: Dict[str, Any]) -> bool:
        """Check if an article is a duplicate based on URL or content hash."""
        # Import here to avoid circular imports
        from ..tasks import Article
        
        url = article_data.get("url")
        content_hash = self.generate_content_hash(article_data)
        
        # Check for URL duplicates
        if url:
            existing_by_url = self.db.query(Article).filter(Article.url == url).first()
            if existing_by_url:
                logger.info("Duplicate article found by URL", url=url)
                _record_duplicate_skipped()
                return True
        
        # Check for content hash duplicates
        existing_by_hash = self.db.query(Article).filter(Article.content_hash == content_hash).first()
        if existing_by_hash:
            logger.info("Duplicate article found by content hash", content_hash=content_hash)
            _record_duplicate_skipped()
            return True
        
        return False