'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ExternalLink, Bookmark, AlertCircle, Info, ChevronDown, ChevronUp, Tag, Award, BookOpen } from 'lucide-react';
import { Paper, SearchResultItem } from '@/lib/api';
import SaveToCollectionModal from './SaveToCollectionModal';

interface PaperCardProps {
  item: SearchResultItem;
}

export default function PaperCard({ item }: PaperCardProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const paper = item.paper;

  const mainSource = paper.source_records[0];
  const originalUrl = mainSource?.original_url || (paper.doi ? `https://doi.org/${paper.doi}` : '#');
  const citationCount = mainSource?.citation_count ?? null;

  return (
    <div className="bg-gray-900 border border-gray-800 hover:border-gray-700 rounded-xl p-6 transition-all duration-200 shadow-lg space-y-4">
      {/* Top Bar: Provenance & Relevance Score */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-800/80 pb-3 text-xs">
        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-1 rounded-full bg-blue-950/80 border border-blue-800 text-blue-300 font-semibold flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
            <span>Rank #{item.rank}</span>
          </span>
          <span className="text-gray-400 font-medium">
            Relevance score: <strong className="text-white">{item.final_score.toFixed(2)}</strong>
          </span>
          <div className="group relative inline-block">
            <Info className="w-3.5 h-3.5 text-gray-500 cursor-pointer hover:text-gray-300" />
            <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-950 border border-gray-800 text-gray-300 text-[11px] p-2.5 rounded-lg shadow-xl w-64 pointer-events-none z-30">
              Ranking signal combining normalized keyword, semantic vector similarity, and topic alignment.
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-gray-400">
          {mainSource && (
            <span className="px-2 py-0.5 rounded bg-gray-950 border border-gray-800 text-[11px] text-gray-300 uppercase tracking-wider font-semibold">
              Source: {mainSource.provider}
            </span>
          )}
          {citationCount !== null && (
            <span className="text-gray-400 flex items-center space-x-1" title="Citations reflect scholarly visibility, not methodological quality.">
              <Award className="w-3.5 h-3.5 text-amber-400" />
              <span>{citationCount} citations</span>
            </span>
          )}
        </div>
      </div>

      {/* Main Title & Authors */}
      <div>
        <Link
          href={`/papers/${paper.id}`}
          className="text-lg font-bold text-white hover:text-blue-400 transition-colors leading-snug line-clamp-2"
        >
          {paper.canonical_title}
        </Link>
        <p className="text-xs text-gray-400 mt-2 flex flex-wrap items-center gap-1.5">
          <span className="font-medium text-gray-300">
            {paper.authors.length > 0
              ? paper.authors.map((a) => a.display_name).join(', ')
              : 'Unknown Authors'}
          </span>
          {paper.publication_year && (
            <>
              <span className="text-gray-600">•</span>
              <span className="text-gray-400">{paper.publication_year}</span>
            </>
          )}
          {paper.venue && (
            <>
              <span className="text-gray-600">•</span>
              <span className="text-blue-300/80 italic">{paper.venue}</span>
            </>
          )}
        </p>
      </div>

      {/* Abstract or Missing Abstract Warning */}
      {paper.abstract ? (
        <p className="text-xs text-gray-300 leading-relaxed line-clamp-3 bg-gray-950/40 p-3 rounded-lg border border-gray-800/50">
          {paper.abstract}
        </p>
      ) : (
        <div className="bg-amber-950/30 border border-amber-900/50 p-3 rounded-lg flex items-center space-x-2 text-amber-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Abstract not supplied by source. Match computed using title and subject taxonomy.</span>
        </div>
      )}

      {/* Subjects & Taxonomy Tags */}
      {paper.subjects.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <Tag className="w-3.5 h-3.5 text-gray-500 mr-1" />
          {paper.subjects.slice(0, 4).map((ps, idx) => (
            <span
              key={idx}
              className="text-[11px] px-2 py-0.5 rounded bg-gray-800/80 text-gray-300 border border-gray-700/60 font-medium"
            >
              {ps.subject.name}
            </span>
          ))}
        </div>
      )}

      {/* Match Explanation Toggle Section */}
      <div className="border-t border-gray-800/80 pt-3">
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center space-x-1 transition-colors"
        >
          <span>Why this paper matched</span>
          {showExplanation ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showExplanation && (
          <div className="mt-2.5 p-3.5 bg-gray-950 rounded-lg border border-blue-900/40 text-xs text-gray-300 space-y-2 animate-in fade-in duration-150">
            <p className="font-medium text-white">{item.explanation.summary}</p>
            {item.explanation.shared_title_keywords && item.explanation.shared_title_keywords.length > 0 && (
              <p className="text-gray-400">
                <strong className="text-gray-300">Title keywords:</strong>{' '}
                {item.explanation.shared_title_keywords.join(', ')}
              </p>
            )}
            <p className="text-[10px] text-gray-500 pt-1 border-t border-gray-900 italic">
              {item.explanation.score_disclaimer}
            </p>
          </div>
        )}
      </div>

      {/* Action Footer Bar */}
      <div className="flex items-center justify-between pt-2">
        <div className="flex items-center space-x-3 text-xs">
          <a
            href={originalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-300 hover:text-white flex items-center space-x-1 font-medium transition-colors"
          >
            <span>Original Source</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          {mainSource?.open_access_url && (
            <a
              href={mainSource.open_access_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:text-emerald-300 font-medium flex items-center space-x-1"
            >
              <span>Open Access PDF</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium rounded-lg flex items-center space-x-1.5 transition-colors border border-gray-700"
        >
          <Bookmark className="w-3.5 h-3.5 text-purple-400" />
          <span>Save to Collection</span>
        </button>
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
