export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface Author {
  id: string;
  display_name: string;
  orcid?: string;
}

export interface Subject {
  id: string;
  provider: string;
  external_id: string;
  name: string;
  level: string;
  parent_id?: string;
}

export interface PaperSubject {
  subject: Subject;
  assignment_method: string;
  confidence?: number;
}

export interface SourceRecord {
  id: string;
  provider: string;
  external_id: string;
  original_url: string;
  open_access_url?: string;
  access_status?: string;
  citation_count?: number;
  retrieved_at: string;
}

export interface Paper {
  id: string;
  canonical_title: string;
  normalized_title: string;
  abstract?: string;
  doi?: string;
  publication_date?: string;
  publication_year?: number;
  venue?: string;
  work_type?: string;
  language?: string;
  created_at: string;
  authors: Author[];
  source_records: SourceRecord[];
  subjects: PaperSubject[];
  has_abstract: boolean;
}

export interface SearchResultItem {
  paper: Paper;
  rank: number;
  keyword_score: number;
  semantic_score: number;
  subject_score: number;
  final_score: number;
  explanation: {
    summary: string;
    shared_title_keywords?: string[];
    shared_abstract_keywords?: string[];
    matching_subjects?: string[];
    has_abstract: boolean;
    missing_metadata_note?: string;
    component_scores?: {
      keyword: number;
      semantic: number;
      subject: number;
      final_relevance_score: number;
    };
    score_disclaimer: string;
  };
}

export interface SearchResponse {
  search_id: string;
  total_count: number;
  results: SearchResultItem[];
  provider_status: Record<string, any>;
  disclaimer: string;
}

export interface SearchQueryRequest {
  research_title: string;
  research_description?: string;
  keywords?: string[];
  subject_filters?: string[];
  year_min?: number;
  year_max?: number;
  open_access_only?: boolean;
  limit?: number;
  offset?: number;
}

export interface CollectionPaper {
  collection_id: string;
  paper_id: string;
  paper: Paper;
  notes?: string;
  tags: string[];
  reading_status: 'to_read' | 'reading' | 'reviewed';
  added_at: string;
}

export interface Collection {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  paper_count: number;
  papers?: CollectionPaper[];
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// Fetch helper with token
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'API request failed');
  }

  return res.json();
}
