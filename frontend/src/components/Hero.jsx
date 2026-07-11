import React from 'react';
import { CONTENT } from '../mock';
import { ChevronDown } from 'lucide-react';

export default function Hero({ onBook }) {
  const { hero } = CONTENT;
  return (
    <section id="top" className="relative h-screen min-h-[640px] w-full overflow-hidden">
      <img src={hero.image} alt="Hund løber frit i naturskøn eng" className="absolute inset-0 w-full h-full object-cover" />
      <div className="absolute inset-0 bg-gradient-to-b from-black/25 via-black/10 to-black/35" />

      <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-6">
        <p className="text-white/90 text-xs md:text-sm tracking-widest-2 uppercase mb-6 animate-fade-up">
          {hero.kicker}
        </p>
        <h1 className="font-serif-display text-white leading-[0.95] animate-fade-up" style={{ animationDelay: '0.1s' }}>
          <span className="block text-6xl md:text-8xl font-semibold">{hero.title1}</span>
          <span className="block text-6xl md:text-8xl italic font-medium mt-1">{hero.title2}</span>
        </h1>
        <p className="text-white/90 text-base md:text-lg max-w-xl mt-7 animate-fade-up" style={{ animationDelay: '0.2s' }}>
          {hero.subtitle}
        </p>
        <div className="flex flex-col sm:flex-row items-center gap-4 mt-10 animate-fade-up" style={{ animationDelay: '0.3s' }}>
          <button
            onClick={onBook}
            className="bg-[#9E5A3C] hover:bg-[#874A30] text-white tracking-widest-2 uppercase text-xs px-10 py-4 rounded-full transition-colors duration-300 shadow-lg"
          >
            Book nu
          </button>
          <a
            href="#faciliteter"
            className="border border-white/70 hover:bg-white/10 text-white tracking-widest-2 uppercase text-xs px-10 py-4 rounded-full transition-colors duration-300"
          >
            Udforsk Parken
          </a>
        </div>
      </div>

      <a href="#om" className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/80 animate-soft-bounce z-10">
        <ChevronDown className="w-7 h-7" strokeWidth={1.5} />
      </a>
    </section>
  );
}
