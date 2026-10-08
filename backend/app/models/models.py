import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Table, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.config import settings

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    search_runs = relationship("SearchRun", back_populates="user")
    feedback = relationship("RelevanceFeedback", back_populates="user")

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    canonical_title = Column(Text, nullable=False)
    normalized_title = Column(Text, nullable=False, index=True)
    abstract = Column(Text, nullable=True)
    doi = Column(String(255), unique=True, nullable=True, index=True)
    publication_date = Column(String(50), nullable=True)
    publication_year = Column(Integer, nullable=True, index=True)
    venue = Column(String(500), nullable=True)
    work_type = Column(String(100), nullable=True)
    language = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    source_records = relationship("PaperSourceRecord", back_populates="paper", cascade="all, delete-orphan")
    subjects = relationship("PaperSubject", back_populates="paper", cascade="all, delete-orphan")
    embeddings = relationship("PaperEmbedding", back_populates="paper", cascade="all, delete-orphan")
    collection_entries = relationship("CollectionPaper", back_populates="paper", cascade="all, delete-orphan")
    search_results = relationship("SearchResult", back_populates="paper", cascade="all, delete-orphan")

class Author(Base):
    __tablename__ = "authors"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    display_name = Column(String(255), nullable=False, index=True)
    orcid = Column(String(100), unique=True, nullable=True, index=True)
    
    papers = relationship("PaperAuthor", back_populates="author")

class PaperAuthor(Base):
    __tablename__ = "paper_authors"
    
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True)
    author_id = Column(String(36), ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)
    author_order = Column(Integer, default=0, nullable=False)
    
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")

class PaperSourceRecord(Base):
    __tablename__ = "paper_source_records"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(100), nullable=False, index=True) # openalex, semanticscholar, crossref
    external_id = Column(String(255), nullable=False, index=True)
    original_url = Column(Text, nullable=False)
    open_access_url = Column(Text, nullable=True)
    access_status = Column(String(100), nullable=True)
    citation_count = Column(Integer, nullable=True)
    provider_updated_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    provenance_info = Column(JSON, nullable=True)
    
    paper = relationship("Paper", back_populates="source_records")
    
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_provider_external_id"),
    )

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    level = Column(String(50), nullable=False) # Domain, Field, Subfield, Topic
    parent_id = Column(String(36), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    
    parent = relationship("Subject", remote_side=[id], backref="children")
    paper_assignments = relationship("PaperSubject", back_populates="subject", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_subject_provider_external"),
    )

class PaperSubject(Base):
    __tablename__ = "paper_subjects"
    
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True)
    assignment_method = Column(String(50), nullable=False, default="provider_supplied") # provider_supplied, model_predicted, user_added
    confidence = Column(Float, nullable=True)
    
    paper = relationship("Paper", back_populates="subjects")
    subject = relationship("Subject", back_populates="paper_assignments")

class PaperEmbedding(Base):
    __tablename__ = "paper_embeddings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(255), nullable=False)
    model_revision = Column(String(100), nullable=False, default="v1")
    input_hash = Column(String(64), nullable=False)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    paper = relationship("Paper", back_populates="embeddings")
    
    __table_args__ = (
        UniqueConstraint("paper_id", "model_id", "input_hash", name="uq_paper_model_hash"),
    )

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="collections")
    papers = relationship("CollectionPaper", back_populates="collection", cascade="all, delete-orphan")

class CollectionPaper(Base):
    __tablename__ = "collection_papers"
    
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list, nullable=False) # list of tag strings
    reading_status = Column(String(50), default="to_read", nullable=False) # to_read, reading, reviewed
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    collection = relationship("Collection", back_populates="papers")
    paper = relationship("Paper", back_populates="collection_entries")

class SearchRun(Base):
    __tablename__ = "search_runs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    research_title = Column(Text, nullable=False)
    research_description = Column(Text, nullable=True) # Subject to privacy retention policy
    keywords = Column(JSON, nullable=True) # list of keywords
    subject_filters = Column(JSON, nullable=True)
    year_min = Column(Integer, nullable=True)
    year_max = Column(Integer, nullable=True)
    open_access_only = Column(Boolean, default=False)
    ranking_config = Column(JSON, nullable=True)
    provider_status = Column(JSON, nullable=True) # status of openalex, semanticscholar, crossref queries
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    user = relationship("User", back_populates="search_runs")
    results = relationship("SearchResult", back_populates="search_run", cascade="all, delete-orphan")
    feedback = relationship("RelevanceFeedback", back_populates="search_run", cascade="all, delete-orphan")

class SearchResult(Base):
    __tablename__ = "search_results"
    
    search_run_id = Column(String(36), ForeignKey("search_runs.id", ondelete="CASCADE"), primary_key=True)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), primary_key=True)
    rank = Column(Integer, nullable=False)
    keyword_score = Column(Float, nullable=False, default=0.0)
    semantic_score = Column(Float, nullable=False, default=0.0)
    subject_score = Column(Float, nullable=False, default=0.0)
    final_score = Column(Float, nullable=False, default=0.0)
    explanation_metadata = Column(JSON, nullable=True)
    
    search_run = relationship("SearchRun", back_populates="results")
    paper = relationship("Paper", back_populates="search_results")

class RelevanceFeedback(Base):
    __tablename__ = "relevance_feedback"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    search_run_id = Column(String(36), ForeignKey("search_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    relevance_judgment = Column(Integer, nullable=False) # 0: Not relevant, 1: Partially relevant, 2: Highly relevant
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="feedback")
    search_run = relationship("SearchRun", back_populates="feedback")

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending") # pending, processing, completed, failed
    progress = Column(Float, default=0.0, nullable=False) # 0.0 to 100.0
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
