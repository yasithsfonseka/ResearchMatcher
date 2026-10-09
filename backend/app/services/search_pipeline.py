import re
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool
from app.models.models import SearchRun, SearchResult, Paper, PaperEmbedding
from app.schemas.schemas import SearchQueryRequest, SearchResultItem, PaperOut, AuthorOut, SubjectOut, PaperSubjectOut, SourceRecordOut
from app.providers.openalex import OpenAlexProvider
from app.services.deduplication import upsert_provider_paper
from app.services.embeddings import embed_paper, embed_texts, generate_embedding, compute_text_hash
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
    oa_results: List[Any] = []
    
    # 1. Retrieve candidates from OpenAlex (async I/O stays on the event loop)
    openalex = OpenAlexProvider()
    logger.info("search stage=openalex_fetch starting")
    fetch_started = time.perf_counter()
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
    except Exception as e:
        logger.error(f"OpenAlex retrieval error: {e}")
        provider_status["openalex"] = {
            "status": "error",
            "error_message": str(e),
            "candidate_count": 0
        }
    logger.info(
        "search stage=openalex_fetch elapsed=%.2fs count=%d",
        time.perf_counter() - fetch_started,
        len(oa_results)
    )

    # All remaining work is synchronous (DB, embeddings, scoring); run it in a worker thread
    return await run_in_threadpool(_run_search_sync, db, req, oa_results, provider_status, user_id)


def _run_search_sync(
    db: Session,
    req: SearchQueryRequest,
    oa_results: List[Any],
    provider_status: Dict[str, Any],
    user_id: Optional[str] = None
) -> Tuple[SearchRun, List[SearchResultItem], Dict[str, Any]]:
    try:
        return _run_search_stages(db, req, oa_results, provider_status, user_id)
    except Exception:
        # Never leave an open transaction (and its row locks) behind after a failed request.
        logger.exception("search failed; rolling back session")
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.warning("Rollback after search failure also failed: %s", rollback_error)
        raise


def _run_search_stages(
    db: Session,
    req: SearchQueryRequest,
    oa_results: List[Any],
    provider_status: Dict[str, Any],
    user_id: Optional[str] = None
) -> Tuple[SearchRun, List[SearchResultItem], Dict[str, Any]]:
    fetched_papers: List[Paper] = []

    logger.info("search stage=upsert starting count=%d", len(oa_results))
    upsert_started = time.perf_counter()
    for provider_paper in oa_results:
        try:
            p_model = upsert_provider_paper(db, provider_paper)
            fetched_papers.append(p_model)
        except Exception as e:
            # Reset the session so it stays usable, then skip only this paper.
            db.rollback()
            logger.warning(
                "Skipping paper after upsert failure (doi=%s, title=%r): %s",
                getattr(provider_paper, "doi", None),
                getattr(provider_paper, "canonical_title", None),
                e
            )
    logger.info(
        "search stage=upsert elapsed=%.2fs count=%d",
        time.perf_counter() - upsert_started,
        len(fetched_papers)
    )

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
    logger.info("search stage=embed_query starting")
    query_embed_started = time.perf_counter()
    query_vector = generate_embedding(full_query_text)
    logger.info("search stage=embed_query elapsed=%.2fs", time.perf_counter() - query_embed_started)
    
    # Embed candidate papers if not embedded
    paper_vectors: Dict[str, np.ndarray] = {}

    def _to_np(emb_val: Any) -> np.ndarray:
        if isinstance(emb_val, str):
            import json
            emb_val = json.loads(emb_val)
        return np.array(emb_val, dtype=np.float32)

    def _warn_paper(p: Paper, e: Exception) -> None:
        logger.warning(
            "Error handling vector for paper %s (doi=%s, title=%r): %s",
            p.id, p.doi, p.canonical_title, e
        )

    logger.info("search stage=embed_papers starting candidates=%d", len(candidate_papers))
    embed_started = time.perf_counter()

    # Reuse stored embeddings; collect the rest so they can be encoded in one batch
    pending: List[Tuple[Paper, str, str]] = []  # (paper, text, input_hash)
    for p in candidate_papers:
        try:
            text_content = f"{p.canonical_title}. {p.abstract or ''}".strip()
            if not text_content:
                continue
            input_hash = compute_text_hash(text_content)
            existing = db.query(PaperEmbedding).filter(
                PaperEmbedding.paper_id == p.id,
                PaperEmbedding.model_id == settings.EMBEDDING_MODEL_NAME,
                PaperEmbedding.input_hash == input_hash
            ).first()
            if existing and existing.embedding is not None:
                paper_vectors[p.id] = _to_np(existing.embedding)
            else:
                pending.append((p, text_content, input_hash))
        except Exception as e:
            db.rollback()
            _warn_paper(p, e)

    if pending:
        try:
            batch_vectors = embed_texts([text_content for _, text_content, _ in pending])
            if len(batch_vectors) != len(pending):
                raise ValueError("batch embedding size mismatch")
        except Exception as e:
            logger.warning("Batch embedding failed (%s); falling back to per-paper embedding", e)
            batch_vectors = None

        if batch_vectors is not None:
            for (p, _, input_hash), vec in zip(pending, batch_vectors):
                try:
                    paper_id = p.id
                    db.add(PaperEmbedding(
                        paper_id=paper_id,
                        model_id=settings.EMBEDDING_MODEL_NAME,
                        model_revision="v1",
                        input_hash=input_hash,
                        embedding=vec
                    ))
                    db.commit()
                    paper_vectors[paper_id] = np.array(vec, dtype=np.float32)
                except Exception as e:
                    db.rollback()
                    _warn_paper(p, e)
        else:
            for p, _, _ in pending:
                try:
                    emb_record = embed_paper(db, p)
                    if emb_record and emb_record.embedding is not None:
                        paper_vectors[p.id] = _to_np(emb_record.embedding)
                except Exception as e:
                    db.rollback()
                    _warn_paper(p, e)

    logger.info(
        "Embedded candidates in %.2fs (candidates=%d, newly_encoded=%d, vectors=%d)",
        time.perf_counter() - embed_started,
        len(candidate_papers),
        len(pending),
        len(paper_vectors)
    )

    # 3. Score and Rank candidates
    logger.info("search stage=scoring starting count=%d", len(candidate_papers))
    scoring_started = time.perf_counter()
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
    logger.info(
        "search stage=scoring elapsed=%.2fs count=%d",
        time.perf_counter() - scoring_started,
        len(scored_items)
    )
    
    # 4. Save SearchRun
    logger.info("search stage=db_save starting")
    save_started = time.perf_counter()
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
    logger.info(
        "search stage=db_save elapsed=%.2fs count=%d",
        time.perf_counter() - save_started,
        len(results)
    )
    
    return search_run, results, provider_status
