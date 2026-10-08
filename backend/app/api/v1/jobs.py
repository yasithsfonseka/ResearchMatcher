from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import IngestionJob
from app.schemas.schemas import IngestionJobOut

router = APIRouter()

@router.get("/{job_id}", response_model=IngestionJobOut)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return job
