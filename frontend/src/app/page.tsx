'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Search, Sparkles, SlidersHorizontal, BookOpen, ShieldCheck, Cpu, BrainCircuit, Bot, Network, FileCode } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [keywords, setKeywords] = useState('');
  const [yearMin, setYearMin] = useState<string>('');
  const [yearMax, setYearMax] = useState<string>('');
  const [openAccessOnly, setOpenAccessOnly] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const params = new URLSearchParams();
    params.set('q', title.trim());
    if (description.trim()) params.set('desc', description.trim());
    if (keywords.trim()) params.set('kw', keywords.trim());
    if (yearMin) params.set('y_min', yearMin);
    if (yearMax) params.set('y_max', yearMax);
    if (openAccessOnly) params.set('oa', 'true');

    router.push(`/search?${params.toString()}`);
  };

  const handleExampleClick = (exampleTitle: string, exampleKeywords: string) => {
    setTitle(exampleTitle);
    setKeywords(exampleKeywords);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-blue-950/80 border border-blue-800 text-blue-300 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span>HYBRID VECTOR & KEYWORD MATCHING ENGINE</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          Match Your Proposed Research to <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400">Connected Scholarly Sources</span>
        </h1>
        <p className="text-base text-gray-400 leading-relaxed">
          ResearchMatch helps you evaluate literature alignment, discover similar works, and organize your review collections.
        </p>
        <div className="pt-2 text-xs text-gray-400 flex items-center justify-center space-x-2 bg-gray-900/60 p-2.5 rounded-lg border border-gray-800 w-fit mx-auto">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Discover papers from connected scholarly sources (OpenAlex, Semantic Scholar, Crossref).</span>
        </div>
      </div>

      {/* Main Search Form Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 sm:p-8 shadow-2xl max-w-4xl mx-auto">
        <form onSubmit={handleSearch} className="space-y-6">
          <div>
            <label className="block text-xs font-bold text-gray-200 uppercase tracking-wider mb-2">
              Proposed Research Title <span className="text-blue-400">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Fine-Tuning Large Language Models for Dialogue Personalization and Memory"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-gray-950 border border-gray-800 focus:border-blue-500 rounded-xl px-4 py-3.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
              Research Description & Objectives <span className="text-gray-500">(Optional)</span>
            </label>
            <textarea
              rows={3}
              placeholder="Describe your research methodology, key objectives, or main hypotheses to improve semantic vector matching context..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-gray-950 border border-gray-800 focus:border-blue-500 rounded-xl px-4 py-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>

          {/* Advanced Filter Toggle */}
          <div className="flex items-center justify-between border-t border-gray-800 pt-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-xs font-semibold text-gray-400 hover:text-white flex items-center space-x-1.5 transition-colors"
            >
              <SlidersHorizontal className="w-4 h-4 text-blue-400" />
              <span>{showAdvanced ? 'Hide Search Filters' : 'Advanced Filters & Keywords'}</span>
            </button>

            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-sm flex items-center space-x-2 shadow-lg shadow-blue-600/30 transition-all transform hover:scale-[1.02]"
            >
              <Search className="w-4 h-4" />
              <span>Discover Papers</span>
            </button>
          </div>

          {showAdvanced && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-gray-800/60 animate-in fade-in duration-150">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">Keywords (Comma-separated)</label>
                <input
                  type="text"
                  placeholder="e.g. conversational ai, transformers, user modeling"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">Year Min</label>
                  <input
                    type="number"
                    placeholder="2018"
                    value={yearMin}
                    onChange={(e) => setYearMin(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">Year Max</label>
                  <input
                    type="number"
                    placeholder="2026"
                    value={yearMax}
                    onChange={(e) => setYearMax(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="sm:col-span-2 flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="oa"
                  checked={openAccessOnly}
                  onChange={(e) => setOpenAccessOnly(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded bg-gray-950 border-gray-800 focus:ring-blue-500"
                />
                <label htmlFor="oa" className="text-xs text-gray-300 cursor-pointer">
                  Restrict to Open-Access publications only
                </label>
              </div>
            </div>
          )}
        </form>

        {/* Example Queries */}
        <div className="mt-8 pt-6 border-t border-gray-800/80">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Example Research Queries</p>
          <div className="flex flex-wrap gap-2">
            {[
              { title: 'Graph Neural Networks for Drug Discovery and Property Prediction', kw: 'gnn, drug discovery, molecular property' },
              { title: 'Zero-Shot Cross-Lingual Transfer in Multilingual Transformers', kw: 'bert, cross-lingual, nlp' },
              { title: 'Human-Robot Interaction for Adaptive Assistive Robotics', kw: 'hri, robotics, user adaptation' },
            ].map((ex, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleExampleClick(ex.title, ex.kw)}
                className="text-xs px-3 py-1.5 rounded-lg bg-gray-950 hover:bg-gray-800 text-gray-300 border border-gray-800 text-left transition-colors"
              >
                {ex.title}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Subject Scope Entry Points */}
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white">Initial Subject Taxonomy Scope</h2>
          <p className="text-xs text-gray-400 mt-1">Browse papers across Computer Science and core AI domains</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { icon: BrainCircuit, title: 'Artificial Intelligence', count: 'OpenAlex / S2' },
            { icon: Cpu, title: 'Machine Learning', count: 'OpenAlex / S2' },
            { icon: Bot, title: 'Robotics', count: 'OpenAlex / S2' },
            { icon: Network, title: 'Natural Language Processing', count: 'OpenAlex / S2' },
          ].map((subj, idx) => (
            <Link
              key={idx}
              href="/subjects"
              className="p-4 rounded-xl bg-gray-900 border border-gray-800 hover:border-blue-500/50 hover:bg-gray-800/50 transition-all flex flex-col items-center text-center space-y-2 group"
            >
              <subj.icon className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform" />
              <span className="text-xs font-semibold text-white group-hover:text-blue-300">{subj.title}</span>
              <span className="text-[10px] text-gray-500">{subj.count}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
