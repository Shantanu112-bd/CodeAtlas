import Link from 'next/link';
import { LayoutDashboard, Network, Share2, AlertTriangle, Layers, Search } from 'lucide-react';

export default function Sidebar() {
  const links = [
    { name: 'Overview', href: '/', icon: LayoutDashboard },
    { name: 'Knowledge Graph', href: '/graph', icon: Network },
    { name: 'Dependencies', href: '/dependencies', icon: Share2 },
    { name: 'Impact Analysis', href: '/impact', icon: AlertTriangle },
    { name: 'Architecture', href: '/architecture', icon: Layers },
    { name: 'Search', href: '/search', icon: Search },
  ];

  return (
    <aside className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col h-full">
      <div className="h-16 flex items-center px-6 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-indigo-500" />
          <span className="font-bold text-lg tracking-tight">CodeAtlas</span>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <Link 
              key={link.name} 
              href={link.href}
              className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800/50 transition-colors"
            >
              <Icon className="w-4 h-4" />
              {link.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-zinc-800">
        <div className="text-xs text-zinc-500 text-center">Repository Intelligence Engine</div>
      </div>
    </aside>
  );
}
