'use client';

import React, { useEffect, useState } from 'react';
import { Subject, Paper, apiFetch } from '@/lib/api';
import { BookOpen, FolderTree, Search, ChevronRight, Layers, Tag } from 'lucide-react';
import Link from 'next/link';

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [filterQuery, setFilterQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const [loadingPapers, setLoadingPapers] = useState(false);

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = async () => {
    setLoadingSubjects(true);
    try {
      const data = await apiFetch<Subject[]>('/subjects');
      setSubjects(data);
      if (data.length > 0) {
        handleSelectSubject(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingSubjects(false);
    }
  };

  const handleSelectSubject = async (subj: Subject) => {
    setSelectedSubject(subj);
    setLoadingPapers(true);
    try {
      const paperData = await apiFetch<Paper[]>(`/subjects/${subj.id}/papers`);
      setPapers(paperData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingPapers(false);
    }
  };

  const filteredSubjects = subjects.filter((s) => {
    const matchesText = s.name.toLowerCase().includes(filterQuery.toLowerCase());
    const matchesLevel = levelFilter === 'ALL' || s.level === levelFilter;
    return matchesText && matchesLevel;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center space-x-3">
          <BookOpen className="w-7 h-7 text-emerald-400" />
          <span>Subject & Domain Browser</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          Explore scholarly taxonomy hierarchy (Domain → Field → Subfield → Topic) mapped from OpenAlex taxonomy.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Subject Taxonomy Hierarchy List */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4 h-fit">
          <div className="space-y-3">
            <div className="relative">
              <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search subjects..."
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="flex items-center space-x-1 text-[11px] text-gray-400">
              <span className="font-semibold text-gray-300">Level:</span>
              {['ALL', 'Domain', 'Field', 'Subfield', 'Topic'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setLevelFilter(lvl)}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    levelFilter === lvl ? 'bg-emerald-600 text-white font-bold' : 'hover:bg-gray-800'
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5 max-h-[550px] overflow-y-auto pr-1">
            {loadingSubjects ? (
              <p className="text-xs text-gray-500 text-center py-6">Loading taxonomy...</p>
            ) : filteredSubjects.length === 0 ? (
              <p className="text-xs text-gray-500 text-center py-6">No matching subjects found</p>
            ) : (
              filteredSubjects.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleSelectSubject(s)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs flex items-center justify-between transition-colors ${
                    selectedSubject?.id === s.id
                      ? 'bg-emerald-950/80 border border-emerald-800 text-emerald-200 font-semibold'
                      : 'hover:bg-gray-800 text-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <FolderTree className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="truncate">{s.name}</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-950 text-gray-400 rounded shrink-0 border border-gray-800">
                    {s.level}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Filtered Papers for Selected Subject */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-6">
          {selectedSubject ? (
            <>
              <div className="border-b border-gray-800 pb-4">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-emerald-950 border border-emerald-800 text-emerald-300 rounded">
                  {selectedSubject.level} Taxonomy Node
                </span>
                <h2 className="text-xl font-bold text-white mt-1.5">{selectedSubject.name}</h2>
                <p className="text-xs text-gray-400 mt-1">
                  Provider: <span className="text-gray-200 uppercase">{selectedSubject.provider}</span> • External ID:{' '}
                  <span className="text-gray-200">{selectedSubject.external_id}</span>
                </p>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-300 flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-blue-400" />
                  <span>Associated Papers ({papers.length})</span>
                </h3>

                {loadingPapers ? (
                  <p className="text-xs text-gray-500 py-10 text-center">Loading papers for subject...</p>
                ) : papers.length === 0 ? (
                  <div className="p-8 text-center bg-gray-950 rounded-lg border border-gray-800 space-y-2">
                    <Tag className="w-6 h-6 text-gray-600 mx-auto" />
                    <p className="text-xs text-gray-400">No indexed papers assigned to this subject yet.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {papers.map((p) => (
                      <div key={p.id} className="p-4 bg-gray-950 border border-gray-800 rounded-lg space-y-2">
                        <Link href={`/papers/${p.id}`} className="text-sm font-bold text-white hover:text-blue-400">
                          {p.canonical_title}
                        </Link>
                        <p className="text-xs text-gray-400">
                          {p.authors.map((a) => a.display_name).join(', ')} ({p.publication_year || 'N/A'})
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-gray-500 text-xs">Select a subject from the left panel to browse papers.</div>
          )}
        </div>
      </div>
    </div>
  );
}
