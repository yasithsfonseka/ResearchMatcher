import re
from typing import List, Dict, Any, Optional
from app.models.models import Paper

def generate_match_explanation(
    research_title: str,
    research_description: Optional[str],
    keywords: Optional[List[str]],
    paper: Paper,
    keyword_score: float,
    semantic_score: float,
    subject_score: float,
    final_score: float
) -> Dict[str, Any]:
    query_terms = set(re.findall(r"\w+", f"{research_title} {research_description or ''}".lower()))
    if keywords:
        query_terms.update([k.lower() for k in keywords])
        
    paper_title_terms = set(re.findall(r"\w+", paper.canonical_title.lower()))
    paper_abstract_terms = set(re.findall(r"\w+", (paper.abstract or "").lower()))
    
    # Exclude common stop words
    stopwords = {"a", "an", "the", "in", "on", "of", "and", "or", "for", "to", "with", "is", "at", "by", "from", "that", "this", "it", "as", "be", "are"}
    meaningful_query_terms = query_terms - stopwords
    
    matching_title_keywords = sorted(list(meaningful_query_terms.intersection(paper_title_terms)))
    matching_abstract_keywords = sorted(list(meaningful_query_terms.intersection(paper_abstract_terms)))
    
    # Extract matching subjects/topics
    matching_subjects = []
    if paper.subjects:
        for ps in paper.subjects:
            if ps.subject:
                s_name = ps.subject.name
                if any(t in s_name.lower() for t in meaningful_query_terms if len(t) > 3):
                    matching_subjects.append(s_name)

    # Build evidence sentences
    reasons = []
    if matching_title_keywords:
        reasons.append(f"Title overlaps on key concepts: {', '.join(matching_title_keywords[:4])}.")
    if matching_abstract_keywords:
        reasons.append(f"Abstract discusses terms: {', '.join(matching_abstract_keywords[:4])}.")
    if matching_subjects:
        reasons.append(f"Categorized under relevant topics: {', '.join(matching_subjects[:3])}.")
        
    has_abstract = bool(paper.abstract and paper.abstract.strip())
    missing_metadata_note = None if has_abstract else "Important metadata missing: Abstract not supplied by source. Match based on title and subjects."
    
    summary_text = " ".join(reasons) if reasons else "Matches broad subject area and search terms."
    
    return {
        "summary": summary_text,
        "shared_title_keywords": matching_title_keywords[:6],
        "shared_abstract_keywords": matching_abstract_keywords[:6],
        "matching_subjects": matching_subjects[:4],
        "has_abstract": has_abstract,
        "missing_metadata_note": missing_metadata_note,
        "component_scores": {
            "keyword": round(keyword_score, 3),
            "semantic": round(semantic_score, 3),
            "subject": round(subject_score, 3),
            "final_relevance_score": round(final_score, 3)
        },
        "score_disclaimer": "Relevance score is a ranking signal based on topic and keyword similarity. It does not establish methodological quality or evidence support for a claim."
    }
