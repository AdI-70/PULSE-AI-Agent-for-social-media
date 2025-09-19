from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import structlog
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import start_http_server as start_metrics_server
import uvicorn

from .config import settings
from .database import get_db, create_tables
from .api import config, pipeline, status, api_settings
from .monitoring import setup_logging, metrics

# Setup structured logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Pulse API",
    description="Enterprise News-to-X Automated Pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router, prefix="/config", tags=["configuration"])
app.include_router(pipeline.router, prefix="", tags=["pipeline"])
app.include_router(status.router, prefix="/status", tags=["status"])
app.include_router(api_settings.router, prefix="/api-settings", tags=["api-settings"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Pulse API", version="1.0.0", environment=settings.app_env)
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    # Start Prometheus metrics server if enabled
    if settings.enable_metrics:
        start_metrics_server(settings.metrics_port)
        logger.info("Metrics server started", port=settings.metrics_port)


@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests with timing."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    logger.info(
        "HTTP request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration_seconds=duration
    )
    
    # Update Prometheus metrics
    metrics.http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    metrics.http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return JSONResponse(
        content=generate_latest().decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        method=request.method,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower()
    )