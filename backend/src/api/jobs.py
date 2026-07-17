from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
import uuid

from src.core.pipeline import kairos_pipeline
from src.database.engine import engine
from src.database.models import Job, JobNote

router = APIRouter(tags=["Jobs"])

def get_session():
    with Session(engine) as session:
        yield session

class JobStatusUpdate(BaseModel):
    status: str

@router.get("/")
def get_jobs(session: Session = Depends(get_session)):
    """Fetch all saved jobs for the Kanban board."""
    jobs = session.exec(select(Job)).all()
    return jobs

@router.patch("/{job_id}/status")
def update_job_status(job_id: uuid.UUID, update_data: JobStatusUpdate, session: Session = Depends(get_session)):
    """Update a job's status (Triggered by Kanban Drag & Drop)."""
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = update_data.status
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
