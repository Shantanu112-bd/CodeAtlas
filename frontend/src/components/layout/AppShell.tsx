import React from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-screen bg-zinc-950 text-zinc-50 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto bg-zinc-950/50">
          {children}
        </main>
      </div>
    </div>
  );
}
