import React, { useEffect, useState } from 'react';
import { CONTENT } from '../mock';
import api from '../api';
import { Check } from 'lucide-react';

export default function Pricing({ onBook }) {
  const { pricing } = CONTENT;
  const [prices, setPrices] = useState({ single_visit_price: 60, extra_dog_price: 30, ten_trip_price: 560 });

  useEffect(() => {
    api.getSettings().then(setPrices).catch(() => {});
  }, []);

  const plans = [
    {
      name: 'Enkeltbesøg', price: `${prices.single_visit_price} kr.`, unit: 'pr. time / 1 hund', popular: true,
      desc: `Perfekt til den spontane legetur. Ekstra hunde tilføjes for ${prices.extra_dog_price} kr. pr. styk.`,
      features: ['1 hund inkluderet', '45 min. eksklusiv adgang', `Ekstra hund: ${prices.extra_dog_price} kr.`, 'Gratis parkering'],
      cta: 'Book nu',
    },
    {
      name: 'Heldagsleje', price: 'Kontakt os', unit: 'for pris og info', popular: false,
      desc: 'Parken kan lejes til træning, kurser og andre arrangementer hele dagen.',
      features: ['Eksklusiv adgang hele dagen', 'Egnet til træning og kurser', 'Fleksible muligheder', 'Kontakt for aftale'],
      cta: 'Kontakt os',
    },
  ];

  return (
    <section id="priser" className="bg-[#EFE9DE] py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6 lg:px-10">
        <div className="text-center mb-16">
          <p className="text-[#A9694A] text-xs tracking-widest-2 uppercase mb-5">{pricing.kicker}</p>
          <h2 className="font-serif-display text-[#333D2E] text-4xl md:text-5xl leading-tight mb-5">
            <span className="font-semibold">{pricing.title1} </span>
            <span className="italic font-medium">{pricing.title2}</span>
          </h2>
          <p className="text-[#5F584B] max-w-lg mx-auto">{pricing.subtitle}</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {plans.map((plan, i) => (
            <div
              key={i}
              className={`relative rounded-3xl p-8 flex flex-col transition-all duration-300 hover:-translate-y-1.5 ${
                plan.popular
                  ? 'bg-[#333D2E] text-white shadow-2xl md:scale-105'
                  : 'bg-[#F7F3EC] text-[#333D2E] border border-[#E2D9C9] hover:shadow-lg'
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#9E5A3C] text-white text-[10px] tracking-widest-2 uppercase px-4 py-1.5 rounded-full">
                  Mest populær
                </span>
              )}
              <h3 className={`font-serif-display text-2xl font-semibold mb-4 ${plan.popular ? 'text-white' : 'text-[#333D2E]'}`}>
                {plan.name}
              </h3>
              <div className="mb-5">
                <span className="font-serif-display text-4xl font-semibold">{plan.price}</span>
                <span className={`block text-sm mt-1 ${plan.popular ? 'text-white/70' : 'text-[#8A8172]'}`}>{plan.unit}</span>
              </div>
              <p className={`text-sm leading-relaxed mb-7 ${plan.popular ? 'text-white/80' : 'text-[#5F584B]'}`}>{plan.desc}</p>
              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((f, j) => (
                  <li key={j} className="flex items-start gap-3 text-sm">
                    <Check className={`w-4 h-4 mt-0.5 shrink-0 ${plan.popular ? 'text-[#C98A5E]' : 'text-[#9E5A3C]'}`} strokeWidth={2.2} />
                    <span className={plan.popular ? 'text-white/90' : 'text-[#5F584B]'}>{f}</span>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => plan.cta === 'Book nu' ? onBook() : (window.location.hash = '#kontakt')}
                className={`w-full py-3.5 rounded-full text-sm tracking-wide transition-colors duration-300 ${
                  plan.popular
                    ? 'bg-[#9E5A3C] hover:bg-[#874A30] text-white'
                    : 'bg-[#333D2E] hover:bg-[#252D20] text-white'
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
