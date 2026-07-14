import React, { useEffect, useState } from 'react';
import { useContent } from '../ContentContext';
import { PawPrint, Menu, X, Facebook } from 'lucide-react';

export default function Navbar({ onBook }) {
  const { brand, nav, contact } = useContent();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-500 ${
        scrolled ? 'bg-[#EFE9DE]/95 backdrop-blur-md shadow-sm' : 'bg-transparent'
      }`}
    >
      <nav className="max-w-7xl mx-auto px-6 lg:px-10 h-20 flex items-center justify-between">
        <a href="#top" className={`flex items-center gap-2 ${scrolled ? 'text-[#333D2E]' : 'text-white'}`}>
          <PawPrint className="w-5 h-5" strokeWidth={1.8} />
          <span className="font-serif-display text-xl font-semibold tracking-wide">{brand}</span>
        </a>

        <div className="hidden md:flex items-center gap-9">
          {nav.map((n) => (
            <a
              key={n.href}
              href={n.href}
              className={`text-sm tracking-wide transition-colors hover:text-[#9E5A3C] ${
                scrolled ? 'text-[#4A4437]' : 'text-white/90'
              }`}
            >
              {n.label}
            </a>
          ))}
          {contact?.facebook_url && (
            <a
              data-testid="navbar-facebook-link"
              href={contact.facebook_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Følg os på Facebook"
              title="Facebook-gruppe"
              className={`transition-colors hover:text-[#9E5A3C] ${scrolled ? 'text-[#4A4437]' : 'text-white/90'}`}
            >
              <Facebook className="w-5 h-5" strokeWidth={1.8} />
            </a>
          )}
          <button
            onClick={onBook}
            className="bg-[#9E5A3C] hover:bg-[#874A30] text-white text-sm px-6 py-2.5 rounded-full transition-colors duration-300 shadow-sm"
          >
            Book nu
          </button>
        </div>

        <button
          className={`md:hidden ${scrolled ? 'text-[#333D2E]' : 'text-white'}`}
          onClick={() => setOpen(!open)}
          aria-label="Menu"
        >
          {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </nav>

      {open && (
        <div className="md:hidden bg-[#EFE9DE] border-t border-[#DED5C6] px-6 py-4 flex flex-col gap-4">
          {nav.map((n) => (
            <a key={n.href} href={n.href} onClick={() => setOpen(false)} className="text-[#4A4437] text-sm">
              {n.label}
            </a>
          ))}
          {contact?.facebook_url && (
            <a
              data-testid="navbar-facebook-link-mobile"
              href={contact.facebook_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 text-[#4A4437] text-sm"
            >
              <Facebook className="w-4 h-4" strokeWidth={1.8} /> Facebook
            </a>
          )}
          <button
            onClick={() => { setOpen(false); onBook(); }}
            className="bg-[#9E5A3C] text-white text-sm px-6 py-2.5 rounded-full w-full"
          >
            Book nu
          </button>
        </div>
      )}
    </header>
  );
}
