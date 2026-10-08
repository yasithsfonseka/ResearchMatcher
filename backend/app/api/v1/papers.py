from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Paper, PaperEmbedding
from app.schemas.schemas import PaperOut, PaperResolveRequest
from app.services.search_pipeline import build_paper_out
from app.services.deduplication import upsert_provider_paper
from app.services.normalization import normalize_doi
from app.providers.openalex import OpenAlexProvider
from app.providers.semanticscholar import SemanticScholarProvider
import numpy as np

router = APIRouter()

@router.get("/{paper_id}", response_model=PaperOut)
def get_paper_details(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return build_paper_out(paper)

@router.post("/resolve", response_model=PaperOut)
async def resolve_paper_identifier(
    req: PaperResolveRequest,
    db: Session = Depends(get_db)
):
    identifier = req.identifier.strip()
    
    # Check DB first by DOI or ID
    norm_doi = normalize_doi(identifier)
    paper = None
    if norm_doi:
        paper = db.query(Paper).filter(Paper.doi == norm_doi).first()
    if not paper:
        paper = db.query(Paper).filter(Paper.id == identifier).first()
        
    if paper:
        return build_paper_out(paper)
        
    # Query OpenAlex
    openalex = OpenAlexProvider()
    provider_paper = await openalex.get_paper_by_id(identifier)
    if provider_paper:
        paper = upsert_provider_paper(db, provider_paper)
        return build_paper_out(paper)
        
    # Query Semantic Scholar
    s2 = SemanticScholarProvider()
    provider_paper = await s2.get_paper_by_id(identifier)
    if provider_paper:
        paper = upsert_provider_paper(db, provider_paper)
        return build_paper_out(paper)
        
    raise HTTPException(status_code=404, detail=f"Could not resolve paper identifier '{identifier}' across scholarly sources.")

@router.get("/{paper_id}/similar", response_model=List[PaperOut])
async def get_similar_papers(
    paper_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    # 1. Try vector similarity in local DB pgvector
    target_emb = db.query(PaperEmbedding).filter(PaperEmbedding.paper_id == paper_id).first()
    if target_emb and target_emb.embedding is not None:
        similar_embs = db.query(PaperEmbedding).filter(
            PaperEmbedding.paper_id != paper_id
        ).order_by(
            PaperEmbedding.embedding.l2_distance(target_emb.embedding)
        ).limit(limit).all()
        
        if similar_embs:
            return [build_paper_out(emb.paper) for emb in similar_embs if emb.paper]

    # 2. Fallback to OpenAlex recommendations
    openalex = OpenAlexProvider()
    src_rec = paper.source_records[0] if paper.source_records else None
    ext_id = src_rec.external_id if src_rec else (paper.doi or paper.canonical_title)
    
    provider_papers = await openalex.get_similar_papers(ext_id, limit=limit)
    out_papers = []
    for p in provider_papers:
        p_model = upsert_provider_paper(db, p)
        out_papers.append(build_paper_out(p_model))
        
    return out_papers
