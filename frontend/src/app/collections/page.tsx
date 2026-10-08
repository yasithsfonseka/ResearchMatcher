'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Collection, CollectionPaper, apiFetch, API_BASE_URL } from '@/lib/api';
import { FolderHeart, Plus, Download, Trash2, Edit2, Bookmark, FileText, Tag, Check, AlertCircle, RefreshCw } from 'lucide-react';

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [activeCollection, setActiveCollection] = useState<Collection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newCollName, setNewCollName] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingNotesPaperId, setEditingNotesPaperId] = useState<string | null>(null);
  const [notesInput, setNotesInput] = useState('');

  useEffect(() => {
    fetchCollections();
  }, []);

  const fetchCollections = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<Collection[]>('/collections');
      setCollections(data);
      if (data.length > 0) {
        loadCollectionDetails(data[0].id);
      }
    } catch (e: any) {
      setError('Please sign in to view and manage private literature review collections.');
    } finally {
      setLoading(false);
    }
  };

  const loadCollectionDetails = async (id: string) => {
    try {
      const details = await apiFetch<Collection>(`/collections/${id}`);
      setActiveCollection(details);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCollName.trim()) return;
    try {
      const created = await apiFetch<Collection>('/collections', {
        method: 'POST',
        body: JSON.stringify({ name: newCollName.trim() }),
      });
      setCollections([created, ...collections]);
      setActiveCollection(created);
      setNewCollName('');
      setShowCreateModal(false);
    } catch (e: any) {
      alert(e.message || 'Failed to create collection');
    }
  };

  const handleDeleteCollection = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this collection and all saved notes?')) return;
    try {
      await apiFetch(`/collections/${id}`, { method: 'DELETE' });
      const updated = collections.filter((c) => c.id !== id);
      setCollections(updated);
      if (updated.length > 0) {
        loadCollectionDetails(updated[0].id);
      } else {
        setActiveCollection(null);
      }
    } catch (e: any) {
      alert(e.message || 'Failed to delete collection');
    }
  };

  const handleRemovePaper = async (paperId: string) => {
    if (!activeCollection) return;
    try {
      await apiFetch(`/collections/${activeCollection.id}/papers/${paperId}`, { method: 'DELETE' });
      loadCollectionDetails(activeCollection.id);
    } catch (e: any) {
      alert(e.message || 'Failed to remove paper');
    }
  };

  const handleUpdateStatus = async (paperId: string, status: 'to_read' | 'reading' | 'reviewed') => {
    if (!activeCollection) return;
    try {
      await apiFetch(`/collections/${activeCollection.id}/papers/${paperId}`, {
        method: 'PATCH',
        body: JSON.stringify({ reading_status: status }),
      });
      loadCollectionDetails(activeCollection.id);
    } catch (e: any) {
      alert(e.message || 'Failed to update reading status');
    }
  };

  const handleExportCSV = async () => {
    if (!activeCollection) return;
    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API_BASE_URL}/collections/${activeCollection.id}/export`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `collection_${activeCollection.name.replace(/\s+/g, '_')}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <RefreshCw className="w-8 h-8 text-purple-500 animate-spin mx-auto" />
        <p className="text-xs text-gray-400">Loading collections dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto py-20 px-4 text-center space-y-4">
        <FolderHeart className="w-12 h-12 text-purple-400 mx-auto" />
        <h2 className="text-xl font-bold text-white">Private Literature Collections</h2>
        <p className="text-xs text-gray-400">{error}</p>
        <Link href="/auth/login" className="inline-block px-5 py-2.5 bg-blue-600 text-white rounded-lg text-xs font-semibold">
          Sign In
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center space-x-3">
            <FolderHeart className="w-7 h-7 text-purple-400" />
            <span>Literature Review Collections</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Organize discovered papers, track reading status, add notes, and export formula-safe CSVs.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors shadow-lg shadow-purple-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Collection</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Collection List */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3 h-fit">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">My Collections</h3>
          {collections.length === 0 ? (
            <p className="text-xs text-gray-500 py-6 text-center">No collections created yet.</p>
          ) : (
            collections.map((c) => (
              <button
                key={c.id}
                onClick={() => loadCollectionDetails(c.id)}
                className={`w-full text-left p-3 rounded-lg text-xs flex items-center justify-between transition-colors ${
                  activeCollection?.id === c.id
                    ? 'bg-purple-950/80 border border-purple-800 text-purple-200 font-semibold'
                    : 'hover:bg-gray-800 text-gray-300'
                }`}
              >
                <div>
                  <p className="font-semibold">{c.name}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">{c.paper_count} papers saved</p>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Right Column: Active Collection Papers & Controls */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-6">
          {activeCollection ? (
            <>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-800 pb-4 gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white">{activeCollection.name}</h2>
                  <p className="text-xs text-gray-400 mt-0.5">{activeCollection.description || 'No description'}</p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleExportCSV}
                    className="px-3.5 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium rounded-lg flex items-center space-x-1.5 border border-gray-700"
                  >
                    <Download className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Export CSV</span>
                  </button>
                  <button
                    onClick={() => handleDeleteCollection(activeCollection.id)}
                    className="p-1.5 bg-red-950/60 hover:bg-red-900 border border-red-800 text-red-300 rounded-lg"
                    title="Delete Collection"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Paper Items */}
              <div className="space-y-4">
                {!activeCollection.papers || activeCollection.papers.length === 0 ? (
                  <div className="p-12 text-center bg-gray-950 rounded-xl border border-gray-800 space-y-2">
                    <Bookmark className="w-8 h-8 text-gray-600 mx-auto" />
                    <p className="text-xs text-gray-400">No papers saved in this collection yet.</p>
                  </div>
                ) : (
                  activeCollection.papers.map((entry) => (
                    <div key={entry.paper_id} className="bg-gray-950 border border-gray-800 p-5 rounded-xl space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <Link href={`/papers/${entry.paper.id}`} className="text-base font-bold text-white hover:text-blue-400 line-clamp-2">
                            {entry.paper.canonical_title}
                          </Link>
                          <p className="text-xs text-gray-400 mt-1">
                            {entry.paper.authors.map((a) => a.display_name).join(', ')} ({entry.paper.publication_year || 'N/A'})
                          </p>
                        </div>
                        <button
                          onClick={() => handleRemovePaper(entry.paper_id)}
                          className="text-gray-500 hover:text-red-400 text-xs"
                          title="Remove Paper"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Status & Tags */}
                      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-900 pt-3 text-xs">
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-400 font-medium">Status:</span>
                          {(['to_read', 'reading', 'reviewed'] as const).map((st) => (
                            <button
                              key={st}
                              onClick={() => handleUpdateStatus(entry.paper_id, st)}
                              className={`px-2.5 py-0.5 rounded text-[11px] font-semibold uppercase ${
                                entry.reading_status === st
                                  ? 'bg-purple-900 text-purple-200 border border-purple-700'
                                  : 'bg-gray-900 text-gray-500 hover:text-gray-300'
                              }`}
                            >
                              {st.replace('_', ' ')}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Notes */}
                      {entry.notes && (
                        <div className="bg-gray-900/60 p-3 rounded-lg border border-gray-800 text-xs text-gray-300 space-y-1">
                          <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">Private Note</span>
                          <p>{entry.notes}</p>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="py-20 text-center text-xs text-gray-500">Select a collection to view saved papers.</div>
          )}
        </div>
      </div>
    </div>
  );
}
