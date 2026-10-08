import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.providers.base import BaseProvider, ProviderPaper, ProviderAuthor, ProviderSubject
from app.core.config import settings

logger = logging.getLogger(__name__)

def reconstruct_abstract(abstract_inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """
    OpenAlex stores abstracts as an inverted index: {"word": [position1, position2]}.
    Reconstruct plain text from this index.
    """
    if not abstract_inverted_index:
        return None
    
    try:
        word_positions = []
        for word, positions in abstract_inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        
        # Sort by position
        word_positions.sort(key=lambda x: x[0])
        return " ".join([word for _, word in word_positions])
    except Exception as e:
        logger.warning(f"Failed to reconstruct abstract from inverted index: {e}")
        return None

def clean_doi(doi_url: Optional[str]) -> Optional[str]:
    if not doi_url:
        return None
    cleaned = doi_url.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
    return cleaned if cleaned else None

class OpenAlexProvider(BaseProvider):
    def __init__(self):
        self.base_url = "https://api.openalex.org"
        self.headers = {
            "User-Agent": f"ResearchMatch/1.0 (mailto:{settings.OPENALEX_POLITE_EMAIL})"
        }
        if settings.OPENALEX_API_KEY:
            self.headers["api_key"] = settings.OPENALEX_API_KEY

    @property
    def provider_name(self) -> str:
        return "openalex"

    async def _make_request(self, endpoint: str, params: Dict[str, Any], retries: int = 3) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        delay = 0.5
        
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            for attempt in range(retries):
                try:
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429: # Rate limited
                        logger.warning(f"OpenAlex rate limited (429). Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"OpenAlex returned status {response.status_code}: {response.text}")
                        if attempt == retries - 1:
                            return None
                        await asyncio.sleep(delay)
                        delay *= 2
                except (httpx.RequestError, httpx.TimeoutException) as exc:
                    logger.warning(f"OpenAlex request error on attempt {attempt+1}: {exc}")
                    if attempt == retries - 1:
                        return None
                    await asyncio.sleep(delay)
                    delay *= 2
        return None

    def _parse_work(self, item: Dict[str, Any]) -> ProviderPaper:
        ext_id = item.get("id", "").replace("https://openalex.org/", "")
        doi = clean_doi(item.get("doi"))
        title = item.get("title") or item.get("display_name") or "Untitled Work"
        abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
        
        # Authors
        authors: List[ProviderAuthor] = []
        for idx, authorship in enumerate(item.get("authorships", [])):
            author_data = authorship.get("author", {})
            name = author_data.get("display_name")
            orcid = author_data.get("orcid", "").replace("https://orcid.org/", "") if author_data.get("orcid") else None
            if name:
                authors.append(ProviderAuthor(display_name=name, orcid=orcid))
        
        # Subjects / Topics
        subjects: List[ProviderSubject] = []
        
        # Primary topic & topics
        primary_topic = item.get("primary_topic")
        if primary_topic:
            topic_id = primary_topic.get("id", "").replace("https://openalex.org/", "")
            subfield = primary_topic.get("subfield", {})
            field = primary_topic.get("field", {})
            domain = primary_topic.get("domain", {})
            
            subjects.append(ProviderSubject(
                external_id=topic_id,
                name=primary_topic.get("display_name", "Unknown Topic"),
                level="Topic",
                parent_external_id=subfield.get("id", "").replace("https://openalex.org/", "") if subfield.get("id") else None,
                confidence=1.0
            ))
            
            if subfield.get("id"):
                subjects.append(ProviderSubject(
                    external_id=subfield.get("id", "").replace("https://openalex.org/", ""),
                    name=subfield.get("display_name", "Subfield"),
                    level="Subfield",
                    parent_external_id=field.get("id", "").replace("https://openalex.org/", "") if field.get("id") else None
                ))
            if field.get("id"):
                subjects.append(ProviderSubject(
                    external_id=field.get("id", "").replace("https://openalex.org/", ""),
                    name=field.get("display_name", "Field"),
                    level="Field",
                    parent_external_id=domain.get("id", "").replace("https://openalex.org/", "") if domain.get("id") else None
                ))
            if domain.get("id"):
                subjects.append(ProviderSubject(
                    external_id=domain.get("id", "").replace("https://openalex.org/", ""),
                    name=domain.get("display_name", "Domain"),
                    level="Domain"
                ))
        
        # Additional concepts as fallback
        for concept in item.get("concepts", []):
            cid = concept.get("id", "").replace("https://openalex.org/", "")
            cname = concept.get("display_name")
            score = concept.get("score")
            if cid and cname and score and score >= 0.3:
                subjects.append(ProviderSubject(
                    external_id=cid,
                    name=cname,
                    level=f"Level_{concept.get('level', 0)}",
                    confidence=score
                ))

        # Venue / Primary Location
        primary_loc = item.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        venue = source.get("display_name") or item.get("publisher")
        
        # Access URLs
        original_url = primary_loc.get("landing_page_url") or item.get("doi") or f"https://openalex.org/{ext_id}"
        open_access_info = item.get("open_access") or {}
        oa_url = open_access_info.get("oa_url") or primary_loc.get("pdf_url")
        oa_status = open_access_info.get("oa_status")
        
        return ProviderPaper(
            provider="openalex",
            external_id=ext_id,
            canonical_title=title,
            abstract=abstract,
            doi=doi,
            publication_date=item.get("publication_date"),
            publication_year=item.get("publication_year"),
            venue=venue,
            work_type=item.get("type"),
            language=item.get("language"),
            authors=authors,
            subjects=subjects,
            original_url=original_url,
            open_access_url=oa_url,
            access_status=oa_status,
            citation_count=item.get("cited_by_count", 0),
            raw_metadata=item,
            provenance_info={
                "source": "OpenAlex",
                "retrieved_via": "OpenAlex REST API v1",
                "openalex_id": item.get("id")
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
        full_query = query
        if keywords:
            full_query += " " + " ".join(keywords)
            
        params: Dict[str, Any] = {
            "search": full_query,
            "per_page": min(limit, 50),
        }
        
        filters = []
        if year_min and year_max:
            filters.append(f"publication_year:{year_min}-{year_max}")
        elif year_min:
            filters.append(f"publication_year:>{year_min - 1}")
        elif year_max:
            filters.append(f"publication_year:<{year_max + 1}")
            
        if open_access_only:
            filters.append("is_oa:true")
            
        if filters:
            params["filter"] = ",".join(filters)

        data = await self._make_request("/works", params=params)
        if not data or "results" not in data:
            return []
            
        results: List[ProviderPaper] = []
        for item in data["results"]:
            try:
                results.append(self._parse_work(item))
            except Exception as e:
                logger.error(f"Error parsing OpenAlex work item: {e}")
                
        return results

    async def get_paper_by_id(self, external_id: str) -> Optional[ProviderPaper]:
        # Accepts W123456789 or DOI
        if external_id.startswith("10."):
            endpoint = f"/works/https://doi.org/{external_id}"
        else:
            endpoint = f"/works/{external_id}"
            
        data = await self._make_request(endpoint, {})
        if not data:
            return None
        return self._parse_work(data)

    async def get_similar_papers(self, external_id: str, limit: int = 10) -> List[ProviderPaper]:
        # Fetch target paper first
        paper = await self.get_paper_by_id(external_id)
        if not paper:
            return []
        
        # OpenAlex exposes related works IDs
        related_ids = paper.raw_metadata.get("related_works", [])
        if not related_ids:
            # Fallback to search by title
            return await self.search_papers(query=paper.canonical_title, limit=limit)
        
        # Batch query up to `limit` related works
        target_openalex_ids = [r.replace("https://openalex.org/", "") for r in related_ids[:limit]]
        params = {
            "filter": f"openalex:{'|'.join(target_openalex_ids)}",
            "per_page": limit
        }
        data = await self._make_request("/works", params=params)
        if not data or "results" not in data:
            return []
            
        return [self._parse_work(item) for item in data["results"]]
