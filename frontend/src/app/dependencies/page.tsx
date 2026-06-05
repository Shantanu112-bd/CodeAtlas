"use client";

import React, { useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  { id: 'center', position: { x: 400, y: 300 }, data: { label: 'AuthService' }, style: { background: '#6366f1', color: 'white', border: 'none', borderRadius: '8px', padding: '10px' } },
  { id: 'dep1', position: { x: 200, y: 100 }, data: { label: 'UserRepository' }, style: { background: '#3f3f46', color: 'white', border: '1px solid #52525b', borderRadius: '8px', padding: '10px' } },
  { id: 'dep2', position: { x: 600, y: 100 }, data: { label: 'JwtUtils' }, style: { background: '#3f3f46', color: 'white', border: '1px solid #52525b', borderRadius: '8px', padding: '10px' } },
  { id: 'caller1', position: { x: 400, y: 500 }, data: { label: 'LoginController' }, style: { background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', padding: '10px' } },
];

const initialEdges = [
  { id: 'e1', source: 'center', target: 'dep1', animated: true, style: { stroke: '#a1a1aa' } },
  { id: 'e2', source: 'center', target: 'dep2', animated: true, style: { stroke: '#a1a1aa' } },
  { id: 'e3', source: 'caller1', target: 'center', animated: true, style: { stroke: '#10b981' } },
];

export default function DependencyExplorer() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="flex flex-col h-full w-full">
      <header className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-950">
        <div>
          <h1 className="text-2xl font-bold text-zinc-50">Dependency Explorer</h1>
          <p className="text-zinc-400 text-sm">Visualize forward and reverse dependencies for a specific component.</p>
        </div>
        <div className="flex gap-4 items-center">
          <div className="bg-zinc-900 border border-zinc-800 rounded-md p-1 flex text-sm">
            <button className="px-3 py-1 bg-zinc-800 text-zinc-100 rounded shadow-sm">Both</button>
            <button className="px-3 py-1 text-zinc-400 hover:text-zinc-200">Forward</button>
            <button className="px-3 py-1 text-zinc-400 hover:text-zinc-200">Reverse</button>
          </div>
          <button className="px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-500 transition-colors">Select Node</button>
        </div>
      </header>

      <div className="flex-1 w-full bg-[#09090b]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          colorMode="dark"
          fitView
        >
          <Controls className="bg-zinc-900 border-zinc-800 fill-zinc-400" />
          <MiniMap nodeStrokeWidth={3} nodeColor="#3f3f46" maskColor="rgba(9, 9, 11, 0.8)" style={{ backgroundColor: '#18181b' }} />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#27272a" />
        </ReactFlow>
      </div>
    </div>
  );
}
