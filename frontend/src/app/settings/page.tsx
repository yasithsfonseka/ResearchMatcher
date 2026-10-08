'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Settings, Shield, Trash2, Check, AlertTriangle } from 'lucide-react';
import { User, apiFetch } from '@/lib/api';

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<User>('/auth/me')
      .then(setUser)
      .catch(() => router.push('/auth/login'));
  }, []);

  const handleDeleteHistory = async () => {
    if (!window.confirm('Delete all search query history records?')) return;
    try {
      await apiFetch('/auth/delete-history', { method: 'POST' });
      setMsg('Search query history deleted successfully.');
    } catch (e: any) {
      alert(e.message || 'Failed to delete history');
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm('CRITICAL: Delete your account and all private collections permanently? This action cannot be undone.')) return;
    try {
      await apiFetch('/auth/me', { method: 'DELETE' });
      localStorage.removeItem('access_token');
      router.push('/');
    } catch (e: any) {
      alert(e.message || 'Failed to delete account');
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center space-x-3">
          <Settings className="w-7 h-7 text-blue-400" />
          <span>Account & Privacy Settings</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">Manage data retention policies and account security settings.</p>
      </div>

      {msg && (
        <div className="bg-emerald-950/60 border border-emerald-800 p-3 rounded-lg text-xs text-emerald-300 flex items-center space-x-2">
          <Check className="w-4 h-4" />
          <span>{msg}</span>
        </div>
      )}

      {/* Account Profile Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white">Researcher Identity</h3>
        <div className="text-xs text-gray-300 space-y-1">
          <p>
            <strong className="text-gray-200">Name:</strong> {user.display_name}
          </p>
          <p>
            <strong className="text-gray-200">Email:</strong> {user.email}
          </p>
          <p>
            <strong className="text-gray-200">Account ID:</strong> {user.id}
          </p>
        </div>
      </div>

      {/* Privacy & Query Data Policy Card */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span>Data Retention & Search History Privacy</span>
        </h3>
        <p className="text-xs text-gray-400 leading-relaxed">
          ResearchMatch treats proposed research descriptions and query context as confidential. Search query parameters are retained strictly for matching pipeline execution and optional account query logs.
        </p>

        <div className="pt-2">
          <button
            onClick={handleDeleteHistory}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold rounded-lg transition-colors border border-gray-700"
          >
            Clear Search History
          </button>
        </div>
      </div>

      {/* Danger Zone Account Deletion */}
      <div className="bg-red-950/30 border border-red-900/60 rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold text-red-300 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <span>Danger Zone</span>
        </h3>
        <p className="text-xs text-red-300/80">
          Permanently purge your account, saved collections, private literature notes, and history records.
        </p>
        <button
          onClick={handleDeleteAccount}
          className="px-4 py-2 bg-red-800 hover:bg-red-700 text-white text-xs font-bold rounded-lg transition-colors shadow-lg shadow-red-900/30 flex items-center space-x-1.5"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Delete Account Permanently</span>
        </button>
      </div>
    </div>
  );
}
