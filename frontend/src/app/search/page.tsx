"use client";

import React, { useState } from 'react';
import { Search, ChevronRight, FileCode, Box, Code } from 'lucide-react';

export default function SearchExperience() {
  const [query, setQuery] = useState("");
  
  // Mock search results
  const mockResults = [
    { id: 1, type: "class", name: "UserRepository", file: "backend/app/repositories/user_repo.py", score: 0.98, intent: "code_discovery" },
    { id: 2, type: "file", name: "user_repo.py", file: "backend/app/repositories/user_repo.py", score: 0.85, intent: "code_discovery" },
    { id: 3, type: "function", name: "get_user_by_id", file: "backend/app/repositories/user_repo.py", score: 0.72, intent: "code_discovery" },
  ];

  const getIcon = (type: string) => {
    if (type === 'class') return <Box className="w-4 h-4 text-indigo-400" />;
    if (type === 'file') return <FileCode className="w-4 h-4 text-blue-400" />;
    return <Code className="w-4 h-4 text-purple-400" />;
  };

  return (
    <div className="flex flex-col h-full w-full">
      <header className="px-6 py-6 border-b border-zinc-800 bg-zinc-950 flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-50">Hybrid Semantic Search</h1>
          <p className="text-zinc-400 text-sm">Powered by RRF: Combining Vector embeddings and Graph context.</p>
        </div>
        <div className="relative w-full max-w-3xl">
          <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-indigo-500" />
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Where is authentication implemented?" 
            className="w-full bg-zinc-900 border-2 border-zinc-800 rounded-xl pl-12 pr-4 py-4 text-lg focus:outline-none focus:border-indigo-500/50 text-zinc-100 placeholder:text-zinc-500 shadow-lg"
          />
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-mono text-zinc-500 bg-zinc-800 px-2 py-1 rounded">
            Enter
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Search Results */}
        <div className="w-1/2 border-r border-zinc-800 bg-[#09090b] p-6 overflow-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">Top Results</h2>
            <div className="text-xs bg-indigo-500/10 text-indigo-400 px-2 py-1 rounded border border-indigo-500/20">
              Intent: Code Discovery
            </div>
          </div>
          
          <div className="space-y-3">
            {mockResults.map(res => (
              <div key={res.id} className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 cursor-pointer transition-colors group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-800 rounded-md">
                      {getIcon(res.type)}
                    </div>
                    <div>
                      <div className="font-medium text-zinc-200 group-hover:text-indigo-400 transition-colors">{res.name}</div>
                      <div className="text-xs text-zinc-500 mt-1">{res.file}</div>
                    </div>
                  </div>
                  <div className="text-xs font-mono text-zinc-500 bg-zinc-950 px-2 py-1 rounded border border-zinc-800">
                    {res.score.toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Context Pane */}
        <div className="w-1/2 bg-zinc-950 p-6 flex flex-col">
          <h2 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Graph Context</h2>
          <div className="flex-1 border border-zinc-800 rounded-lg bg-[#09090b] flex items-center justify-center text-zinc-500 flex-col gap-4 p-8 text-center">
            <NetworkIcon />
            <p>Select a search result to view its immediate graph context.</p>
            <p className="text-sm">This visualizes the callers, callees, and dependencies automatically appended by the Hybrid Ranking Engine.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function NetworkIcon() {
  return (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="opacity-50">
      <rect x="16" y="16" width="6" height="6" rx="1" />
      <rect x="2" y="16" width="6" height="6" rx="1" />
      <rect x="9" y="2" width="6" height="6" rx="1" />
      <path d="M5 16v-3a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v3" />
      <path d="M12 8v4" />
    </svg>
  );
}
