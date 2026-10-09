import hashlib
import logging
from typing import List, Optional
import numpy as np
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import Paper, PaperEmbedding

logger = logging.getLogger(__name__)

# Lazy loader for sentence transformer model
_model_instance = None
_model_load_attempted = False

def get_embedding_model():
    global _model_instance, _model_load_attempted
    if not _model_load_attempted:
        _model_load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.warning(f"SentenceTransformer model unavailable ({e}). Using deterministic fallback embeddings.")
            _model_instance = None
    return _model_instance

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _fallback_vector(text: str) -> List[float]:
    # Deterministic normalized vector if model loading/encoding fails
    rng = np.random.RandomState(seed=int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16))
    vec = rng.randn(settings.EMBEDDING_DIMENSION).astype(np.float32)
    norm = np.linalg.norm(vec)
    return (vec / (norm + 1e-9)).tolist()

def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embed many texts with a single model.encode call, preserving input order."""
    if not texts:
        return []
    try:
        model = get_embedding_model()
        if model is not None:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return [e.tolist() for e in embeddings]
    except Exception as e:
        logger.warning(f"Model encode failed ({e}). Using fallback vectors.")

    return [_fallback_vector(t) for t in texts]

def generate_embedding(text: str) -> List[float]:
    return embed_texts([text])[0]

def embed_paper(db: Session, paper: Paper) -> Optional[PaperEmbedding]:
    try:
        text_content = f"{paper.canonical_title}. {paper.abstract or ''}".strip()
        if not text_content:
            return None
            
        input_hash = compute_text_hash(text_content)
        
        # Check if already embedded with current model & hash
        existing = db.query(PaperEmbedding).filter(
            PaperEmbedding.paper_id == paper.id,
            PaperEmbedding.model_id == settings.EMBEDDING_MODEL_NAME,
            PaperEmbedding.input_hash == input_hash
        ).first()
        
        if existing:
            return existing
            
        vec = generate_embedding(text_content)
        if not vec:
            return None
            
        emb = PaperEmbedding(
            paper_id=paper.id,
            model_id=settings.EMBEDDING_MODEL_NAME,
            model_revision="v1",
            input_hash=input_hash,
            embedding=vec
        )
        db.add(emb)
        db.commit()
        db.refresh(emb)
        return emb
    except Exception as e:
        logger.error(f"Error embedding paper {paper.id}: {e}")
        db.rollback()
        return None
