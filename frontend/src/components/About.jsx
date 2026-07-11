import React from 'react';
import { CONTENT } from '../mock';

export default function About() {
  const { about } = CONTENT;
  return (
    <section id="om" className="bg-[#EFE9DE] py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 grid md:grid-cols-2 gap-14 md:gap-20 items-center">
        <div>
          <p className="text-[#A9694A] text-xs tracking-widest-2 uppercase mb-5">{about.kicker}</p>
          <h2 className="font-serif-display text-[#333D2E] text-4xl md:text-5xl leading-tight mb-8">
            <span className="block font-semibold">{about.title1}</span>
            <span className="block italic font-medium">{about.title2}</span>
          </h2>
          <p className="text-[#5F584B] leading-relaxed mb-5 max-w-md">{about.p1}</p>
          <p className="text-[#5F584B] leading-relaxed max-w-md">{about.p2}</p>
        </div>
        <div className="relative">
          <div className="overflow-hidden rounded-3xl shadow-xl">
            <img src={about.image} alt="Morgendug på græs i parken" className="w-full h-[520px] object-cover hover:scale-105 transition-transform duration-1000" />
          </div>
        </div>
      </div>
    </section>
  );
}
