"use client";

import React from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AlertTriangle, AlertCircle, FileCode } from 'lucide-react';

const initialNodes = [
  { id: 'target', position: { x: 100, y: 200 }, data: { label: 'AuthContext.tsx' }, style: { background: '#ef4444', color: 'white', border: 'none', borderRadius: '8px', padding: '10px', boxShadow: '0 0 15px rgba(239, 68, 68, 0.5)' } },
  { id: 'i1', position: { x: 400, y: 100 }, data: { label: 'Header.tsx' }, style: { background: '#f59e0b', color: 'white', border: 'none', borderRadius: '8px', padding: '10px' } },
  { id: 'i2', position: { x: 400, y: 200 }, data: { label: 'LoginModal.tsx' }, style: { background: '#f59e0b', color: 'white', border: 'none', borderRadius: '8px', padding: '10px' } },
  { id: 'i3', position: { x: 400, y: 300 }, data: { label: 'ProtectedRoute.tsx' }, style: { background: '#f59e0b', color: 'white', border: 'none', borderRadius: '8px', padding: '10px' } },
  { id: 'i4', position: { x: 700, y: 200 }, data: { label: 'App.tsx' }, style: { background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', padding: '10px' } },
];

const initialEdges = [
  { id: 'e1', source: 'target', target: 'i1', style: { stroke: '#ef4444', strokeWidth: 2 } },
  { id: 'e2', source: 'target', target: 'i2', style: { stroke: '#ef4444', strokeWidth: 2 } },
  { id: 'e3', source: 'target', target: 'i3', style: { stroke: '#ef4444', strokeWidth: 2 } },
  { id: 'e4', source: 'i3', target: 'i4', style: { stroke: '#f59e0b', strokeWidth: 1, strokeDasharray: '5 5' } },
];

export default function ImpactAnalysis() {
  return (
    <div className="flex flex-col h-full w-full">
      <header className="px-6 py-4 border-b border-zinc-800 flex justify-between items-start bg-zinc-950">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-zinc-50 flex items-center gap-2">
            <AlertTriangle className="text-amber-500 w-6 h-6" /> Impact Analysis
          </h1>
          <p className="text-zinc-400 text-sm mt-1">Determine what breaks if you modify or delete a component.</p>
        </div>
        
        <div className="flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <div className="text-sm text-zinc-400 mb-2">Target Component</div>
          <div className="flex gap-2">
            <input type="text" value="AuthContext.tsx" readOnly className="flex-1 bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-sm text-zinc-300" />
            <button className="px-3 py-1.5 bg-zinc-800 text-zinc-300 rounded text-sm hover:bg-zinc-700">Change</button>
          </div>
        </div>
      </header>

      <div className="flex h-full w-full">
        {/* Left Sidebar for Metrics */}
        <div className="w-80 border-r border-zinc-800 bg-zinc-950 p-6 flex flex-col gap-6 overflow-auto">
          <div>
            <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-3">Risk Assessment</h3>
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="text-red-500 w-5 h-5 shrink-0" />
              <div>
                <div className="text-red-400 font-medium">High Risk</div>
                <div className="text-xs text-zinc-400 mt-1">Modifying this file will directly break 3 components and indirectly affect the entire application shell.</div>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-3">Affected Components</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-amber-400 bg-amber-400/10 px-3 py-2 rounded">
                <FileCode className="w-4 h-4" /> Header.tsx
              </div>
              <div className="flex items-center gap-2 text-sm text-amber-400 bg-amber-400/10 px-3 py-2 rounded">
                <FileCode className="w-4 h-4" /> LoginModal.tsx
              </div>
              <div className="flex items-center gap-2 text-sm text-amber-400 bg-amber-400/10 px-3 py-2 rounded">
                <FileCode className="w-4 h-4" /> ProtectedRoute.tsx
              </div>
              <div className="flex items-center gap-2 text-sm text-blue-400 bg-blue-400/10 px-3 py-2 rounded">
                <FileCode className="w-4 h-4" /> App.tsx (Indirect)
              </div>
            </div>
          </div>
        </div>
        
        {/* Main Graph Area */}
        <div className="flex-1 bg-[#09090b]">
          <ReactFlow
            nodes={initialNodes}
            edges={initialEdges}
            colorMode="dark"
            fitView
          >
            <Controls className="bg-zinc-900 border-zinc-800 fill-zinc-400" />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#27272a" />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
