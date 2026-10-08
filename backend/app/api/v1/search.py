from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import SearchQueryRequest, SearchResponse, SearchResultItem, SearchRunOut
from app.services.search_pipeline import execute_search, build_paper_out
from app.api.v1.auth import get_current_user
from app.models.models import User, SearchRun, SearchResult, Paper

router = APIRouter()

@router.post("", response_model=SearchResponse)
async def create_search(
    req: SearchQueryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    user_id = current_user.id if current_user else None
    search_run, results, provider_status = await execute_search(db, req, user_id=user_id)
    
    return SearchResponse(
        search_id=search_run.id,
        total_count=len(results),
        results=results,
        provider_status=provider_status
    )

@router.get("/{search_id}", response_model=SearchRunOut)
def get_search_run(
    search_id: str,
    db: Session = Depends(get_db)
):
    sr = db.query(SearchRun).filter(SearchRun.id == search_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Search run not found")
    return sr

@router.get("/{search_id}/results", response_model=List[SearchResultItem])
def get_search_results(
    search_id: str,
    db: Session = Depends(get_db)
):
    sr = db.query(SearchRun).filter(SearchRun.id == search_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Search run not found")
        
    db_results = db.query(SearchResult).filter(SearchResult.search_run_id == search_id).order_by(SearchResult.rank.asc()).all()
    
    output = []
    for res in db_results:
        paper_out = build_paper_out(res.paper)
        output.append(SearchResultItem(
            paper=paper_out,
            rank=res.rank,
            keyword_score=res.keyword_score,
            semantic_score=res.semantic_score,
            subject_score=res.subject_score,
            final_score=res.final_score,
            explanation=res.explanation_metadata or {}
        ))
    return output
