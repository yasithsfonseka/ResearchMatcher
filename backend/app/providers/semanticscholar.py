import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.providers.base import BaseProvider, ProviderPaper, ProviderAuthor, ProviderSubject
from app.core.config import settings

logger = logging.getLogger(__name__)

class SemanticScholarProvider(BaseProvider):
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.headers = {}
        if settings.SEMANTIC_SCHOLAR_API_KEY:
            self.headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

    @property
    def provider_name(self) -> str:
        return "semanticscholar"

    async def _make_request(self, endpoint: str, params: Dict[str, Any], retries: int = 2) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        delay = 0.5
        async with httpx.AsyncClient(headers=self.headers, timeout=8.0) as client:
            for attempt in range(retries):
                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        if attempt == retries - 1:
                            return None
                        await asyncio.sleep(delay)
                except Exception as e:
                    logger.warning(f"Semantic Scholar request failed: {e}")
                    if attempt == retries - 1:
                        return None
                    await asyncio.sleep(delay)
        return None

    def _parse_paper(self, item: Dict[str, Any]) -> ProviderPaper:
        paper_id = item.get("paperId", "")
        external_ids = item.get("externalIds", {}) or {}
        doi = external_ids.get("DOI")
        
        title = item.get("title", "Untitled")
        abstract = item.get("abstract")
        year = item.get("year")
        venue = item.get("venue")
        
        authors = []
        for auth in item.get("authors", []):
            name = auth.get("name")
            if name:
                authors.append(ProviderAuthor(display_name=name))
                
        subjects = []
        for s in item.get("sFieldsOfStudy", []) or []:
            subjects.append(ProviderSubject(
                external_id=s.lower(),
                name=s,
                level="Field"
            ))

        url = item.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}"
        oa_info = item.get("openAccessPdf") or {}
        oa_url = oa_info.get("url")
        
        return ProviderPaper(
            provider="semanticscholar",
            external_id=paper_id,
            canonical_title=title,
            abstract=abstract,
            doi=doi,
            publication_year=year,
            venue=venue,
            authors=authors,
            subjects=subjects,
            original_url=url,
            open_access_url=oa_url,
            citation_count=item.get("citationCount", 0),
            raw_metadata=item,
            provenance_info={
                "source": "Semantic Scholar",
                "retrieved_via": "Semantic Scholar Academic Graph API v1"
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
            "limit": min(limit, 20),
            "fields": "paperId,externalIds,url,title,abstract,venue,year,authors,citationCount,openAccessPdf,sFieldsOfStudy"
        }
        if year_min and year_max:
            params["year"] = f"{year_min}-{year_max}"
        elif year_min:
            params["year"] = f"{year_min}-"

        data = await self._make_request("/paper/search", params=params)
        if not data or "data" not in data:
            return []
            
        return [self._parse_paper(p) for p in data["data"]]

    async def get_paper_by_id(self, external_id: str) -> Optional[ProviderPaper]:
        endpoint = f"/paper/{external_id}"
        params = {"fields": "paperId,externalIds,url,title,abstract,venue,year,authors,citationCount,openAccessPdf,sFieldsOfStudy"}
        data = await self._make_request(endpoint, params=params)
        if not data:
            return None
        return self._parse_paper(data)

    async def get_similar_papers(self, external_id: str, limit: int = 10) -> List[ProviderPaper]:
        # Semantic Scholar has a recommendations API: /recommendations/v1/papers/forpaper/{paper_id}
        url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{external_id}"
        params = {
            "limit": min(limit, 20),
            "fields": "paperId,externalIds,url,title,abstract,venue,year,authors,citationCount,openAccessPdf,sFieldsOfStudy"
        }
        async with httpx.AsyncClient(headers=self.headers, timeout=8.0) as client:
            try:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    return [self._parse_paper(p) for p in data.get("recommendedPapers", [])]
            except Exception as e:
                logger.warning(f"Semantic Scholar recommendations failed: {e}")
        return []
