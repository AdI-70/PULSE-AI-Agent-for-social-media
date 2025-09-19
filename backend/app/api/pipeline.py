from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import structlog
import uuid
from datetime import datetime

from ..database import get_db, Job
from ..monitoring import metrics

logger = structlog.get_logger()
router = APIRouter()


class RunRequest(BaseModel):
    niche: str = Field(..., description="Niche to process")
    preview_mode: bool = Field(default=False, description="Run in preview mode without posting")


class RunResponse(BaseModel):
    job_id: str
    niche: str
    status: str
    message: str


@router.post("/run", response_model=RunResponse)
async def run_pipeline(
    request: RunRequest,
    db: Session = Depends(get_db)
):
    """Enqueue a pipeline job."""
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Create job record
        db_job = Job(
            job_id=job_id,
            niche=request.niche,
            status="pending"
        )
        db.add(db_job)
        db.commit()
        
        # Import Celery task here to avoid circular imports
        from worker.tasks import fetch_and_post
        
        # Enqueue the task
        task = fetch_and_post.delay(
            niche=request.niche,
            job_id=job_id,
            preview_mode=request.preview_mode
        )
        
        # Update job with task ID
        db_job.job_id = task.id
        db.commit()
        
        logger.info(
            "Pipeline job enqueued",
            job_id=job_id,
            task_id=task.id,
            niche=request.niche,
            preview_mode=request.preview_mode
        )
        
        # Update metrics
        metrics.pipeline_jobs_total.labels(
            niche=request.niche,
            status="enqueued"
        ).inc()
        
        metrics.active_jobs.inc()
        
        return RunResponse(
            job_id=job_id,
            niche=request.niche,
            status="enqueued",
            message=f"Pipeline job enqueued for niche: {request.niche}"
        )
        
    except ImportError:
        # Fallback for when Celery worker is not available
        logger.warning("Celery worker not available, running in mock mode")
        
        # Check if job already exists to avoid constraint violation
        existing_job = db.query(Job).filter(Job.job_id == job_id).first()
        if existing_job:
            # If job exists, update it instead of creating a new one
            existing_job.status = "completed"
            existing_job.completed_at = datetime.utcnow()
            existing_job.result = {
                "mock": True,
                "articles_processed": 1,
                "posts_created": 1 if not request.preview_mode else 0,
                "message": "Mock pipeline execution completed successfully"
            }
            db.commit()
        else:
            # Create a mock job that will be marked as completed
            db_job = Job(
                job_id=job_id,
                niche=request.niche,
                status="completed",
                completed_at=datetime.utcnow(),
                result={
                    "mock": True,
                    "articles_processed": 1,
                    "posts_created": 1 if not request.preview_mode else 0,
                    "message": "Mock pipeline execution completed successfully"
                }
            )
            db.add(db_job)
            db.commit()
        
        return RunResponse(
            job_id=job_id,
            niche=request.niche,
            status="completed",
            message=f"Mock pipeline job completed for niche: {request.niche}"
        )
        
    except Exception as e:
        logger.error("Failed to enqueue pipeline job", error=str(e), niche=request.niche)
        raise HTTPException(status_code=500, detail="Failed to enqueue pipeline job")