"use client";

import React, { useEffect } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 180;
const nodeHeight = 50;

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = 'top';
    node.sourcePosition = 'bottom';
    
    // We are shifting the dagre node position (anchor=center center) to the top left
    // so it matches the React Flow node anchor point (top left).
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    return node;
  });

  return { nodes, edges };
};

const initialNodes = [
  // Controllers
  { id: 'c1', data: { label: 'UserController' }, style: { background: '#f59e0b', color: 'black', fontWeight: 'bold' } },
  { id: 'c2', data: { label: 'PaymentController' }, style: { background: '#f59e0b', color: 'black', fontWeight: 'bold' } },
  
  // Services
  { id: 's1', data: { label: 'UserService' }, style: { background: '#10b981', color: 'black', fontWeight: 'bold' } },
  { id: 's2', data: { label: 'PaymentService' }, style: { background: '#10b981', color: 'black', fontWeight: 'bold' } },
  { id: 's3', data: { label: 'EmailService' }, style: { background: '#10b981', color: 'black', fontWeight: 'bold' } },
  
  // Repositories
  { id: 'r1', data: { label: 'UserRepository' }, style: { background: '#6366f1', color: 'white', fontWeight: 'bold' } },
  { id: 'r2', data: { label: 'PaymentRepository' }, style: { background: '#6366f1', color: 'white', fontWeight: 'bold' } },
];

const initialEdges = [
  { id: 'e1', source: 'c1', target: 's1' },
  { id: 'e2', source: 'c2', target: 's2' },
  { id: 'e3', source: 's1', target: 'r1' },
  { id: 'e4', source: 's2', target: 'r2' },
  { id: 'e5', source: 's2', target: 's1' },
  { id: 'e6', source: 's2', target: 's3' },
];

const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
  initialNodes,
  initialEdges
);

export default function ArchitectureView() {
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  return (
    <div className="flex flex-col h-full w-full">
      <header className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-950">
        <div>
          <h1 className="text-2xl font-bold text-zinc-50">Architecture View</h1>
          <p className="text-zinc-400 text-sm">Auto-layout hierarchical diagram of Services, Controllers, and Repositories.</p>
        </div>
      </header>

      <div className="flex-1 w-full bg-[#09090b]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          colorMode="dark"
          fitView
          fitViewOptions={{ padding: 0.2 }}
        >
          <Controls className="bg-zinc-900 border-zinc-800 fill-zinc-400" />
          <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#27272a" />
        </ReactFlow>
      </div>
    </div>
  );
}
