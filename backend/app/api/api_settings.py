from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any
import structlog
import json
import os

from ..database import get_db
from ..config import settings

logger = structlog.get_logger()
router = APIRouter()

class ApiSettingsRequest(BaseModel):
    newsApiKey: str = Field(default="", description="NewsAPI key")
    googleSearchApiKey: str = Field(default="", description="Google Search API key")
    googleSearchEngineId: str = Field(default="", description="Google Search Engine ID")
    openaiApiKey: str = Field(default="", description="OpenAI API key")
    huggingfaceApiKey: str = Field(default="", description="Hugging Face API key")
    xApiKey: str = Field(default="", description="X API key")
    xApiSecret: str = Field(default="", description="X API secret")
    xAccessToken: str = Field(default="", description="X access token")
    xAccessTokenSecret: str = Field(default="", description="X access token secret")
    # Rate limits
    newsFetchRateLimit: int = Field(default=100, description="News fetch rate limit per day")
    googleSearchRateLimit: int = Field(default=90, description="Google search rate limit per day")
    xPostRateLimit: int = Field(default=50, description="X post rate limit per day")
    llmRequestRateLimit: int = Field(default=1000, description="LLM request rate limit per day")
    # Mock modes
    mockNewsFetching: bool = Field(default=False, description="Mock news fetching")
    mockLlmSummarization: bool = Field(default=False, description="Mock LLM summarization")
    mockXPosting: bool = Field(default=False, description="Mock X posting")

class ApiSettingsResponse(ApiSettingsRequest):
    pass

# File to store API settings (in production, this would be in a database)
API_SETTINGS_FILE = "api_settings.json"

def save_api_settings_to_file(settings_data: Dict[str, Any]) -> None:
    """Save API settings to a JSON file."""
    # In a real implementation, this would be stored in a database
    # For now, we'll save to a file
    try:
        with open(API_SETTINGS_FILE, "w") as f:
            json.dump(settings_data, f, indent=2)
        logger.info("API settings saved to file", file=API_SETTINGS_FILE)
    except Exception as e:
        logger.error("Failed to save API settings to file", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to save API settings")

def load_api_settings_from_file() -> Dict[str, Any]:
    """Load API settings from a JSON file."""
    # In a real implementation, this would be loaded from a database
    # For now, we'll load from a file
    try:
        if os.path.exists(API_SETTINGS_FILE):
            with open(API_SETTINGS_FILE, "r") as f:
                return json.load(f)
        else:
            # Return default settings
            return {
                "newsApiKey": "",
                "googleSearchApiKey": "",
                "googleSearchEngineId": "",
                "openaiApiKey": "",
                "huggingfaceApiKey": "",
                "xApiKey": "",
                "xApiSecret": "",
                "xAccessToken": "",
                "xAccessTokenSecret": "",
                "newsFetchRateLimit": 100,
                "googleSearchRateLimit": 90,
                "xPostRateLimit": 50,
                "llmRequestRateLimit": 1000,
                "mockNewsFetching": False,
                "mockLlmSummarization": False,
                "mockXPosting": False
            }
    except Exception as e:
        logger.error("Failed to load API settings from file", error=str(e))
        # Return default settings if file can't be read
        return {
            "newsApiKey": "",
            "googleSearchApiKey": "",
            "googleSearchEngineId": "",
            "openaiApiKey": "",
            "huggingfaceApiKey": "",
            "xApiKey": "",
            "xApiSecret": "",
            "xAccessToken": "",
            "xAccessTokenSecret": "",
            "newsFetchRateLimit": 100,
            "googleSearchRateLimit": 90,
            "xPostRateLimit": 50,
            "llmRequestRateLimit": 1000,
            "mockNewsFetching": False,
            "mockLlmSummarization": False,
            "mockXPosting": False
        }

@router.post("/", response_model=ApiSettingsResponse)
async def update_api_settings(
    settings_data: ApiSettingsRequest,
):
    """Update API settings."""
    try:
        # Convert Pydantic model to dict
        settings_dict = settings_data.dict()
        
        # Save to file (in production, this would be saved to a database)
        save_api_settings_to_file(settings_dict)
        
        logger.info("API settings updated")
        
        return ApiSettingsResponse(**settings_dict)
        
    except Exception as e:
        logger.error("Failed to update API settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update API settings")

@router.get("/", response_model=ApiSettingsResponse)
async def get_api_settings():
    """Get current API settings."""
    try:
        # Load from file (in production, this would be loaded from a database)
        settings_dict = load_api_settings_from_file()
        
        logger.info("API settings retrieved")
        
        return ApiSettingsResponse(**settings_dict)
        
    except Exception as e:
        logger.error("Failed to get API settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get API settings")