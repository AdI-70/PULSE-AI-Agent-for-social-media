#!/bin/bash
set -e

echo "🚀 Starting Pulse Demo in Mock Mode..."
echo "This script demonstrates the complete pipeline without requiring real API keys"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.example..."
    cp .env.example .env
    
    # Enable mock mode
    sed -i 's/MOCK_MODE=false/MOCK_MODE=true/g' .env
    sed -i 's/MOCK_NEWS_ARTICLES=true/MOCK_NEWS_ARTICLES=true/g' .env
    sed -i 's/MOCK_LLM_RESPONSES=true/MOCK_LLM_RESPONSES=true/g' .env
    sed -i 's/MOCK_X_POSTS=true/MOCK_X_POSTS=true/g' .env
fi

echo "🐳 Starting infrastructure services..."
docker-compose up -d postgres redis

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🚀 Starting backend and worker services..."
docker-compose up -d backend worker

echo "⏳ Waiting for application services to be ready..."
sleep 15

echo "🧪 Testing API endpoints..."

# Test configuration endpoint
echo "📝 Setting up configuration..."
curl -X POST "http://localhost:8000/config" \
  -H "Content-Type: application/json" \
  -d '{
    "niches": ["technology", "artificial intelligence"],
    "frequency": "hourly",
    "tone": "professional",
    "auto_post": false
  }' || echo "⚠️  Config endpoint not ready yet"

echo -e "\n📊 Checking system status..."
curl -X GET "http://localhost:8000/status" || echo "⚠️  Status endpoint not ready yet"

echo -e "\n🔄 Running pipeline in mock mode..."
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{"niche": "technology"}' || echo "⚠️  Run endpoint not ready yet"

echo -e "\n⏳ Waiting for job to complete..."
sleep 10

echo -e "\n📊 Final status check..."
curl -X GET "http://localhost:8000/status" || echo "⚠️  Status endpoint not ready yet"

echo -e "\n✅ Demo completed!"
echo "📚 Check the logs with: docker-compose logs backend worker"
echo "🌐 Visit http://localhost:8000/docs for API documentation"
echo "🖥️  To start the PC app: cd pc-app && npm install && npm run dev"
echo "🛑 To stop all services: docker-compose down"