'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { UserPlus, Sparkles, AlertCircle } from 'lucide-react';
import { apiFetch, User } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await apiFetch<User>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ display_name: displayName, email, password }),
      });
      router.push('/auth/login');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-20">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white mx-auto shadow-lg shadow-blue-600/30">
            <Sparkles className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-white">Create Researcher Account</h1>
          <p className="text-xs text-gray-400">Join ResearchMatch to organize literature reviews & saved papers</p>
        </div>

        {error && (
          <div className="bg-red-950/60 border border-red-800 p-3 rounded-lg text-xs text-red-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Full Name / Display Name</label>
            <input
              type="text"
              required
              placeholder="Dr. Alex Rivera"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Email Address</label>
            <input
              type="email"
              required
              placeholder="researcher@institution.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Password (Min 8 characters)</label>
            <input
              type="password"
              required
              minLength={8}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-blue-600/30 transition-colors flex items-center justify-center space-x-2"
          >
            <UserPlus className="w-4 h-4" />
            <span>{loading ? 'Creating Account...' : 'Register Account'}</span>
          </button>
        </form>

        <p className="text-xs text-center text-gray-400 pt-2 border-t border-gray-800">
          Already registered?{' '}
          <Link href="/auth/login" className="text-blue-400 hover:underline font-semibold">
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
}
