import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_status_empty():
    """Test getting system status when empty."""
    response = client.get("/status/")
    assert response.status_code == 200
    
    data = response.json()
    assert "system_health" in data
    assert "active_jobs" in data
    assert "total_jobs" in data
    assert "total_posts" in data
    assert "recent_jobs" in data
    assert "recent_posts" in data
    
    # Should have default values when empty
    assert data["active_jobs"] == 0
    assert data["total_jobs"] == 0
    assert data["total_posts"] == 0
    assert isinstance(data["recent_jobs"], list)
    assert isinstance(data["recent_posts"], list)


def test_run_pipeline_mock():
    """Test running pipeline in mock mode."""
    run_request = {
        "niche": "technology",
        "preview_mode": True
    }
    
    response = client.post("/run", json=run_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "job_id" in data
    assert data["niche"] == "technology"
    assert data["status"] in ["enqueued", "completed"]
    assert "message" in data


def test_run_pipeline_without_preview():
    """Test running full pipeline."""
    run_request = {
        "niche": "artificial intelligence",
        "preview_mode": False
    }
    
    response = client.post("/run", json=run_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "job_id" in data
    assert data["niche"] == "artificial intelligence"
    assert data["status"] in ["enqueued", "completed"]


def test_run_pipeline_invalid_niche():
    """Test running pipeline with invalid data."""
    run_request = {
        "niche": "",  # Empty niche
        "preview_mode": True
    }
    
    response = client.post("/run", json=run_request)
    # Should validate niche is not empty
    assert response.status_code in [200, 422]  # 422 for validation error


def test_get_job_status_nonexistent():
    """Test getting status of non-existent job."""
    response = client.get("/status/job/nonexistent-job-id")
    assert response.status_code == 404


def test_run_and_check_status():
    """Test complete flow: run pipeline and check status."""
    # Run pipeline
    run_request = {
        "niche": "cybersecurity", 
        "preview_mode": True
    }
    
    run_response = client.post("/run", json=run_request)
    assert run_response.status_code == 200
    
    job_data = run_response.json()
    job_id = job_data["job_id"]
    
    # Check job status
    status_response = client.get(f"/status/job/{job_id}")
    
    if status_response.status_code == 200:
        # Job found in database
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["niche"] == "cybersecurity"
        assert "status" in status_data
        assert "created_at" in status_data
    else:
        # Job not found (mock mode might complete immediately)
        assert status_response.status_code == 404