from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ProviderAuthor(BaseModel):
    display_name: str
    orcid: Optional[str] = None

class ProviderSubject(BaseModel):
    external_id: str
    name: str
    level: str # Domain, Field, Subfield, Topic
    parent_external_id: Optional[str] = None
    confidence: Optional[float] = None

class ProviderPaper(BaseModel):
    provider: str
    external_id: str
    canonical_title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[str] = None
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    work_type: Optional[str] = None
    language: Optional[str] = None
    authors: List[ProviderAuthor] = Field(default_factory=list)
    subjects: List[ProviderSubject] = Field(default_factory=list)
    original_url: str
    open_access_url: Optional[str] = None
    access_status: Optional[str] = None
    citation_count: Optional[int] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance_info: Dict[str, Any] = Field(default_factory=dict)

class BaseProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def search_papers(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        open_access_only: bool = False,
        limit: int = 20,
    ) -> List[ProviderPaper]:
        pass

    @abstractmethod
    async def get_paper_by_id(self, external_id: str) -> Optional[ProviderPaper]:
        pass

    @abstractmethod
    async def get_similar_papers(self, external_id: str, limit: int = 10) -> List[ProviderPaper]:
        pass
