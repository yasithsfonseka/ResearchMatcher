from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=2)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# Author & Subject & Source schemas
class AuthorOut(BaseModel):
    id: str
    display_name: str
    orcid: Optional[str] = None

    class Config:
        from_attributes = True

class SubjectOut(BaseModel):
    id: str
    provider: str
    external_id: str
    name: str
    level: str
    parent_id: Optional[str] = None

    class Config:
        from_attributes = True

class PaperSubjectOut(BaseModel):
    subject: SubjectOut
    assignment_method: str
    confidence: Optional[float] = None

    class Config:
        from_attributes = True

class SourceRecordOut(BaseModel):
    id: str
    provider: str
    external_id: str
    original_url: str
    open_access_url: Optional[str] = None
    access_status: Optional[str] = None
    citation_count: Optional[int] = None
    provider_updated_at: Optional[datetime] = None
    retrieved_at: datetime
    provenance_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class PaperOut(BaseModel):
    id: str
    canonical_title: str
    normalized_title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[str] = None
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    work_type: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime
    authors: List[AuthorOut] = []
    source_records: List[SourceRecordOut] = []
    subjects: List[PaperSubjectOut] = []
    has_abstract: bool = True

    class Config:
        from_attributes = True

class PaperResolveRequest(BaseModel):
    identifier: str # DOI, OpenAlex ID, or Semantic Scholar ID

# Search schemas
class SearchQueryRequest(BaseModel):
    research_title: str = Field(..., min_length=3, description="Proposed research title")
    research_description: Optional[str] = Field(None, description="Detailed research objectives or context")
    keywords: Optional[List[str]] = Field(default_factory=list)
    subject_filters: Optional[List[str]] = Field(default_factory=list)
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    open_access_only: bool = False
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

class SearchResultItem(BaseModel):
    paper: PaperOut
    rank: int
    keyword_score: float
    semantic_score: float
    subject_score: float
    final_score: float
    explanation: Dict[str, Any]

class SearchResponse(BaseModel):
    search_id: str
    total_count: int
    results: List[SearchResultItem]
    provider_status: Dict[str, Any]
    disclaimer: str = "Discovering papers from connected scholarly sources. Topic similarity does not establish that a paper supports a research claim."

class SearchRunOut(BaseModel):
    id: str
    research_title: str
    created_at: datetime
    keywords: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

# Collection schemas
class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class CollectionPaperCreate(BaseModel):
    paper_id: str
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    reading_status: str = Field("to_read", pattern="^(to_read|reading|reviewed)$")

class CollectionPaperUpdate(BaseModel):
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    reading_status: Optional[str] = Field(None, pattern="^(to_read|reading|reviewed)$")

class CollectionPaperOut(BaseModel):
    collection_id: str
    paper_id: str
    paper: PaperOut
    notes: Optional[str] = None
    tags: List[str] = []
    reading_status: str
    added_at: datetime

    class Config:
        from_attributes = True

class CollectionOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paper_count: int = 0
    papers: Optional[List[CollectionPaperOut]] = None

    class Config:
        from_attributes = True

# Feedback schema
class FeedbackCreate(BaseModel):
    search_run_id: str
    paper_id: str
    relevance_judgment: int = Field(..., ge=0, le=2) # 0, 1, 2
    comment: Optional[str] = None

class FeedbackOut(BaseModel):
    id: str
    user_id: str
    search_run_id: str
    paper_id: str
    relevance_judgment: int
    created_at: datetime

    class Config:
        from_attributes = True

# Job schema
class IngestionJobOut(BaseModel):
    id: str
    provider: str
    status: str
    progress: float
    error_summary: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
