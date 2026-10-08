import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import SearchRun, SearchResult, Paper, PaperEmbedding
from app.schemas.schemas import SearchQueryRequest, SearchResultItem, PaperOut, AuthorOut, SubjectOut, PaperSubjectOut, SourceRecordOut
from app.providers.openalex import OpenAlexProvider
from app.services.deduplication import upsert_provider_paper
from app.services.embeddings import embed_paper, generate_embedding, compute_text_hash
from app.services.explanations import generate_match_explanation
from app.core.config import settings

logger = logging.getLogger(__name__)

def calculate_keyword_score(query_text: str, title: str, abstract: Optional[str]) -> float:
    q_words = set(re.findall(r"\w+", query_text.lower()))
    stopwords = {"a", "an", "the", "in", "on", "of", "and", "or", "for", "to", "with", "is", "at", "by", "from"}
    q_keywords = q_words - stopwords
    if not q_keywords:
        return 0.0
        
    t_words = set(re.findall(r"\w+", title.lower()))
    a_words = set(re.findall(r"\w+", (abstract or "").lower()))
    
    title_matches = q_keywords.intersection(t_words)
    abstract_matches = q_keywords.intersection(a_words)
    
    # Title match weighted 2.0x, abstract match 1.0x
    raw_score = (len(title_matches) * 2.0 + len(abstract_matches) * 1.0) / (len(q_keywords) * 2.0)
    return min(1.0, float(raw_score))

def calculate_subject_score(subject_filters: Optional[List[str]], paper: Paper) -> float:
    if not subject_filters or not paper.subjects:
        return 0.5 # Neutral score if no subject filters applied
    filters_lower = [f.lower() for f in subject_filters]
    matched = 0
    for ps in paper.subjects:
        if ps.subject and any(flt in ps.subject.name.lower() for flt in filters_lower):
            matched += 1
    return 1.0 if matched > 0 else 0.2

def build_paper_out(paper: Paper) -> PaperOut:
    authors_out = [
        AuthorOut(id=pa.author.id, display_name=pa.author.display_name, orcid=pa.author.orcid)
        for pa in paper.authors if pa.author
    ]
    subjects_out = [
        PaperSubjectOut(
            subject=SubjectOut(
                id=ps.subject.id,
                provider=ps.subject.provider,
                external_id=ps.subject.external_id,
                name=ps.subject.name,
                level=ps.subject.level,
                parent_id=ps.subject.parent_id
            ),
            assignment_method=ps.assignment_method,
            confidence=ps.confidence
        )
        for ps in paper.subjects if ps.subject
    ]
    sources_out = [
        SourceRecordOut(
            id=sr.id,
            provider=sr.provider,
            external_id=sr.external_id,
            original_url=sr.original_url,
            open_access_url=sr.open_access_url,
            access_status=sr.access_status,
            citation_count=sr.citation_count,
            provider_updated_at=sr.provider_updated_at,
            retrieved_at=sr.retrieved_at,
            provenance_info=sr.provenance_info
        )
        for sr in paper.source_records
    ]
    return PaperOut(
        id=paper.id,
        canonical_title=paper.canonical_title,
        normalized_title=paper.normalized_title,
        abstract=paper.abstract,
        doi=paper.doi,
        publication_date=paper.publication_date,
        publication_year=paper.publication_year,
        venue=paper.venue,
        work_type=paper.work_type,
        language=paper.language,
        created_at=paper.created_at,
        authors=authors_out,
        source_records=sources_out,
        subjects=subjects_out,
        has_abstract=bool(paper.abstract and paper.abstract.strip())
    )

