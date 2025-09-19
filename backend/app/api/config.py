from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
import structlog

from ..database import get_db, PipelineConfig

logger = structlog.get_logger()
router = APIRouter()


class ConfigRequest(BaseModel):
    niches: List[str] = Field(..., description="List of selected niches")
    frequency: str = Field(..., description="Posting frequency (hourly, daily, weekly)")
    tone: str = Field(..., description="Content tone (professional, casual, creative)")
    auto_post: bool = Field(default=False, description="Enable automatic posting")


class ConfigResponse(BaseModel):
    id: int
    niches: List[str]
    frequency: str
    tone: str
    auto_post: bool
    created_at: str
    updated_at: str


@router.post("/", response_model=ConfigResponse)
async def save_config(
    config: ConfigRequest,
    db: Session = Depends(get_db)
):
    """Save pipeline configuration."""
    try:
        # Get existing config or create new one
        db_config = db.query(PipelineConfig).first()
        
        if db_config:
            # Update existing config
            db_config.niches = config.niches
            db_config.frequency = config.frequency
            db_config.tone = config.tone
            db_config.auto_post = config.auto_post
        else:
            # Create new config
            db_config = PipelineConfig(
                niches=config.niches,
                frequency=config.frequency,
                tone=config.tone,
                auto_post=config.auto_post
            )
            db.add(db_config)
        
        db.commit()
        db.refresh(db_config)
        
        logger.info(
            "Configuration saved",
            config_id=db_config.id,
            niches=config.niches,
            frequency=config.frequency,
            tone=config.tone,
            auto_post=config.auto_post
        )
        
        return ConfigResponse(
            id=db_config.id,
            niches=db_config.niches,
            frequency=db_config.frequency,
            tone=db_config.tone,
            auto_post=db_config.auto_post,
            created_at=db_config.created_at.isoformat(),
            updated_at=db_config.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to save configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to save configuration")


@router.get("/", response_model=Optional[ConfigResponse])
async def get_config(db: Session = Depends(get_db)):
    """Get current pipeline configuration."""
    try:
        db_config = db.query(PipelineConfig).first()
        
        if not db_config:
            return None
        
        return ConfigResponse(
            id=db_config.id,
            niches=db_config.niches,
            frequency=db_config.frequency,
            tone=db_config.tone,
            auto_post=db_config.auto_post,
            created_at=db_config.created_at.isoformat(),
            updated_at=db_config.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Failed to get configuration", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get configuration")