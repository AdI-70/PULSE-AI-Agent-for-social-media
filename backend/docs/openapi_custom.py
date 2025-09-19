"""
Custom OpenAPI documentation generation for Pulse API
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Pulse API",
        version="2.0.0",
        description="""
## Enterprise News Aggregation API

### Features
- Real-time news fetching from multiple sources
- AI-powered summarization using multiple LLM providers
- Multi-platform social media posting
- Comprehensive monitoring and metrics
- Rate limiting and security features

### Authentication
All API endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Rate Limits
API requests are rate-limited to prevent abuse:
- News fetching: 100 requests per hour
- LLM requests: 1000 requests per hour
- Social media posting: 50 posts per hour

### Error Handling
All endpoints return standard HTTP status codes:
- 200: Success
- 400: Bad request (invalid parameters)
- 401: Unauthorized (missing or invalid token)
- 404: Not found
- 429: Too many requests (rate limit exceeded)
- 500: Internal server error

### Response Format
All successful responses follow a consistent format:
```json
{
  "data": {...},
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "2.0.0"
  }
}
```
""",
        routes=app.routes,
    )
    
    # Add custom examples
    if "paths" in openapi_schema:
        # Configuration endpoint examples
        if "/config/" in openapi_schema["paths"]:
            config_path = openapi_schema["paths"]["/config/"]
            if "post" in config_path:
                config_path["post"]["requestBody"]["content"]["application/json"]["example"] = {
                    "niches": ["technology", "artificial intelligence", "cybersecurity"],
                    "frequency": "hourly",
                    "tone": "professional",
                    "auto_post": True
                }
        
        # Pipeline run endpoint examples
        if "/run" in openapi_schema["paths"]:
            run_path = openapi_schema["paths"]["/run"]
            if "post" in run_path:
                run_path["post"]["requestBody"]["content"]["application/json"]["example"] = {
                    "niche": "artificial intelligence",
                    "preview_mode": False
                }
                if "responses" in run_path["post"]:
                    if "200" in run_path["post"]["responses"]:
                        run_path["post"]["responses"]["200"]["content"]["application/json"]["example"] = {
                            "job_id": "550e8400-e29b-41d4-a716-446655440000",
                            "niche": "artificial intelligence",
                            "status": "enqueued",
                            "message": "Pipeline job enqueued for niche: artificial intelligence"
                        }
        
        # Status endpoint examples
        if "/status/" in openapi_schema["paths"]:
            status_path = openapi_schema["paths"]["/status/"]
            if "get" in status_path:
                if "responses" in status_path["get"]:
                    if "200" in status_path["get"]["responses"]:
                        status_path["get"]["responses"]["200"]["content"]["application/json"]["example"] = {
                            "system_health": "healthy",
                            "active_jobs": 2,
                            "total_jobs": 42,
                            "total_posts": 38,
                            "recent_jobs": [
                                {
                                    "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                    "niche": "technology",
                                    "status": "completed",
                                    "created_at": "2024-01-01T10:00:00Z",
                                    "started_at": "2024-01-01T10:00:05Z",
                                    "completed_at": "2024-01-01T10:02:30Z",
                                    "error_message": None,
                                    "result": {
                                        "articles_fetched": 5,
                                        "articles_processed": 5,
                                        "posts_created": 5,
                                        "posts_published": 5,
                                        "errors": []
                                    }
                                }
                            ],
                            "recent_posts": [
                                {
                                    "id": 123,
                                    "content": "AI Breakthrough: New Model Achieves Human-Level Performance. Source: https://example.com/article",
                                    "platform": "x",
                                    "status": "posted",
                                    "posted_at": "2024-01-01T10:02:30Z",
                                    "created_at": "2024-01-01T10:01:00Z",
                                    "error_message": None,
                                    "engagement_stats": {
                                        "likes": 42,
                                        "retweets": 15,
                                        "comments": 3
                                    }
                                }
                            ]
                        }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema