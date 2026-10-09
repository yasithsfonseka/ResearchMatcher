'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { SearchResponse, SearchResultItem, apiFetch } from '@/lib/api';
import PaperCard from '@/components/PaperCard';
import { Search, SlidersHorizontal, ArrowUpDown, AlertCircle, RefreshCw, CheckCircle2, Info } from 'lucide-react';

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const q = searchParams.get('q') || '';
  const desc = searchParams.get('desc') || '';
  const kw = searchParams.get('kw') || '';
  const y_min = searchParams.get('y_min') || '';
  const y_max = searchParams.get('y_max') || '';
  const oa = searchParams.get('oa') === 'true';

  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'relevance' | 'year' | 'citations'>('relevance');

  useEffect(() => {
    if (!q) {
      router.push('/');
      return;
    }
    executeSearchQuery();
  }, [q, desc, kw, y_min, y_max, oa]);

  const executeSearchQuery = async () => {
    setLoading(true);
    setError(null);

    const keywordsList = kw
      .split(',')
      .map((k) => k.trim())
      .filter((k) => k.length > 0);

    const parsedYMin = y_min && !isNaN(parseInt(y_min, 10)) ? parseInt(y_min, 10) : undefined;
    const parsedYMax = y_max && !isNaN(parseInt(y_max, 10)) ? parseInt(y_max, 10) : undefined;

    try {
      const data = await apiFetch<SearchResponse>('/search', {
        method: 'POST',
        body: JSON.stringify({
          research_title: q,
          research_description: desc || undefined,
          keywords: keywordsList,
          year_min: parsedYMin,
          year_max: parsedYMax,
          open_access_only: oa,
          limit: 30,
        }),
      });
      setResponse(data);
    } catch (e: any) {
      setError(e.message || 'Failed to retrieve search results from scholarly providers.');
    } finally {
      setLoading(false);
    }
  };

  const getSortedResults = (): SearchResultItem[] => {
    if (!response) return [];
    const list = [...response.results];
    if (sortBy === 'year') {
      return list.sort((a, b) => (b.paper.publication_year || 0) - (a.paper.publication_year || 0));
    } else if (sortBy === 'citations') {
      return list.sort((a, b) => {
        const cA = a.paper.source_records[0]?.citation_count || 0;
        const cB = b.paper.source_records[0]?.citation_count || 0;
        return cB - cA;
      });
    }
    return list;
  };

  const sortedResults = getSortedResults();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Query Header Summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-4">
          <div>
            <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">Search Query Target</span>
            <h1 className="text-xl sm:text-2xl font-bold text-white mt-1">{q}</h1>
            {desc && <p className="text-xs text-gray-400 mt-1 max-w-3xl line-clamp-2">{desc}</p>}
          </div>

          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold rounded-lg shrink-0 transition-colors flex items-center space-x-1.5"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Modify Query</span>
          </button>
        </div>

        {/* Provider Status Indicator */}
        {response && (
          <div className="flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center space-x-3 text-gray-400">
              <span className="flex items-center space-x-1 text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>OpenAlex REST API Connected</span>
              </span>
              <span className="text-gray-600">•</span>
              <span>Retrieved {response.total_count} candidate papers</span>
            </div>

            {/* Sorting controls */}
            <div className="flex items-center space-x-2">
              <ArrowUpDown className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-400">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-gray-950 border border-gray-800 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="relevance">Hybrid Relevance</option>
                <option value="year">Publication Year (Newest)</option>
                <option value="citations">Citation Count</option>
              </select>
            </div>
          </div>
        )}

        {sortBy === 'citations' && (
          <div className="bg-amber-950/30 border border-amber-900/50 p-2.5 rounded-lg text-amber-300 text-[11px] flex items-center space-x-2">
            <Info className="w-4 h-4 shrink-0" />
            <span>Citation count reflects paper visibility and age, not methodological quality or evidence support.</span>
          </div>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="py-20 text-center space-y-4">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
          <p className="text-sm text-gray-400 font-medium">
            Fetching scholarly works from connected sources & computing vector embeddings...
          </p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="bg-red-950/60 border border-red-800 p-6 rounded-xl text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
          <p className="text-sm font-semibold text-red-200">{error}</p>
          <button
            onClick={executeSearchQuery}
            className="px-4 py-2 bg-red-800 hover:bg-red-700 text-white rounded-lg text-xs font-semibold"
          >
            Retry Provider Request
          </button>
        </div>
      )}

      {/* Results List */}
      {!loading && !error && response && (
        <div className="space-y-6">
          {sortedResults.length === 0 ? (
            <div className="bg-gray-900 border border-gray-800 p-12 rounded-xl text-center space-y-3">
              <Search className="w-10 h-10 text-gray-600 mx-auto" />
              <h3 className="text-base font-semibold text-white">No matching papers found</h3>
              <p className="text-xs text-gray-400 max-w-md mx-auto">
                Try broadening your title terms, removing restrictive year filters, or adding alternate keywords.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {sortedResults.map((item) => (
                <PaperCard key={item.paper.id} item={item} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="py-20 text-center text-sm text-gray-400">Loading search...</div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}
