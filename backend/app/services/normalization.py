import re
from typing import Optional

def normalize_title(title: str) -> str:
    if not title:
        return ""
    # Lowercase, replace non-alphanumeric chars with spaces, collapse spaces
    cleaned = re.sub(r"[^\w\s]", " ", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()

def normalize_doi(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    cleaned = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip().lower()
    return cleaned if cleaned else None
