import React, { useState } from 'react';
import { useContent } from '../ContentContext';
import { MapPin, Phone, Mail, Loader2 } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import api from '../api';

export default function Contact() {
  const { contact } = useContent();
  const { toast } = useToast();
  const [form, setForm] = useState({ name: '', email: '', phone: '', message: '' });
  const [sending, setSending] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) {
      toast({ title: 'Udfyld venligst navn, e-mail og besked.' });
      return;
    }
    setSending(true);
    try {
      await api.sendContact(form);
      toast({ title: 'Tak for din besked!', description: 'Vi vender tilbage hurtigst muligt.' });
      setForm({ name: '', email: '', phone: '', message: '' });
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Beskeden kunne ikke sendes. Prøv igen senere.';
      toast({ title: 'Ups!', description: msg });
    } finally {
      setSending(false);
    }
  };

  const info = [
    { icon: MapPin, text: contact.address },
    { icon: Phone, text: contact.phone },
    { icon: Mail, text: contact.email },
  ];

  return (
    <section id="kontakt" className="bg-[#EFE9DE] py-24 md:py-32">
      <div className="max-w-6xl mx-auto px-6 lg:px-10">
        <div className="text-center mb-16">
          <p className="text-[#A9694A] text-xs tracking-widest-2 uppercase mb-5">{contact.kicker}</p>
          <h2 className="font-serif-display text-[#333D2E] text-4xl md:text-5xl leading-tight mb-5">
            <span className="font-semibold">{contact.title1} </span>
            <span className="italic font-medium">{contact.title2}</span>
          </h2>
          <p className="text-[#5F584B] max-w-lg mx-auto">{contact.subtitle}</p>
        </div>

        <div className="grid md:grid-cols-2 gap-12">
          <div className="flex flex-col justify-center gap-6">
            {info.map((it, i) => (
              <div key={i} className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-xl bg-[#EADFCF] flex items-center justify-center shrink-0">
                  <it.icon className="w-5 h-5 text-[#9E5A3C]" strokeWidth={1.7} />
                </div>
                <span className="text-[#4A4437]">{it.text}</span>
              </div>
            ))}
          </div>

          <form onSubmit={submit} className="bg-[#F7F3EC] rounded-3xl p-8 border border-[#E2D9C9] space-y-4">
            <input
              value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Dit navn"
              className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
            />
            <input
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="E-mailadresse" type="email"
              className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
            />
            <input
              value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
              placeholder="Telefonnummer (valgfrit)"
              className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
            />
            <textarea
              value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })}
              placeholder="Besked" rows={4}
              className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40 resize-none"
            />
            <button type="submit" disabled={sending} className="w-full bg-[#9E5A3C] hover:bg-[#874A30] text-white py-3.5 rounded-full text-sm tracking-wide transition-colors duration-300 flex items-center justify-center gap-2 disabled:opacity-60">
              {sending && <Loader2 className="w-4 h-4 animate-spin" />} Send besked
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
