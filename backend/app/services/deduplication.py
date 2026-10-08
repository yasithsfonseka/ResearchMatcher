import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    Paper, Author, PaperAuthor, Subject, PaperSubject, PaperSourceRecord
)
from app.providers.base import ProviderPaper
from app.services.normalization import normalize_title, normalize_doi

logger = logging.getLogger(__name__)

def upsert_provider_paper(db: Session, p: ProviderPaper) -> Paper:
    norm_doi = normalize_doi(p.doi)
    norm_title = normalize_title(p.canonical_title)
    
    existing_paper: Optional[Paper] = None
    
    # 1. Prefer DOI match
    if norm_doi:
        existing_paper = db.query(Paper).filter(Paper.doi == norm_doi).first()
        
    # 2. Fallback to exact normalized title match if no DOI or not found
    if not existing_paper and norm_title:
        existing_paper = db.query(Paper).filter(Paper.normalized_title == norm_title).first()
        
    if existing_paper:
        # Update fields if new provider has richer metadata (e.g. abstract)
        if not existing_paper.abstract and p.abstract:
            existing_paper.abstract = p.abstract
        if not existing_paper.venue and p.venue:
            existing_paper.venue = p.venue
        if not existing_paper.publication_date and p.publication_date:
            existing_paper.publication_date = p.publication_date
        if not existing_paper.publication_year and p.publication_year:
            existing_paper.publication_year = p.publication_year
        paper = existing_paper
    else:
        # Create new paper
        paper = Paper(
            canonical_title=p.canonical_title,
            normalized_title=norm_title,
            abstract=p.abstract,
            doi=norm_doi,
            publication_date=p.publication_date,
            publication_year=p.publication_year,
            venue=p.venue,
            work_type=p.work_type,
            language=p.language
        )
        db.add(paper)
        db.flush()

    # Upsert Source Record
    existing_src = db.query(PaperSourceRecord).filter(
        PaperSourceRecord.provider == p.provider,
        PaperSourceRecord.external_id == p.external_id
    ).first()
    
    if not existing_src:
        src = PaperSourceRecord(
            paper_id=paper.id,
            provider=p.provider,
            external_id=p.external_id,
            original_url=p.original_url,
            open_access_url=p.open_access_url,
            access_status=p.access_status,
            citation_count=p.citation_count,
            metadata_json=p.raw_metadata,
            provenance_info=p.provenance_info
        )
        db.add(src)
    else:
        existing_src.citation_count = p.citation_count
        if p.open_access_url:
            existing_src.open_access_url = p.open_access_url

    # Upsert Authors
    for idx, auth_data in enumerate(p.authors):
        author_obj: Optional[Author] = None
        if auth_data.orcid:
            author_obj = db.query(Author).filter(Author.orcid == auth_data.orcid).first()
        if not author_obj:
            author_obj = db.query(Author).filter(Author.display_name == auth_data.display_name).first()
            
        if not author_obj:
            author_obj = Author(display_name=auth_data.display_name, orcid=auth_data.orcid)
            db.add(author_obj)
            db.flush()
            
        # Link paper_author if not exists
        pa_link = db.query(PaperAuthor).filter(
            PaperAuthor.paper_id == paper.id,
            PaperAuthor.author_id == author_obj.id
        ).first()
        if not pa_link:
            pa_link = PaperAuthor(paper_id=paper.id, author_id=author_obj.id, author_order=idx)
            db.add(pa_link)

    # Upsert Subjects
    for subj_data in p.subjects:
        subj_obj = db.query(Subject).filter(
            Subject.provider == p.provider,
            Subject.external_id == subj_data.external_id
        ).first()
        
        if not subj_obj:
            subj_obj = Subject(
                provider=p.provider,
                external_id=subj_data.external_id,
                name=subj_data.name,
                level=subj_data.level
            )
            db.add(subj_obj)
            db.flush()
            
        ps_link = db.query(PaperSubject).filter(
            PaperSubject.paper_id == paper.id,
            PaperSubject.subject_id == subj_obj.id
        ).first()
        if not ps_link:
            ps_link = PaperSubject(
                paper_id=paper.id,
                subject_id=subj_obj.id,
                assignment_method="provider_supplied",
                confidence=subj_data.confidence
            )
            db.add(ps_link)

    db.commit()
    db.refresh(paper)
    return paper
