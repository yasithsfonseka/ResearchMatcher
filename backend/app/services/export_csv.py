import csv
import io
from typing import List
from app.models.models import CollectionPaper

def sanitize_csv_field(val: str) -> str:
    """
    Prevent Spreadsheet Formula Injection (CSV Injection).
    If a field begins with '=', '+', '-', '@', '\t', or '\r', prepend a single quote (').
    """
    if not val:
        return ""
    str_val = str(val)
    if str_val.startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + str_val
    return str_val

def generate_collection_csv(papers: List[CollectionPaper]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    # Write Header
    writer.writerow([
        "Title",
        "DOI",
        "Publication Year",
        "Venue",
        "Authors",
        "Reading Status",
        "Tags",
        "Notes",
        "Source URL",
        "Added At"
    ])
    
    for entry in papers:
        p = entry.paper
        author_names = ", ".join([pa.author.display_name for pa in p.authors if pa.author]) if p.authors else "Unknown"
        tags_str = ", ".join(entry.tags) if entry.tags else ""
        source_url = p.source_records[0].original_url if p.source_records else (f"https://doi.org/{p.doi}" if p.doi else "")
        
        row = [
            sanitize_csv_field(p.canonical_title),
            sanitize_csv_field(p.doi or ""),
            sanitize_csv_field(str(p.publication_year or "")),
            sanitize_csv_field(p.venue or ""),
            sanitize_csv_field(author_names),
            sanitize_csv_field(entry.reading_status),
            sanitize_csv_field(tags_str),
            sanitize_csv_field(entry.notes or ""),
            sanitize_csv_field(source_url),
            sanitize_csv_field(entry.added_at.isoformat() if entry.added_at else "")
        ]
        writer.writerow(row)
        
    return output.getvalue()
