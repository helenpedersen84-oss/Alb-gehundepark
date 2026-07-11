import React from 'react';
import { CONTENT } from '../mock';
import { Home, Leaf, ToyBrick, Droplets, ParkingCircle, CalendarCheck, Smartphone } from 'lucide-react';

const ICONS = { Home, Leaf, ToyBrick, Droplets, ParkingCircle, CalendarCheck, Smartphone };

export default function Features() {
  const { features } = CONTENT;
  return (
    <section id="faciliteter" className="bg-[#E8E1D3] py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-10">
        <div className="text-center mb-16">
          <p className="text-[#A9694A] text-xs tracking-widest-2 uppercase mb-5">{features.kicker}</p>
          <h2 className="font-serif-display text-[#333D2E] text-4xl md:text-5xl leading-tight">
            <span className="font-semibold">{features.title1} </span>
            <span className="italic font-medium">{features.title2}</span>
          </h2>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.items.map((item, i) => {
            const Icon = ICONS[item.icon] || Home;
            return (
              <div
                key={i}
                className="group bg-[#F7F3EC] rounded-2xl p-8 border border-[#E2D9C9] hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-[#EADFCF] flex items-center justify-center mb-6 group-hover:bg-[#9E5A3C] transition-colors duration-300">
                  <Icon className="w-6 h-6 text-[#9E5A3C] group-hover:text-white transition-colors duration-300" strokeWidth={1.6} />
                </div>
                <h3 className="font-serif-display text-[#333D2E] text-xl font-semibold mb-3">{item.title}</h3>
                <p className="text-[#5F584B] text-sm leading-relaxed">{item.text}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
