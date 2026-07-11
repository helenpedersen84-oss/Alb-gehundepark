import React from 'react';
import { CONTENT } from '../mock';
import { MapPin, Clock, Car, Navigation } from 'lucide-react';

export default function Location() {
  const { location } = CONTENT;
  const mapSrc = `https://www.openstreetmap.org/export/embed.html?bbox=${location.lng - 0.03}%2C${location.lat - 0.018}%2C${location.lng + 0.03}%2C${location.lat + 0.018}&layer=mapnik&marker=${location.lat}%2C${location.lng}`;
  const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(location.destination)}`;

  const cards = [
    { icon: MapPin, title: 'Adresse', lines: location.address },
    { icon: Clock, title: 'Åbningstider', lines: location.hours },
    { icon: Car, title: 'Parkering', lines: location.parking },
  ];

  return (
    <section id="lokation" className="bg-[#E8E1D3] py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-10">
        <div className="text-center mb-16">
          <p className="text-[#A9694A] text-xs tracking-widest-2 uppercase mb-5">{location.kicker}</p>
          <h2 className="font-serif-display text-[#333D2E] text-4xl md:text-5xl leading-tight">
            <span className="font-semibold">{location.title1} </span>
            <span className="italic font-medium">{location.title2}</span>
          </h2>
        </div>

        <div className="grid lg:grid-cols-2 gap-10 items-stretch">
          <div className="relative rounded-3xl overflow-hidden shadow-lg border border-[#E2D9C9] min-h-[360px]">
            <iframe
              title="Kort over Albøge Hundepark"
              src={mapSrc}
              className="w-full h-full min-h-[360px]"
              style={{ border: 0 }}
              loading="lazy"
            />
            <a
              href={directionsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-[#9E5A3C] hover:bg-[#874A30] text-white text-sm px-6 py-3 rounded-full shadow-lg transition-colors duration-300 flex items-center gap-2 whitespace-nowrap"
            >
              <Navigation className="w-4 h-4" strokeWidth={1.8} /> Få rutevejledning
            </a>
          </div>

          <div className="grid gap-6 content-center">
            {cards.map((c, i) => (
              <div key={i} className="bg-[#F7F3EC] rounded-2xl p-7 border border-[#E2D9C9] flex items-start gap-5">
                <div className="w-12 h-12 rounded-xl bg-[#EADFCF] flex items-center justify-center shrink-0">
                  <c.icon className="w-6 h-6 text-[#9E5A3C]" strokeWidth={1.6} />
                </div>
                <div>
                  <h3 className="font-serif-display text-[#333D2E] text-lg font-semibold mb-1">{c.title}</h3>
                  {c.lines.map((l, j) => (
                    <p key={j} className="text-[#5F584B] text-sm">{l}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
