'use client';

import React, { useState, useEffect } from 'react';
import { X, Plus, FolderPlus, Bookmark, Check } from 'lucide-react';
import { Collection, apiFetch } from '@/lib/api';

interface SaveToCollectionModalProps {
  paperId: string;
  paperTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function SaveToCollectionModal({
  paperId,
  paperTitle,
  isOpen,
  onClose,
}: SaveToCollectionModalProps) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('');
  const [readingStatus, setReadingStatus] = useState<'to_read' | 'reading' | 'reviewed'>('to_read');
  const [notes, setNotes] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [newCollName, setNewCollName] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchCollections();
    }
  }, [isOpen]);

  const fetchCollections = async () => {
    try {
      const data = await apiFetch<Collection[]>('/collections');
      setCollections(data);
      if (data.length > 0 && !selectedCollectionId) {
        setSelectedCollectionId(data[0].id);
      }
    } catch (e: any) {
      setErrorMsg('Please sign in to save papers to collections.');
    }
  };

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCollName.trim()) return;
    try {
      const newColl = await apiFetch<Collection>('/collections', {
        method: 'POST',
        body: JSON.stringify({ name: newCollName.trim() }),
      });
      setCollections([newColl, ...collections]);
      setSelectedCollectionId(newColl.id);
      setNewCollName('');
      setShowCreateForm(false);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to create collection');
    }
  };

  const handleSavePaper = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCollectionId) {
      setErrorMsg('Please select or create a collection.');
      return;
    }
    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    const tagsList = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    try {
      await apiFetch(`/collections/${selectedCollectionId}/papers`, {
        method: 'POST',
        body: JSON.stringify({
          paper_id: paperId,
          notes: notes.trim() || undefined,
          tags: tagsList,
          reading_status: readingStatus,
        }),
      });
      setSuccessMsg('Paper saved to collection!');
      setTimeout(() => {
        setSuccessMsg('');
        onClose();
      }, 1200);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to save paper');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-lg overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="p-5 border-b border-gray-800 flex items-center justify-between bg-gray-950">
          <h3 className="text-base font-semibold text-white flex items-center space-x-2">
            <Bookmark className="w-5 h-5 text-blue-400" />
            <span>Save to Literature Collection</span>
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div className="bg-gray-950 p-3.5 rounded-lg border border-gray-800">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Paper</p>
            <p className="text-sm font-medium text-white line-clamp-2 mt-0.5">{paperTitle}</p>
          </div>

          {errorMsg && (
            <div className="bg-red-950/60 border border-red-800 text-red-300 p-3 rounded-lg text-xs">
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div className="bg-emerald-950/60 border border-emerald-800 text-emerald-300 p-3 rounded-lg text-xs flex items-center space-x-2">
              <Check className="w-4 h-4" />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleSavePaper} className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-gray-300">Target Collection</label>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(!showCreateForm)}
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>New Collection</span>
                </button>
              </div>

              {showCreateForm ? (
                <div className="flex items-center space-x-2 mb-3">
                  <input
                    type="text"
                    placeholder="Collection name (e.g. LLM Reasoning)"
                    value={newCollName}
                    onChange={(e) => setNewCollName(e.target.value)}
                    className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                  <button
                    type="button"
                    onClick={handleCreateCollection}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium"
                  >
                    Create
                  </button>
                </div>
              ) : null}

              <select
                value={selectedCollectionId}
                onChange={(e) => setSelectedCollectionId(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              >
                {collections.length === 0 && <option value="">No collections found. Create one!</option>}
                {collections.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.paper_count} papers)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Reading Status</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'to_read', label: 'To Read' },
                  { id: 'reading', label: 'Reading' },
                  { id: 'reviewed', label: 'Reviewed' },
                ].map((st) => (
                  <button
                    key={st.id}
                    type="button"
                    onClick={() => setReadingStatus(st.id as any)}
                    className={`py-2 px-3 rounded-lg text-xs font-medium border transition-colors ${
                      readingStatus === st.id
                        ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                        : 'bg-gray-950 border-gray-800 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    {st.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Tags (comma-separated)</label>
              <input
                type="text"
                placeholder="e.g. survey, fine-tuning, benchmark"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Private Research Notes</label>
              <textarea
                rows={3}
                placeholder="Add private methodological notes or literature review comments..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-gray-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !selectedCollectionId}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-md shadow-blue-600/20 transition-colors"
              >
                {loading ? 'Saving...' : 'Save Paper'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
