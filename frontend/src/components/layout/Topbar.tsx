import { Search } from 'lucide-react';

export default function Topbar() {
  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm z-10 sticky top-0">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-96">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input 
            type="text" 
            placeholder="Search code, components, or ask a question (Cmd+K)" 
            className="w-full bg-zinc-900 border border-zinc-800 rounded-full pl-10 pr-4 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-zinc-100 placeholder:text-zinc-500"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <select className="bg-zinc-900 border border-zinc-800 rounded-md px-3 py-1.5 text-sm text-zinc-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50">
          <option>CodeAtlas Repository</option>
        </select>
        <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-medium text-sm">
          CA
        </div>
      </div>
    </header>
  );
}
