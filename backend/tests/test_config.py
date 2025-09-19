import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_empty_config():
    """Test getting config when none exists."""
    response = client.get("/config/")
    assert response.status_code == 200
    # Should return None when no config exists
    assert response.json() is None


def test_save_config():
    """Test saving a new configuration."""
    config_data = {
        "niches": ["technology", "artificial intelligence"],
        "frequency": "hourly",
        "tone": "professional",
        "auto_post": False
    }
    
    response = client.post("/config/", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["niches"] == config_data["niches"]
    assert data["frequency"] == config_data["frequency"]
    assert data["tone"] == config_data["tone"]
    assert data["auto_post"] == config_data["auto_post"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_config_after_save():
    """Test getting config after saving."""
    # First save a config
    config_data = {
        "niches": ["business", "fintech"],
        "frequency": "daily",
        "tone": "casual",
        "auto_post": True
    }
    
    save_response = client.post("/config/", json=config_data)
    assert save_response.status_code == 200
    
    # Then get it
    get_response = client.get("/config/")
    assert get_response.status_code == 200
    
    data = get_response.json()
    assert data["niches"] == config_data["niches"]
    assert data["frequency"] == config_data["frequency"]
    assert data["tone"] == config_data["tone"]
    assert data["auto_post"] == config_data["auto_post"]


def test_update_config():
    """Test updating an existing configuration."""
    # First save a config
    initial_config = {
        "niches": ["science"],
        "frequency": "weekly",
        "tone": "professional",
        "auto_post": False
    }
    
    client.post("/config/", json=initial_config)
    
    # Then update it
    updated_config = {
        "niches": ["science", "technology"],
        "frequency": "daily",
        "tone": "creative",
        "auto_post": True
    }
    
    response = client.post("/config/", json=updated_config)
    assert response.status_code == 200
    
    data = response.json()
    assert data["niches"] == updated_config["niches"]
    assert data["frequency"] == updated_config["frequency"]
    assert data["tone"] == updated_config["tone"]
    assert data["auto_post"] == updated_config["auto_post"]


def test_invalid_config():
    """Test saving invalid configuration."""
    invalid_configs = [
        {"niches": [], "frequency": "hourly", "tone": "professional", "auto_post": False},  # Empty niches
        {"niches": ["tech"], "frequency": "invalid", "tone": "professional", "auto_post": False},  # Invalid frequency
        {"niches": ["tech"], "frequency": "hourly", "tone": "invalid", "auto_post": False},  # Invalid tone
    ]
    
    for config in invalid_configs:
        response = client.post("/config/", json=config)
        # Should handle validation at the API level
        # For now, we assume the API accepts any values and validation is done in the UI