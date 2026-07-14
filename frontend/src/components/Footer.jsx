import React from 'react';
import { useContent } from '../ContentContext';
import { PawPrint, Facebook } from 'lucide-react';

export default function Footer() {
  const content = useContent();
  const { brand, nav, contact } = content;
  return (
    <footer className="bg-[#333D2E] text-white/80 py-14">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2 text-white">
          <PawPrint className="w-5 h-5" strokeWidth={1.8} />
          <span className="font-serif-display text-lg font-semibold">{brand}</span>
        </div>
        <div className="flex items-center gap-8 text-sm">
          {nav.map((n) => (
            <a key={n.href} href={n.href} className="hover:text-white transition-colors">{n.label}</a>
          ))}
        </div>
        <div className="flex items-center gap-6">
          {contact?.facebook_url && (
            <a
              data-testid="footer-facebook-link"
              href={contact.facebook_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Følg os på Facebook"
              title="Facebook-gruppe"
              className="w-10 h-10 rounded-full bg-white/10 hover:bg-[#9E5A3C] flex items-center justify-center transition-colors duration-300"
            >
              <Facebook className="w-5 h-5 text-white" strokeWidth={1.8} />
            </a>
          )}
          <p className="text-xs text-white/50">© {new Date().getFullYear()} {brand}</p>
        </div>
      </div>
    </footer>
  );
}
