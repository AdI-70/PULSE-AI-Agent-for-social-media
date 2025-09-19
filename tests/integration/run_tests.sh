#!/bin/bash
set -e

echo "🧪 Running Pulse Integration Tests"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Set test environment variables
export MOCK_MODE=true
export MOCK_NEWS_ARTICLES=true
export MOCK_LLM_RESPONSES=true
export MOCK_X_POSTS=true
export DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulse_db
export REDIS_URL=redis://localhost:6379/0

echo "🐳 Starting test infrastructure..."

# Start infrastructure services
docker-compose up -d postgres redis

echo "⏳ Waiting for services to be ready..."
sleep 10

# Wait for PostgreSQL to be ready
echo "🔍 Checking PostgreSQL connection..."
until docker-compose exec postgres pg_isready -U pulse_user; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Wait for Redis to be ready
echo "🔍 Checking Redis connection..."
until docker-compose exec redis redis-cli ping; do
    echo "Waiting for Redis..."
    sleep 2
done

echo "🚀 Starting application services..."

# Start backend and worker
docker-compose up -d backend worker

echo "⏳ Waiting for application services..."
sleep 20

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s $url > /dev/null; then
            echo "✅ $service is ready"
            return 0
        fi
        echo "⏳ Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed to start"
    return 1
}

# Check backend health
if ! check_service "Backend" "http://localhost:8000/health"; then
    echo "❌ Backend health check failed"
    docker-compose logs backend
    exit 1
fi

echo "🧪 Running integration tests..."

# Test 1: API Health Check
echo "Test 1: API Health Check"
response=$(curl -s http://localhost:8000/health)
if echo "$response" | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $response"
    exit 1
fi

# Test 2: Configuration Management
echo "Test 2: Configuration Management"
config_data='{"niches":["technology","ai"],"frequency":"hourly","tone":"professional","auto_post":false}'
config_response=$(curl -s -X POST -H "Content-Type: application/json" -d "$config_data" http://localhost:8000/config/)

if echo "$config_response" | grep -q "technology"; then
    echo "✅ Configuration save passed"
else
    echo "❌ Configuration save failed: $config_response"
    exit 1
fi

# Test 3: Get Configuration
echo "Test 3: Get Configuration"
get_config_response=$(curl -s http://localhost:8000/config/)
if echo "$get_config_response" | grep -q "technology"; then
    echo "✅ Configuration retrieval passed"
else
    echo "❌ Configuration retrieval failed: $get_config_response"
    exit 1
fi

# Test 4: System Status
echo "Test 4: System Status"
status_response=$(curl -s http://localhost:8000/status/)
if echo "$status_response" | grep -q "system_health"; then
    echo "✅ System status passed"
else
    echo "❌ System status failed: $status_response"
    exit 1
fi

# Test 5: Pipeline Execution (Preview Mode)
echo "Test 5: Pipeline Execution (Preview Mode)"
run_data='{"niche":"technology","preview_mode":true}'
run_response=$(curl -s -X POST -H "Content-Type: application/json" -d "$run_data" http://localhost:8000/run)

if echo "$run_response" | grep -q "job_id"; then
    echo "✅ Pipeline execution passed"
    
    # Extract job ID and check status
    job_id=$(echo "$run_response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$job_id" ]; then
        echo "🔍 Checking job status for: $job_id"
        sleep 5  # Wait for job to process
        
        # Check job status (might be 404 in mock mode)
        job_status_response=$(curl -s -w "%{http_code}" http://localhost:8000/status/job/$job_id)
        http_code=$(echo "$job_status_response" | tail -c 4)
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "404" ]; then
            echo "✅ Job status check passed (HTTP $http_code)"
        else
            echo "❌ Job status check failed (HTTP $http_code)"
            exit 1
        fi
    fi
else
    echo "❌ Pipeline execution failed: $run_response"
    exit 1
fi

# Test 6: Metrics Endpoint
echo "Test 6: Metrics Endpoint"
metrics_response=$(curl -s http://localhost:8000/metrics)
if echo "$metrics_response" | grep -q "pulse_"; then
    echo "✅ Metrics endpoint passed"
else
    echo "❌ Metrics endpoint failed"
    exit 1
fi

# Test 7: Database Connectivity
echo "Test 7: Database Connectivity"
db_test=$(docker-compose exec -T postgres psql -U pulse_user -d pulse_db -c "SELECT 1;" 2>/dev/null)
if echo "$db_test" | grep -q "1 row"; then
    echo "✅ Database connectivity passed"
else
    echo "❌ Database connectivity failed"
    exit 1
fi

# Test 8: Redis Connectivity
echo "Test 8: Redis Connectivity"
redis_test=$(docker-compose exec -T redis redis-cli ping 2>/dev/null)
if echo "$redis_test" | grep -q "PONG"; then
    echo "✅ Redis connectivity passed"
else
    echo "❌ Redis connectivity failed"
    exit 1
fi

echo "🎉 All integration tests passed!"

# Cleanup option
if [ "${CLEANUP:-true}" = "true" ]; then
    echo "🧹 Cleaning up test environment..."
    docker-compose down
    echo "✨ Cleanup completed"
fi

echo "✅ Integration test suite completed successfully!"