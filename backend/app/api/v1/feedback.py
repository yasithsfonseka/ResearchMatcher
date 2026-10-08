from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import require_current_user
from app.models.models import User, RelevanceFeedback, SearchRun, Paper
from app.schemas.schemas import FeedbackCreate, FeedbackOut

router = APIRouter()

@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    fb_in: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    sr = db.query(SearchRun).filter(SearchRun.id == fb_in.search_run_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Search run not found")
        
    paper = db.query(Paper).filter(Paper.id == fb_in.paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    feedback = RelevanceFeedback(
        user_id=current_user.id,
        search_run_id=fb_in.search_run_id,
        paper_id=fb_in.paper_id,
        relevance_judgment=fb_in.relevance_judgment,
        comment=fb_in.comment
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
