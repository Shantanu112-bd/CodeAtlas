"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// Cytoscape requires document to be defined, so dynamic import with SSR disabled is required.
const CytoscapeComponent = dynamic(() => import("react-cytoscapejs"), { ssr: false });

export default function KnowledgeGraphExplorer() {
  const [elements, setElements] = useState<any[]>([]);

  useEffect(() => {
    // Generate some mock massive graph data for the MVP
    const nodes = [];
    const edges = [];
    
    // Core Services
    const services = ['AuthService', 'PaymentService', 'UserRepository', 'EmailService', 'DatabaseCore'];
    services.forEach((s, i) => {
      nodes.push({ data: { id: s, label: s, type: 'service' } });
    });
    
    // Connections
    edges.push({ data: { source: 'AuthService', target: 'UserRepository' } });
    edges.push({ data: { source: 'PaymentService', target: 'UserRepository' } });
    edges.push({ data: { source: 'PaymentService', target: 'EmailService' } });
    edges.push({ data: { source: 'UserRepository', target: 'DatabaseCore' } });

    // Generate random nodes to simulate density
    for (let i = 0; i < 50; i++) {
      const id = `node_${i}`;
      nodes.push({ data: { id, label: `Utility_${i}`, type: 'utility' } });
      edges.push({ data: { source: id, target: services[i % services.length] } });
    }

    setElements([...nodes, ...edges]);
  }, []);

  const layout = { name: "cose" };
  const style = [
    {
      selector: "node",
      style: {
        "background-color": "#6366f1",
        label: "data(label)",
        color: "#f4f4f5",
        "font-size": "10px",
        "text-valign": "center" as const,
        "text-halign": "center" as const,
        width: 40,
        height: 40,
      },
    },
    {
      selector: 'node[type="service"]',
      style: {
        "background-color": "#10b981",
        width: 60,
        height: 60,
        "font-size": "12px",
      }
    },
    {
      selector: "edge",
      style: {
        width: 1,
        "line-color": "#3f3f46",
        "target-arrow-color": "#3f3f46",
        "target-arrow-shape": "triangle" as const,
        "curve-style": "bezier" as const,
      },
    },
  ];

  return (
    <div className="flex flex-col h-full w-full">
      <header className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-950">
        <div>
          <h1 className="text-2xl font-bold text-zinc-50">Knowledge Graph Explorer</h1>
          <p className="text-zinc-400 text-sm">Massive, zoomable visualization of all nodes and edges via Cytoscape.</p>
        </div>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 text-sm bg-zinc-800 text-zinc-300 rounded hover:bg-zinc-700 transition-colors">Filter Nodes</button>
          <button className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-500 transition-colors">Reset View</button>
        </div>
      </header>
      
      <div className="flex-1 w-full bg-[#09090b]">
        {elements.length > 0 && (
          <CytoscapeComponent
            elements={elements}
            layout={layout}
            stylesheet={style}
            style={{ width: "100%", height: "100%" }}
            minZoom={0.2}
            maxZoom={4}
          />
        )}
      </div>
    </div>
  );
}
