# Pulse - Enterprise News-to-X Automated Pipeline

Pulse is an enterprise-ready, containerized news aggregation and social media posting pipeline with a desktop control panel. It automatically fetches relevant news articles, summarizes them with AI, and posts them to X (Twitter) with proper attribution.

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   PC App    │    │   Backend    │    │   Worker    │
│ (Electron)  │───▶│  (FastAPI)   │───▶│  (Celery)   │
└─────────────┘    └──────────────┘    └─────────────┘
                            │                 │
                            ▼                 ▼
                     ┌─────────────┐   ┌─────────────┐
                     │  Database   │   │   Redis     │
                     │ (PostgreSQL)│   │ (Broker)    │
                     └─────────────┘   └─────────────┘
```

### Components

- **PC App**: Electron + React (TypeScript) - Desktop control panel
- **Backend API**: FastAPI (Python) - Configuration and job management
- **Worker**: Celery + Redis - Async news processing and posting
- **Database**: PostgreSQL (primary) + optional MongoDB
- **Browser Scraping**: Playwright for JS-heavy sites
- **News Sources**: NewsAPI with scraper fallback
- **Summarization**: Pluggable LLM interface (OpenAI/HuggingFace/Mock)
- **Social**: X API integration with rate limiting
- **Infrastructure**: Docker + Kubernetes ready

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for PC app development)
- Python 3.11+ (for local development)

### Local Development

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd pulse
cp .env.example .env
# Edit .env with your API keys
```

2. **Start backend services**:
```bash
docker-compose up -d postgres redis
docker-compose up backend worker
```

3. **Start PC app** (in development mode):
```bash
cd pc-app
npm install
npm run dev
```

4. **Run demo pipeline**:
```bash
chmod +x demo_run.sh
./demo_run.sh
```

### Building the Project

#### Building Docker Images

To build the Docker images for backend and worker services:

```bash
# Build backend service
docker build -t pulse-backend -f backend/Dockerfile .

# Build worker service
docker build -t pulse-worker -f worker/Dockerfile .

# Or build all services using docker-compose
docker-compose build
```

#### Building the PC App

To build the Electron desktop application:

```bash
cd pc-app
npm install
npm run build
```

This will create distributable packages for Windows, macOS, and Linux in the `pc-app/release/` directory.

#### Running Tests

Before building, ensure all tests pass:

```bash
# Backend tests
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov
pytest tests/ -v

# Worker tests
cd ../worker
pip install -r requirements.txt
pip install pytest pytest-cov
pytest tests/ -v

# PC App tests
cd ../pc-app
npm install
npm run test
```

### Production Deployment

For production deployment, use the provided Kubernetes manifests:

```bash
# Apply all manifests
kubectl apply -f infra/k8s/

# Or apply individual components
kubectl apply -f infra/k8s/postgres.yaml
kubectl apply -f infra/k8s/redis.yaml
kubectl apply -f infra/k8s/backend.yaml
kubectl apply -f infra/k8s/worker.yaml
```

Update the image tags in the manifests to point to your built images.

## 📁 Project Structure

