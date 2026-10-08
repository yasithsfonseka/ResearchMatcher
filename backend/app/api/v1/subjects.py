from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Subject, PaperSubject, Paper
from app.schemas.schemas import SubjectOut, PaperOut
from app.services.search_pipeline import build_paper_out

router = APIRouter()

@router.get("", response_model=List[SubjectOut])
def list_subjects(
    level: Optional[str] = None,
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Subject)
    if level:
        query = query.filter(Subject.level == level)
    if provider:
        query = query.filter(Subject.provider == provider)
    return query.order_by(Subject.name.asc()).limit(200).all()

@router.get("/{subject_id}/papers", response_model=List[PaperOut])
def get_papers_by_subject(
    subject_id: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    subj = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    assignments = db.query(PaperSubject).filter(
        PaperSubject.subject_id == subject_id
    ).offset(offset).limit(limit).all()
    
    output = []
    for a in assignments:
        if a.paper:
            output.append(build_paper_out(a.paper))
    return output
