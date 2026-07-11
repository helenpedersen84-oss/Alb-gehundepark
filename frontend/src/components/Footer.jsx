import React from 'react';
import { CONTENT } from '../mock';
import { PawPrint } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-[#333D2E] text-white/80 py-14">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2 text-white">
          <PawPrint className="w-5 h-5" strokeWidth={1.8} />
          <span className="font-serif-display text-lg font-semibold">{CONTENT.brand}</span>
        </div>
        <div className="flex items-center gap-8 text-sm">
          {CONTENT.nav.map((n) => (
            <a key={n.href} href={n.href} className="hover:text-white transition-colors">{n.label}</a>
          ))}
        </div>
        <p className="text-xs text-white/50">© {new Date().getFullYear()} {CONTENT.brand}</p>
      </div>
    </footer>
  );
}
