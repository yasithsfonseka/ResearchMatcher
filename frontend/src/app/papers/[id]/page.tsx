'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Paper, apiFetch } from '@/lib/api';
import { BookOpen, ExternalLink, Bookmark, Sparkles, Award, Tag, AlertCircle, ArrowLeft, RefreshCw, FileText } from 'lucide-react';
import SaveToCollectionModal from '@/components/SaveToCollectionModal';

export default function PaperDetailsPage() {
  const params = useParams();
  const paperId = params.id as string;

  const [paper, setPaper] = useState<Paper | null>(null);
  const [similarPapers, setSimilarPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (paperId) {
      fetchPaperDetails();
    }
  }, [paperId]);

  const fetchPaperDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<Paper>(`/papers/${paperId}`);
      setPaper(data);
      fetchSimilarPapers(data.id);
    } catch (e: any) {
      setError(e.message || 'Paper not found');
    } finally {
      setLoading(false);
    }
  };

  const fetchSimilarPapers = async (id: string) => {
    setLoadingSimilar(true);
    try {
      const simData = await apiFetch<Paper[]>(`/papers/${id}/similar?limit=6`);
      setSimilarPapers(simData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSimilar(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
        <p className="text-xs text-gray-400">Loading paper metadata and provenance...</p>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="max-w-3xl mx-auto py-20 px-4 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Paper Details Not Found</h2>
        <p className="text-xs text-gray-400">{error}</p>
        <Link href="/" className="inline-flex items-center space-x-1.5 text-xs text-blue-400 hover:underline">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Search</span>
        </Link>
      </div>
    );
  }

  const mainSource = paper.source_records[0];
  const originalUrl = mainSource?.original_url || (paper.doi ? `https://doi.org/${paper.doi}` : '#');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <Link href="/" className="inline-flex items-center space-x-1.5 text-xs font-medium text-gray-400 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Discovery</span>
      </Link>

      {/* Main Header Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {paper.work_type && (
              <span className="px-2.5 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300 font-semibold uppercase tracking-wider">
                {paper.work_type}
              </span>
            )}
            {paper.publication_year && (
              <span className="px-2.5 py-0.5 rounded bg-gray-800 text-gray-300 font-medium">
                Published {paper.publication_year}
              </span>
            )}
            {mainSource?.citation_count !== undefined && (
              <span className="px-2.5 py-0.5 rounded bg-amber-950/60 border border-amber-900 text-amber-300 font-medium flex items-center space-x-1">
                <Award className="w-3.5 h-3.5" />
                <span>{mainSource.citation_count} Citations</span>
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white leading-tight">{paper.canonical_title}</h1>

          <p className="text-sm text-gray-300">
            <strong className="text-white">Authors:</strong>{' '}
            {paper.authors.length > 0 ? paper.authors.map((a) => a.display_name).join(', ') : 'Unknown'}
          </p>

          {paper.venue && (
            <p className="text-xs text-gray-400">
              <strong className="text-gray-300">Venue / Publisher:</strong> {paper.venue}
            </p>
          )}

          {paper.doi && (
            <p className="text-xs text-gray-400">
              <strong className="text-gray-300">DOI:</strong> {paper.doi}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-gray-800">
          <a
            href={originalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors shadow-lg shadow-blue-600/20"
          >
            <span>Verify Original Publication</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          {mainSource?.open_access_url && (
            <a
              href={mainSource.open_access_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors"
            >
              <span>Open Access Full PDF</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors border border-gray-700"
          >
            <Bookmark className="w-3.5 h-3.5 text-purple-400" />
            <span>Save to Literature Collection</span>
          </button>
        </div>

        {/* Abstract */}
        <div className="space-y-2 pt-2">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Abstract</h3>
          {paper.abstract ? (
            <p className="text-xs text-gray-300 leading-relaxed bg-gray-950 p-4 rounded-xl border border-gray-800">
              {paper.abstract}
            </p>
          ) : (
            <div className="bg-amber-950/30 border border-amber-900/50 p-4 rounded-xl text-amber-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>Abstract not supplied by scholarly provider. Only title and subjects recorded.</span>
            </div>
          )}
        </div>

        {/* Subjects & Provenance */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-800">
          <div>
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <Tag className="w-3.5 h-3.5 text-blue-400" />
              <span>Subject Taxonomy</span>
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {paper.subjects.length > 0 ? (
                paper.subjects.map((ps, idx) => (
                  <span key={idx} className="text-xs px-2.5 py-1 rounded bg-gray-950 border border-gray-800 text-gray-300">
                    {ps.subject.name} ({ps.subject.level})
                  </span>
                ))
              ) : (
                <span className="text-xs text-gray-500">Unclassified</span>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              <span>Source Provenance</span>
            </h4>
            <div className="bg-gray-950 p-3 rounded-lg border border-gray-800 text-xs space-y-1">
              <p className="text-gray-300">
                <strong className="text-white">Provider:</strong> {mainSource?.provider || 'OpenAlex'}
              </p>
              <p className="text-gray-400">
                <strong className="text-gray-300">Retrieved:</strong>{' '}
                {mainSource ? new Date(mainSource.retrieved_at).toLocaleDateString() : 'Recent'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Similar Papers Section */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <span>Similar Paper Discoveries</span>
        </h2>

        {loadingSimilar ? (
          <p className="text-xs text-gray-500 py-6">Finding similar works via pgvector embedding similarity...</p>
        ) : similarPapers.length === 0 ? (
          <p className="text-xs text-gray-500">No similar papers indexed yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {similarPapers.map((sim) => (
              <div key={sim.id} className="bg-gray-900 border border-gray-800 p-4 rounded-xl space-y-2 hover:border-gray-700 transition-colors">
                <Link href={`/papers/${sim.id}`} className="text-sm font-bold text-white hover:text-blue-400 line-clamp-2">
                  {sim.canonical_title}
                </Link>
                <p className="text-xs text-gray-400">
                  {sim.authors.map((a) => a.display_name).join(', ')} ({sim.publication_year || 'N/A'})
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <SaveToCollectionModal
        paperId={paper.id}
        paperTitle={paper.canonical_title}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
