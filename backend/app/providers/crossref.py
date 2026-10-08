import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.providers.base import BaseProvider, ProviderPaper, ProviderAuthor, ProviderSubject
from app.core.config import settings

logger = logging.getLogger(__name__)

class CrossrefProvider(BaseProvider):
    def __init__(self):
        self.base_url = "https://api.crossref.org"
        self.headers = {
            "User-Agent": f"ResearchMatch/1.0 (mailto:{settings.CROSSREF_POLITE_EMAIL})"
        }

    @property
    def provider_name(self) -> str:
        return "crossref"

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(headers=self.headers, timeout=8.0) as client:
            try:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(f"Crossref API request error: {e}")
        return None

    def _parse_work(self, item: Dict[str, Any]) -> ProviderPaper:
        doi = item.get("DOI")
        titles = item.get("title", [])
        title = titles[0] if titles else "Untitled Work"
        
        abstract = item.get("abstract")
        
        # Authors
        authors = []
        for a in item.get("author", []):
            given = a.get("given", "")
            family = a.get("family", "")
            name = f"{given} {family}".strip() or a.get("name", "Unknown Author")
            orcid = a.get("ORCID", "").replace("http://orcid.org/", "").replace("https://orcid.org/", "") if a.get("ORCID") else None
            authors.append(ProviderAuthor(display_name=name, orcid=orcid))

        # Year
        created = item.get("created", {}).get("date-parts", [[]])[0]
        year = created[0] if created else None
        
        container = item.get("container-title", [])
        venue = container[0] if container else item.get("publisher")
        
        original_url = item.get("URL") or f"https://doi.org/{doi}"
        
        return ProviderPaper(
            provider="crossref",
            external_id=doi or title,
            canonical_title=title,
            abstract=abstract,
            doi=doi,
            publication_year=year,
            venue=venue,
            work_type=item.get("type"),
            authors=authors,
            original_url=original_url,
            citation_count=item.get("is-referenced-by-count", 0),
            raw_metadata=item,
            provenance_info={
                "source": "Crossref",
                "retrieved_via": "Crossref REST API v1"
            }
        )

    async def search_papers(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        open_access_only: bool = False,
        limit: int = 20,
    ) -> List[ProviderPaper]:
        params = {
            "query": query,
            "rows": min(limit, 20)
        }
        data = await self._make_request("/works", params=params)
        if not data or "message" not in data or "items" not in data["message"]:
            return []
            
        return [self._parse_work(item) for item in data["message"]["items"]]

    async def get_paper_by_id(self, external_id: str) -> Optional[ProviderPaper]:
        data = await self._make_request(f"/works/{external_id}", {})
        if not data or "message" not in data:
            return None
        return self._parse_work(data["message"])

    async def get_similar_papers(self, external_id: str, limit: int = 10) -> List[ProviderPaper]:
        paper = await self.get_paper_by_id(external_id)
        if not paper:
            return []
        return await self.search_papers(query=paper.canonical_title, limit=limit)