async def execute_search(
    db: Session,
    req: SearchQueryRequest,
    user_id: Optional[str] = None
) -> Tuple[SearchRun, List[SearchResultItem], Dict[str, Any]]:
    
    provider_status = {}
    fetched_papers: List[Paper] = []
    
    # 1. Retrieve candidates from OpenAlex
    openalex = OpenAlexProvider()
    try:
        oa_results = await openalex.search_papers(
            query=req.research_title,
            keywords=req.keywords,
            year_min=req.year_min,
            year_max=req.year_max,
            open_access_only=req.open_access_only,
            limit=req.limit * 2 # Fetch excess candidates for reranking
        )
        provider_status["openalex"] = {
            "status": "success",
            "candidate_count": len(oa_results)
        }
        for provider_paper in oa_results:
            p_model = upsert_provider_paper(db, provider_paper)
            fetched_papers.append(p_model)
    except Exception as e:
        logger.error(f"OpenAlex retrieval error: {e}")
        provider_status["openalex"] = {
            "status": "error",
            "error_message": str(e),
            "candidate_count": 0
        }

    # Deduplicate fetched candidate papers list
    unique_papers_dict = {p.id: p for p in fetched_papers}
    candidate_papers = list(unique_papers_dict.values())
    
    # Also include existing DB papers matching title/keywords if candidates < limit
    if len(candidate_papers) < req.limit:
        db_candidates = db.query(Paper).limit(req.limit).all()
        for p in db_candidates:
            if p.id not in unique_papers_dict:
                candidate_papers.append(p)
                unique_papers_dict[p.id] = p

    # 2. Query vector embedding for semantic matching
    full_query_text = f"{req.research_title}. {req.research_description or ''} {' '.join(req.keywords or [])}".strip()
    query_vector = generate_embedding(full_query_text)
    
    # Embed candidate papers if not embedded
    paper_vectors: Dict[str, np.ndarray] = {}
    for p in candidate_papers:
        try:
            emb_record = embed_paper(db, p)
            if emb_record and emb_record.embedding is not None:
                emb_val = emb_record.embedding
                if isinstance(emb_val, str):
                    import json
                    emb_val = json.loads(emb_val)
                paper_vectors[p.id] = np.array(emb_val, dtype=np.float32)
        except Exception as e:
            logger.warning(f"Error handling vector for paper {p.id}: {e}")

    # 3. Score and Rank candidates
    query_vec_np = np.array(query_vector, dtype=np.float32) if query_vector else None
    
    scored_items: List[Tuple[Paper, float, float, float, float]] = []
    
    # Configurable weights
    w_kw, w_sem, w_subj = 0.4, 0.5, 0.1
    
    for p in candidate_papers:
        # Keyword score
        kw_score = calculate_keyword_score(full_query_text, p.canonical_title, p.abstract)
        
        # Semantic score (Cosine similarity)
        sem_score = 0.0
        if query_vec_np is not None and p.id in paper_vectors:
            p_vec = paper_vectors[p.id]
            dot_prod = float(np.dot(query_vec_np, p_vec))
            norm_q = float(np.linalg.norm(query_vec_np))
            norm_p = float(np.linalg.norm(p_vec))
            if norm_q > 0 and norm_p > 0:
                # Cosine similarity in range [-1, 1], scale to [0, 1]
                cos_sim = dot_prod / (norm_q * norm_p)
                sem_score = max(0.0, float((cos_sim + 1.0) / 2.0))
        else:
            # Fallback to keyword score if embedding missing
            sem_score = kw_score

        # Subject score
        subj_score = calculate_subject_score(req.subject_filters, p)
        
        # Hybrid final score
        final_score = (w_kw * kw_score) + (w_sem * sem_score) + (w_subj * subj_score)
        scored_items.append((p, kw_score, sem_score, subj_score, final_score))

    # Sort by final score descending
    scored_items.sort(key=lambda x: x[4], reverse=True)
    
    # 4. Save SearchRun
    search_run = SearchRun(
        user_id=user_id,
        research_title=req.research_title,
        research_description=req.research_description,
        keywords=req.keywords,
        subject_filters=req.subject_filters,
        year_min=req.year_min,
        year_max=req.year_max,
        open_access_only=req.open_access_only,
        ranking_config={"w_kw": w_kw, "w_sem": w_sem, "w_subj": w_subj},
        provider_status=provider_status
    )
    db.add(search_run)
    db.flush()

    # 5. Build results & save SearchResults
    results: List[SearchResultItem] = []
    
    paginated_items = scored_items[req.offset : req.offset + req.limit]
    
    for rank, (p, kw_score, sem_score, subj_score, final_score) in enumerate(paginated_items, start=req.offset + 1):
        explanation = generate_match_explanation(
            research_title=req.research_title,
            research_description=req.research_description,
            keywords=req.keywords,
            paper=p,
            keyword_score=kw_score,
            semantic_score=sem_score,
            subject_score=subj_score,
            final_score=final_score
        )
        
        sr = SearchResult(
            search_run_id=search_run.id,
            paper_id=p.id,
            rank=rank,
            keyword_score=kw_score,
            semantic_score=sem_score,
            subject_score=subj_score,
            final_score=final_score,
            explanation_metadata=explanation
        )
        db.add(sr)
        
        paper_out = build_paper_out(p)
        results.append(SearchResultItem(
            paper=paper_out,
            rank=rank,
            keyword_score=kw_score,
            semantic_score=sem_score,
            subject_score=subj_score,
            final_score=final_score,
            explanation=explanation
        ))

    db.commit()
    db.refresh(search_run)
    
    return search_run, results, provider_status
