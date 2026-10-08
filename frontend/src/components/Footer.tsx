import React from 'react';
import { Info, ShieldAlert } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-gray-800 bg-gray-950 text-gray-400 py-10 mt-20 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h4 className="text-sm font-semibold text-white mb-2">ResearchMatch Platform</h4>
            <p className="leading-relaxed">
              Discover papers from connected scholarly sources including OpenAlex, Semantic Scholar, and Crossref.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white mb-2 flex items-center space-x-1.5">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Scientific Distinction</span>
            </h4>
            <p className="leading-relaxed text-gray-400">
              Topic similarity does not establish that a paper supports a research claim. Citation counts reflect visibility, not methodological quality.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white mb-2 flex items-center space-x-1.5">
              <Info className="w-4 h-4 text-blue-400" />
              <span>Scope & Discipline</span>
            </h4>
            <p className="leading-relaxed text-gray-400">
              Initial focus: Computer Science, AI, Machine Learning, Data Science, NLP, HCI, and Robotics. Architecture designed for multi-disciplinary extension.
            </p>
          </div>
        </div>
        <div className="border-t border-gray-900 pt-6 flex flex-col sm:flex-row items-center justify-between text-gray-500">
          <p>© {new Date().getFullYear()} ResearchMatch. All rights reserved.</p>
          <p className="mt-2 sm:mt-0">OpenAlex REST API • Semantic Scholar Graph API • Crossref API</p>
        </div>
      </div>
    </footer>
  );
}
