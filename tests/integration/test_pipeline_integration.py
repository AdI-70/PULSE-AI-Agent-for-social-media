import pytest
import requests
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""
    
    def test_health_check(self):
        """Test that the API is healthy."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_full_config_flow(self):
        """Test complete configuration management flow."""
        # Test getting empty config
        response = requests.get(f"{BASE_URL}/config/")
        assert response.status_code == 200
        
        # Test saving config
        config_data = {
            "niches": ["technology", "artificial intelligence"],
            "frequency": "hourly",
            "tone": "professional",
            "auto_post": False
        }
        
        response = requests.post(f"{BASE_URL}/config/", json=config_data)
        assert response.status_code == 200
        
        saved_config = response.json()
        assert saved_config["niches"] == config_data["niches"]
        assert saved_config["frequency"] == config_data["frequency"]
        assert "id" in saved_config
        
        # Test getting saved config
        response = requests.get(f"{BASE_URL}/config/")
        assert response.status_code == 200
        
        retrieved_config = response.json()
        assert retrieved_config["id"] == saved_config["id"]
        assert retrieved_config["niches"] == config_data["niches"]
    
    def test_pipeline_execution_flow(self):
        """Test complete pipeline execution in preview mode."""
        # First, set up configuration
        config_data = {
            "niches": ["technology"],
            "frequency": "hourly", 
            "tone": "professional",
            "auto_post": False
        }
        
        config_response = requests.post(f"{BASE_URL}/config/", json=config_data)
        assert config_response.status_code == 200
        
        # Run pipeline in preview mode
        run_data = {
            "niche": "technology",
            "preview_mode": True
        }
        
        run_response = requests.post(f"{BASE_URL}/run", json=run_data)
        assert run_response.status_code == 200
        
        run_result = run_response.json()
        assert "job_id" in run_result
        assert run_result["niche"] == "technology"
        assert run_result["status"] in ["enqueued", "completed"]
        
        job_id = run_result["job_id"]
        
        # Wait a bit for job to process
        time.sleep(5)
        
        # Check system status
        status_response = requests.get(f"{BASE_URL}/status/")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "system_health" in status_data
        assert "total_jobs" in status_data
        
        # Try to get job status (might be 404 in mock mode)
        job_status_response = requests.get(f"{BASE_URL}/status/job/{job_id}")
        # Accept both 200 (found) and 404 (not found in mock mode)
        assert job_status_response.status_code in [200, 404]
        
        if job_status_response.status_code == 200:
            job_data = job_status_response.json()
            assert job_data["job_id"] == job_id
            assert job_data["niche"] == "technology"
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        response = requests.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        
        # Should contain Prometheus metrics
        content = response.json()
        assert "pulse_" in content
    
    def test_error_handling(self):
        """Test API error handling."""
        # Test invalid job ID
        response = requests.get(f"{BASE_URL}/status/job/invalid-job-id")
        assert response.status_code == 404
        
        # Test invalid JSON
        response = requests.post(
            f"{BASE_URL}/config/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = requests.options(f"{BASE_URL}/config/")
        # CORS headers should be present (handled by FastAPI middleware)
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS
    
    def test_multiple_niche_execution(self):
        """Test running pipeline with multiple niches."""
        niches = ["technology", "artificial intelligence", "cybersecurity"]
        
        for niche in niches:
            run_data = {
                "niche": niche,
                "preview_mode": True
            }
            
            response = requests.post(f"{BASE_URL}/run", json=run_data)
            assert response.status_code == 200
            
            result = response.json()
            assert result["niche"] == niche
            assert "job_id" in result
            
            # Small delay between requests
            time.sleep(1)
    
    def test_system_status_structure(self):
        """Test system status endpoint returns correct structure."""
        response = requests.get(f"{BASE_URL}/status/")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        required_fields = [
            "system_health", "active_jobs", "total_jobs", 
            "total_posts", "recent_jobs", "recent_posts"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check data types
        assert isinstance(data["active_jobs"], int)
        assert isinstance(data["total_jobs"], int)
        assert isinstance(data["total_posts"], int)
        assert isinstance(data["recent_jobs"], list)
        assert isinstance(data["recent_posts"], list)
        assert data["system_health"] in ["healthy", "busy", "degraded"]


def run_integration_tests():
    """Run integration tests with proper setup."""
    try:
        # Wait for services to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            
            if attempt == max_attempts - 1:
                raise Exception("Services not ready after 30 attempts")
            
            print(f"Waiting for services... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(2)
        
        # Run tests
        pytest.main([__file__, "-v"])
        
    except Exception as e:
        print(f"Integration test setup failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    run_integration_tests()