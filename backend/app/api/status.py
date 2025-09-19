from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import structlog

from ..database import get_db, Job, Post, Article, PipelineConfig

logger = structlog.get_logger()
router = APIRouter()


class JobStatus(BaseModel):
    job_id: str
    niche: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class PostStatus(BaseModel):
    id: int
    content: str
    platform: str
    status: str
    posted_at: Optional[str] = None
    created_at: str
    error_message: Optional[str] = None
    engagement_stats: Optional[Dict[str, Any]] = None


class SystemStatus(BaseModel):
    system_health: str
    active_jobs: int
    total_jobs: int
    total_posts: int
    recent_jobs: List[JobStatus]
    recent_posts: List[PostStatus]
    current_config: Optional[Dict[str, Any]] = None


@router.get("/", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """Get comprehensive system status."""
    try:
        # Get job statistics
        total_jobs = db.query(Job).count()
        active_jobs = db.query(Job).filter(
            Job.status.in_(["pending", "running"])
        ).count()
        
        # Get recent jobs (last 10)
        recent_jobs_db = db.query(Job).order_by(desc(Job.created_at)).limit(10).all()
        recent_jobs = [
            JobStatus(
                job_id=job.job_id,
                niche=job.niche,
                status=job.status,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                error_message=job.error_message,
                result=job.result
            )
            for job in recent_jobs_db
        ]
        
        # Get post statistics
        total_posts = db.query(Post).count()
        
        # Get recent posts (last 10)
        recent_posts_db = db.query(Post).order_by(desc(Post.created_at)).limit(10).all()
        recent_posts = [
            PostStatus(
                id=post.id,
                content=post.content[:100] + "..." if len(post.content) > 100 else post.content,
                platform=post.platform,
                status=post.status,
                posted_at=post.posted_at.isoformat() if post.posted_at else None,
                created_at=post.created_at.isoformat(),
                error_message=post.error_message,
                engagement_stats=post.engagement_stats
            )
            for post in recent_posts_db
        ]
        
        # Get current configuration
        current_config_db = db.query(PipelineConfig).first()
        current_config = None
        if current_config_db:
            current_config = {
                "niches": current_config_db.niches,
                "frequency": current_config_db.frequency,
                "tone": current_config_db.tone,
                "auto_post": current_config_db.auto_post,
                "updated_at": current_config_db.updated_at.isoformat()
            }
        
        # Determine system health
        system_health = "healthy"
        if active_jobs > 10:
            system_health = "busy"
        
        failed_jobs_count = db.query(Job).filter(Job.status == "failed").count()
        if failed_jobs_count > total_jobs * 0.1:  # More than 10% failed
            system_health = "degraded"
        
        return SystemStatus(
            system_health=system_health,
            active_jobs=active_jobs,
            total_jobs=total_jobs,
            total_posts=total_posts,
            recent_jobs=recent_jobs,
            recent_posts=recent_posts,
            current_config=current_config
        )
        
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get status of a specific job."""
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatus(
            job_id=job.job_id,
            niche=job.niche,
            status=job.status,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            error_message=job.error_message,
            result=job.result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", error=str(e), job_id=job_id)
        raise HTTPException(status_code=500, detail="Failed to get job status")