from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import require_current_user
from app.models.models import User, Collection, CollectionPaper, Paper
from app.schemas.schemas import (
    CollectionCreate, CollectionUpdate, CollectionOut,
    CollectionPaperCreate, CollectionPaperUpdate, CollectionPaperOut
)
from app.services.search_pipeline import build_paper_out
from app.services.export_csv import generate_collection_csv

router = APIRouter()

def build_collection_out(coll: Collection, include_papers: bool = False) -> CollectionOut:
    paper_count = len(coll.papers)
    papers_out = None
    if include_papers:
        papers_out = [
            CollectionPaperOut(
                collection_id=cp.collection_id,
                paper_id=cp.paper_id,
                paper=build_paper_out(cp.paper),
                notes=cp.notes,
                tags=cp.tags or [],
                reading_status=cp.reading_status,
                added_at=cp.added_at
            )
            for cp in coll.papers if cp.paper
        ]
    return CollectionOut(
        id=coll.id,
        user_id=coll.user_id,
        name=coll.name,
        description=coll.description,
        created_at=coll.created_at,
        updated_at=coll.updated_at,
        paper_count=paper_count,
        papers=papers_out
    )

@router.get("", response_model=List[CollectionOut])
def get_user_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    collections = db.query(Collection).filter(Collection.user_id == current_user.id).order_by(Collection.updated_at.desc()).all()
    return [build_collection_out(c, include_papers=False) for c in collections]

@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(
    c_in: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = Collection(
        user_id=current_user.id,
        name=c_in.name,
        description=c_in.description
    )
    db.add(coll)
    db.commit()
    db.refresh(coll)
    return build_collection_out(coll, include_papers=True)

@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found or authorization denied")
    return build_collection_out(coll, include_papers=True)

@router.patch("/{collection_id}", response_model=CollectionOut)
def update_collection(
    collection_id: str,
    c_in: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found or authorization denied")
        
    if c_in.name is not None:
        coll.name = c_in.name
    if c_in.description is not None:
        coll.description = c_in.description
        
    db.commit()
    db.refresh(coll)
    return build_collection_out(coll, include_papers=True)

@router.delete("/{collection_id}")
def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found or authorization denied")
        
    db.delete(coll)
    db.commit()
    return {"message": "Collection deleted successfully"}

@router.post("/{collection_id}/papers", response_model=CollectionPaperOut)
def add_paper_to_collection(
    collection_id: str,
    cp_in: CollectionPaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found or authorization denied")
        
    paper = db.query(Paper).filter(Paper.id == cp_in.paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    existing = db.query(CollectionPaper).filter(
        CollectionPaper.collection_id == collection_id,
        CollectionPaper.paper_id == cp_in.paper_id
    ).first()
    
    if existing:
        existing.notes = cp_in.notes
        existing.tags = cp_in.tags
        existing.reading_status = cp_in.reading_status
        cp_record = existing
    else:
        cp_record = CollectionPaper(
            collection_id=collection_id,
            paper_id=cp_in.paper_id,
            notes=cp_in.notes,
            tags=cp_in.tags,
            reading_status=cp_in.reading_status
        )
        db.add(cp_record)
        
    db.commit()
    db.refresh(cp_record)
    return CollectionPaperOut(
        collection_id=cp_record.collection_id,
        paper_id=cp_record.paper_id,
        paper=build_paper_out(cp_record.paper),
        notes=cp_record.notes,
        tags=cp_record.tags or [],
        reading_status=cp_record.reading_status,
        added_at=cp_record.added_at
    )

@router.patch("/{collection_id}/papers/{paper_id}", response_model=CollectionPaperOut)
def update_collection_paper(
    collection_id: str,
    paper_id: str,
    cp_in: CollectionPaperUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    cp_record = db.query(CollectionPaper).filter(
        CollectionPaper.collection_id == collection_id,
        CollectionPaper.paper_id == paper_id
    ).first()
    if not cp_record:
        raise HTTPException(status_code=404, detail="Paper not in collection")
        
    if cp_in.notes is not None:
        cp_record.notes = cp_in.notes
    if cp_in.tags is not None:
        cp_record.tags = cp_in.tags
    if cp_in.reading_status is not None:
        cp_record.reading_status = cp_in.reading_status
        
    db.commit()
    db.refresh(cp_record)
    return CollectionPaperOut(
        collection_id=cp_record.collection_id,
        paper_id=cp_record.paper_id,
        paper=build_paper_out(cp_record.paper),
        notes=cp_record.notes,
        tags=cp_record.tags or [],
        reading_status=cp_record.reading_status,
        added_at=cp_record.added_at
    )

@router.delete("/{collection_id}/papers/{paper_id}")
def remove_paper_from_collection(
    collection_id: str,
    paper_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    cp_record = db.query(CollectionPaper).filter(
        CollectionPaper.collection_id == collection_id,
        CollectionPaper.paper_id == paper_id
    ).first()
    if not cp_record:
        raise HTTPException(status_code=404, detail="Paper not in collection")
        
    db.delete(cp_record)
    db.commit()
    return {"message": "Paper removed from collection"}

@router.get("/{collection_id}/export")
def export_collection_csv(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_current_user)
):
    coll = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    csv_data = generate_collection_csv(coll.papers)
    safe_filename = "".join(c for c in coll.name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    headers = {
        "Content-Disposition": f"attachment; filename=collection_{safe_filename}.csv"
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)