```
pulse/
├── backend/           # FastAPI application
│   ├── app/           # API endpoints and core logic
│   ├── tests/         # Unit and integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── worker/            # Celery worker tasks
│   ├── adapters/      # LLM, news, and social API adapters
│   ├── utils/         # Utility functions
│   ├── tests/         # Unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── pc-app/            # Electron + React desktop app
│   ├── src/
│   │   ├── main/      # Electron main process
│   │   ├── renderer/  # React frontend
│   │   └── shared/    # Shared code
│   ├── package.json
│   └── vite.config.ts
├── infra/             # Infrastructure configuration
│   ├── docker-compose.yml
│   ├── k8s/           # Kubernetes manifests
│   │   ├── config.yaml
│   │   ├── postgres.yaml
│   │   ├── redis.yaml
│   │   ├── backend.yaml
│   │   ├── worker.yaml
│   │   └── ingress.yaml
│   └── postgres/
│       └── init.sql
├── tests/             # Integration and end-to-end tests
│   ├── unit/
│   └── integration/
├── .github/           # CI/CD workflows
│   └── workflows/
│       └── ci.yml
├── demo_run.sh        # Demo script
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 🧪 Testing

### Unit Tests

Run backend unit tests:
```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov
pytest tests/ -v
```

Run worker unit tests:
```bash
cd worker
pip install -r requirements.txt
pip install pytest pytest-cov
pytest tests/ -v
```

### Integration Tests

Run integration tests:
```bash
./tests/integration/run_tests.sh
```

### Mock Mode Testing

All components support mock mode for testing without real API keys:
```bash
# Set in .env
MOCK_MODE=true
MOCK_NEWS_ARTICLES=true
MOCK_LLM_RESPONSES=true
MOCK_X_POSTS=true
```

## 🐳 Docker Compose Setup

### Services

- **postgres**: PostgreSQL database for storing configurations, articles, and posts
- **redis**: Redis for Celery task queue and caching
- **backend**: FastAPI application with REST API endpoints
- **worker**: Celery workers processing news articles
- **prometheus**: (Optional) Prometheus for metrics collection
- **grafana**: (Optional) Grafana for dashboard visualization

### Environment Variables

All services are configured through environment variables. See [.env.example](.env.example) for all available options.

## ☸️ Kubernetes Deployment

See [infra/k8s/README.md](infra/k8s/README.md) for detailed Kubernetes deployment instructions.

### Key Features

- Horizontal Pod Autoscaling for backend and worker
- Persistent volumes for PostgreSQL and Redis
- ConfigMaps and Secrets for configuration management
- Ingress for external access
- Resource limits and requests for optimal performance

## 🔧 Configuration

### API Keys Required

For production use, you'll need API keys for:

1. **NewsAPI**: https://newsapi.org/ (optional if using Google Search API)
2. **Google Custom Search API**: 
   - API Key: https://console.cloud.google.com/
   - Custom Search Engine: https://programmablesearchengine.google.com/
3. **OpenAI** (optional): https://platform.openai.com/
4. **Hugging Face** (optional): https://huggingface.co/
5. **X/Twitter API**: https://developer.twitter.com/

### News Source Selection

Pulse supports multiple news sources:

1. **NewsAPI** (primary): Set `NEWSAPI_KEY` in environment
2. **Google Custom Search API** (alternative): 
   - Set `GOOGLE_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID`
   - Requires enabling Custom Search API in Google Cloud Console
   - See [GOOGLE_API_FIX_INSTRUCTIONS.md](GOOGLE_API_FIX_INSTRUCTIONS.md) for setup details
   - Worker service now properly configured to use Google API credentials
3. **Playwright Scraper** (fallback): Automatically used when APIs fail
4. **Mock Mode**: For testing without real API keys

### LLM Provider Selection

Pulse supports multiple LLM providers:

1. **OpenAI**: Set `OPENAI_API_KEY` and `OPENAI_MODEL`
2. **Hugging Face**: Set `HF_API_KEY` and `HF_MODEL`
3. **Mock**: For testing without real API keys

The system will automatically try providers in order of preference.

### Rate Limiting

Pulse implements rate limiting to respect API quotas:

- NewsAPI: Configurable requests per hour
- X API: 50 posts per hour by default
- LLM APIs: Configurable requests per hour

## 📊 Monitoring

### Prometheus Metrics

The backend exposes Prometheus metrics at `/metrics` endpoint:

- HTTP request metrics
- Pipeline job metrics
- System resource usage
- Error rates

### Structured Logging

All components use structured JSON logging for better observability:

``json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "info",
  "logger": "pulse.worker",
  "message": "Article processed successfully",
  "article_id": 123,
  "niche": "technology"
}
```

## 🔒 Security

### API Key Management

- Never commit API keys to version control
- Use environment variables and Kubernetes secrets
- Rotate keys regularly

### Authentication

- PC app requests are JWT-signed
- Implement proper CORS and rate limiting
- Use HTTPS in production

### Data Protection

- Database encryption at rest
- Secure connection strings
- Regular security audits

## 🔄 Extensibility

### Adding New LLM Providers

1. Create a new adapter class implementing `BaseLLMAdapter`
2. Add it to the adapter chain in [worker/adapters/llm_adapter.py](worker/adapters/llm_adapter.py)
3. Update configuration options

### Adding New Social Platforms

1. Create a new poster class similar to `XPoster`
2. Update the worker task to support the new platform
3. Add platform-specific configuration

## 📈 Performance Optimization

### Database Indexes

Key indexes are created automatically:
- Articles by niche and publication date
- Posts by status and platform
- Jobs by status and creation time

### Caching Strategy

- Redis caching for frequently accessed data
- Celery result backend for task results
- Database connection pooling

### Horizontal Scaling

- Multiple worker instances for parallel processing
- Backend replicas for high availability
- Redis clustering for large deployments

## 🛠️ Troubleshooting

### Common Issues

1. **Services not starting**: Check Docker logs and environment variables
2. **Database connection errors**: Verify PostgreSQL is running and credentials are correct
3. **Worker not processing jobs**: Check Redis connectivity and Celery configuration
4. **API rate limits**: Monitor logs for rate limit warnings
5. **Google Search API access denied**: 
   - Verify Custom Search API is enabled in Google Cloud Console
   - Check API key permissions include Custom Search API
   - Ensure Custom Search Engine is configured to search the web
   - See [GOOGLE_API_FIX_INSTRUCTIONS.md](GOOGLE_API_FIX_INSTRUCTIONS.md) for detailed steps

### Debug Commands

```bash
# View service logs
docker-compose logs backend
docker-compose logs worker

# Check service health
docker-compose exec backend curl http://localhost:8000/health
docker-compose exec redis redis-cli ping

# Database access
docker-compose exec postgres psql -U pulse_user -d pulse_db

# Test Google Search API integration
python test_google_search.py
```

## 📚 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /config` - Save pipeline configuration
- `GET /config` - Get current configuration
- `POST /run` - Enqueue a pipeline job
- `GET /status` - Get system status
- `GET /status/job/{job_id}` - Get specific job status
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics

## 🎯 Roadmap

### v1.1 (Next Release)
- Admin dashboard with analytics
- Multi-platform support (LinkedIn, Threads)
- Fact-checking step
- Enhanced error handling

### v2.0 (Future)
- LangGraph/agent-based pipeline
- Dynamic tool selection
- Memory and decision loops
- Advanced analytics and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- Celery for distributed task processing
- Electron for cross-platform desktop apps
- OpenAI and Hugging Face for LLM APIs
- NewsAPI for news aggregation
- All contributors and the open-source community