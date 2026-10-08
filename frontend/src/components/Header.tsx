'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { BookOpen, Search, FolderHeart, Settings, LogIn, LogOut, Sparkles } from 'lucide-react';
import { User, apiFetch } from '@/lib/api';

export default function Header() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      apiFetch<User>('/auth/me')
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('access_token');
          setUser(null);
        });
    }
  }, []);

  const handleLogout = async () => {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch (e) {
      // ignore
    }
    localStorage.removeItem('access_token');
    setUser(null);
    window.location.href = '/';
  };

  return (
    <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/30 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-bold tracking-tight text-white group-hover:text-blue-400 transition-colors">
              ResearchMatch
            </span>
            <span className="text-[10px] text-gray-400 font-medium tracking-wide">SCHOLARLY DISCOVERY</span>
          </div>
        </Link>

        <nav className="flex items-center space-x-6">
          <Link href="/" className="flex items-center space-x-1.5 text-sm font-medium text-gray-300 hover:text-white transition-colors">
            <Search className="w-4 h-4 text-blue-400" />
            <span>Discover</span>
          </Link>
          <Link href="/subjects" className="flex items-center space-x-1.5 text-sm font-medium text-gray-300 hover:text-white transition-colors">
            <BookOpen className="w-4 h-4 text-emerald-400" />
            <span>Browse Subjects</span>
          </Link>
          <Link href="/collections" className="flex items-center space-x-1.5 text-sm font-medium text-gray-300 hover:text-white transition-colors">
            <FolderHeart className="w-4 h-4 text-purple-400" />
            <span>Collections</span>
          </Link>
        </nav>

        <div className="flex items-center space-x-4">
          {user ? (
            <div className="flex items-center space-x-3">
              <Link href="/settings" className="text-sm text-gray-300 hover:text-white flex items-center space-x-1">
                <Settings className="w-4 h-4" />
                <span className="hidden sm:inline">{user.display_name}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 text-xs font-medium bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg flex items-center space-x-1 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link
                href="/auth/login"
                className="px-3.5 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors flex items-center space-x-1"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
              <Link
                href="/auth/register"
                className="px-3.5 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors shadow-md shadow-blue-600/20"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
