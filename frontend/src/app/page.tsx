"use client";

import React, { useEffect, useState } from "react";
import axios from "axios";
import { FileCode, Box, Code, Share2, Activity, Layers, Database } from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";
// Placeholder UUID for the single repository for MVP
const REPO_ID = "00000000-0000-0000-0000-000000000000"; 

interface RepoStats {
  repository_id: string;
  files: number;
  classes: number;
  functions: number;
  dependencies: number;
  services: number;
  controllers: number;
  repositories: number;
  health_score: number;
}

export default function RepositoryOverview() {
  const [stats, setStats] = useState<RepoStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // We would fetch the real ID dynamically. Mocking for UI build context.
    const fetchStats = async () => {
      try {
        // Just mock data for now since we don't have a real UUID in the UI yet
        setStats({
          repository_id: REPO_ID,
          files: 145,
          classes: 42,
          functions: 380,
          dependencies: 1205,
          services: 12,
          controllers: 8,
          repositories: 5,
          health_score: 92
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading || !stats) {
    return <div className="p-8 text-zinc-400 animate-pulse">Loading repository statistics...</div>;
  }

  const metrics = [
    { label: "Files", value: stats.files, icon: FileCode, color: "text-blue-400", bg: "bg-blue-400/10" },
    { label: "Classes", value: stats.classes, icon: Box, color: "text-indigo-400", bg: "bg-indigo-400/10" },
    { label: "Functions", value: stats.functions, icon: Code, color: "text-purple-400", bg: "bg-purple-400/10" },
    { label: "Dependencies", value: stats.dependencies, icon: Share2, color: "text-rose-400", bg: "bg-rose-400/10" },
    { label: "Services", value: stats.services, icon: Activity, color: "text-emerald-400", bg: "bg-emerald-400/10" },
    { label: "Controllers", value: stats.controllers, icon: Layers, color: "text-amber-400", bg: "bg-amber-400/10" },
    { label: "Repositories", value: stats.repositories, icon: Database, color: "text-cyan-400", bg: "bg-cyan-400/10" },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-50">Repository Overview</h1>
          <p className="text-zinc-400 mt-1">High-level structural metrics and intelligence.</p>
        </div>
        <div className="flex flex-col items-end">
          <div className="text-sm text-zinc-400 mb-1">Health Score</div>
          <div className="flex items-center gap-2">
            <div className="text-3xl font-bold text-emerald-400">{stats.health_score}</div>
            <div className="text-zinc-500">/ 100</div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div key={m.label} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex items-center gap-4 hover:border-zinc-700 transition-colors">
              <div className={`w-12 h-12 rounded-lg ${m.bg} flex items-center justify-center`}>
                <Icon className={`w-6 h-6 ${m.color}`} />
              </div>
              <div>
                <div className="text-2xl font-semibold text-zinc-100">{m.value.toLocaleString()}</div>
                <div className="text-sm font-medium text-zinc-500">{m.label}</div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 h-96 flex flex-col items-center justify-center text-zinc-500">
        <Activity className="w-8 h-8 mb-4 opacity-50" />
        <p>Recent Activity Feed (Coming Soon)</p>
        <p className="text-sm mt-2">Will show indexing updates, structural changes, and drift detection.</p>
      </div>
    </div>
  );
}
