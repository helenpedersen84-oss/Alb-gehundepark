import React, { useEffect, useState } from 'react';
import api from '../api';
import { Link } from 'react-router-dom';
import { PawPrint, Loader2, RefreshCw, Save, Tag, FileText } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

export default function Admin() {
  const { toast } = useToast();
  const [key, setKey] = useState(localStorage.getItem('ahp_admin_key') || '');
  const [authed, setAuthed] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [prices, setPrices] = useState({ single_visit_price: 60, extra_dog_price: 30, ten_trip_price: 560 });
  const [savingPrices, setSavingPrices] = useState(false);
  const [content, setContent] = useState(null);
  const [savingContent, setSavingContent] = useState(false);

  const load = async (k) => {
    setLoading(true); setError('');
    try {
      const data = await api.listBookings(k);
      setBookings(data); setAuthed(true);
      localStorage.setItem('ahp_admin_key', k);
      const s = await api.getSettings();
      setPrices({ single_visit_price: s.single_visit_price, extra_dog_price: s.extra_dog_price, ten_trip_price: s.ten_trip_price });
      const c = await api.getContent();
      setContent(c);
    } catch (e) {
      setError('Forkert adgangskode eller serverfejl.');
      setAuthed(false);
    } finally { setLoading(false); }
  };

  useEffect(() => { if (key) load(key); /* eslint-disable-next-line */ }, []);

  const savePrices = async () => {
    setSavingPrices(true);
    try {
      await api.updateSettings(key, {
        single_visit_price: Number(prices.single_visit_price),
        extra_dog_price: Number(prices.extra_dog_price),
        ten_trip_price: Number(prices.ten_trip_price),
      });
      toast({ title: 'Priser gemt', description: 'Ændringerne er nu live på hjemmesiden.' });
    } catch (e) {
      toast({ title: 'Kunne ikke gemme priser', description: 'Prøv igen.' });
    } finally { setSavingPrices(false); }
  };

  const setField = (section, field, value) => {
    setContent((c) => ({ ...c, [section]: { ...c[section], [field]: value } }));
  };

  const saveContent = async () => {
    setSavingContent(true);
    try {
      const updated = await api.updateContent(key, content);
      setContent(updated);
      toast({ title: 'Indhold gemt', description: 'Teksterne er nu live på hjemmesiden.' });
    } catch (e) {
      toast({ title: 'Kunne ikke gemme indhold', description: 'Prøv igen.' });
    } finally { setSavingContent(false); }
  };

  const statusBadge = (b) => {
    const s = b.display_status;
    if (s === 'paid') return <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#DCE7D3] text-[#4E7A3E]">Betalt</span>;
    if (s === 'locked') return <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#F0DEC9] text-[#B4632F]">Reserveret</span>;
    return <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#E7DCDC] text-[#9A5252]">Udløbet</span>;
  };

  const priceFields = [
    { key: 'single_visit_price', label: 'Enkeltbesøg (pr. time / 1 hund)' },
    { key: 'extra_dog_price', label: 'Ekstra hund (pr. styk)' },
    { key: 'ten_trip_price', label: '10-turskort (samlet pris)' },
  ];

  return (
    <div className="min-h-screen bg-[#EFE9DE]">
      <div className="bg-[#333D2E] px-6 lg:px-10 py-5 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-white"><PawPrint className="w-5 h-5" /><span className="font-serif-display text-lg font-semibold">Albøge Hundepark · Admin</span></Link>
        {authed && (
          <button onClick={() => load(key)} className="text-white/80 hover:text-white flex items-center gap-2 text-sm"><RefreshCw className="w-4 h-4" /> Opdater</button>
        )}
      </div>

      <div className="max-w-6xl mx-auto px-6 lg:px-10 py-10">
        {!authed ? (
          <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-3xl p-8 max-w-sm mx-auto mt-16">
            <h1 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-5">Admin login</h1>
            <input type="password" value={key} onChange={(e) => setKey(e.target.value)} placeholder="Adgangskode" className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40" />
            {error && <p className="text-[#9A5252] text-sm mb-3">{error}</p>}
            <button onClick={() => load(key)} disabled={loading} className="w-full bg-[#9E5A3C] hover:bg-[#874A30] text-white py-3 rounded-full text-sm flex items-center justify-center gap-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />} Log ind
            </button>
          </div>
        ) : (
          <>
            {/* Pricing editor */}
            <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-2xl p-7 mb-10">
              <div className="flex items-center gap-2 mb-5">
                <Tag className="w-5 h-5 text-[#9E5A3C]" />
                <h2 className="font-serif-display text-2xl text-[#333D2E] font-semibold">Priser</h2>
              </div>
              <p className="text-[#8A8172] text-sm mb-6">Rediger priserne herunder. De opdateres live på hjemmesiden kort efter du gemmer.</p>
              <div className="grid sm:grid-cols-3 gap-5">
                {priceFields.map((f) => (
                  <div key={f.key}>
                    <label className="block text-xs text-[#5F584B] mb-1.5">{f.label}</label>
                    <div className="relative">
                      <input
                        type="number" min="0" value={prices[f.key]}
                        onChange={(e) => setPrices({ ...prices, [f.key]: e.target.value })}
                        className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
                      />
                      <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[#8A8172] text-sm">kr.</span>
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={savePrices} disabled={savingPrices} className="mt-6 bg-[#9E5A3C] hover:bg-[#874A30] text-white px-8 py-3 rounded-full text-sm flex items-center gap-2 disabled:opacity-60">
                {savingPrices ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Gem priser
              </button>
            </div>

            {/* Content editor */}
            {content && (
              <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-2xl p-7 mb-10">
                <div className="flex items-center gap-2 mb-5">
                  <FileText className="w-5 h-5 text-[#9E5A3C]" />
                  <h2 className="font-serif-display text-2xl text-[#333D2E] font-semibold">Indhold & kontaktoplysninger</h2>
                </div>
                <p className="text-[#8A8172] text-sm mb-6">Rediger hjemmesidens tekster og kontaktoplysninger. De opdateres live kort efter du gemmer.</p>

                <div className="space-y-8">
                  {/* Contact info */}
                  <div>
                    <h3 className="text-[#333D2E] font-medium mb-3 text-sm uppercase tracking-wide">Kontaktoplysninger</h3>
                    <div className="grid sm:grid-cols-3 gap-4">
                      <Field label="Adresse" value={content.contact.address} onChange={(v) => setField('contact', 'address', v)} />
                      <Field label="Telefon" value={content.contact.phone} onChange={(v) => setField('contact', 'phone', v)} />
                      <Field label="E-mail" value={content.contact.email} onChange={(v) => setField('contact', 'email', v)} />
                    </div>
                    <div className="mt-4">
                      <Field label="Kontakt-undertekst" value={content.contact.subtitle} onChange={(v) => setField('contact', 'subtitle', v)} textarea />
                    </div>
                  </div>

                  {/* Hero */}
                  <div>
                    <h3 className="text-[#333D2E] font-medium mb-3 text-sm uppercase tracking-wide">Forside (hero)</h3>
                    <div className="grid sm:grid-cols-3 gap-4">
                      <Field label="Overskrift (lille)" value={content.hero.kicker} onChange={(v) => setField('hero', 'kicker', v)} />
                      <Field label="Titel linje 1" value={content.hero.title1} onChange={(v) => setField('hero', 'title1', v)} />
                      <Field label="Titel linje 2 (kursiv)" value={content.hero.title2} onChange={(v) => setField('hero', 'title2', v)} />
                    </div>
                    <div className="mt-4">
                      <Field label="Undertekst" value={content.hero.subtitle} onChange={(v) => setField('hero', 'subtitle', v)} textarea />
                    </div>
                  </div>

                  {/* About */}
                  <div>
                    <h3 className="text-[#333D2E] font-medium mb-3 text-sm uppercase tracking-wide">Om parken</h3>
                    <div className="grid sm:grid-cols-3 gap-4">
                      <Field label="Overskrift (lille)" value={content.about.kicker} onChange={(v) => setField('about', 'kicker', v)} />
                      <Field label="Titel linje 1" value={content.about.title1} onChange={(v) => setField('about', 'title1', v)} />
                      <Field label="Titel linje 2 (kursiv)" value={content.about.title2} onChange={(v) => setField('about', 'title2', v)} />
                    </div>
                    <div className="grid sm:grid-cols-2 gap-4 mt-4">
                      <Field label="Afsnit 1" value={content.about.p1} onChange={(v) => setField('about', 'p1', v)} textarea />
                      <Field label="Afsnit 2" value={content.about.p2} onChange={(v) => setField('about', 'p2', v)} textarea />
                    </div>
                  </div>
                </div>

                <button onClick={saveContent} disabled={savingContent} className="mt-7 bg-[#9E5A3C] hover:bg-[#874A30] text-white px-8 py-3 rounded-full text-sm flex items-center gap-2 disabled:opacity-60">
                  {savingContent ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Gem indhold
                </button>
              </div>
            )}

            <h1 className="font-serif-display text-3xl text-[#333D2E] font-semibold mb-6">Bookinger</h1>
            <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-2xl overflow-hidden overflow-x-auto">
              <table className="w-full text-sm min-w-[720px]">
                <thead className="bg-[#E8E1D3] text-[#5F584B]">
                  <tr>
                    {['Dato', 'Tid', 'Navn', 'Kontakt', 'Hunde', 'Beløb', 'Status'].map((h) => (
                      <th key={h} className="text-left px-5 py-3 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bookings.length === 0 && (
                    <tr><td colSpan={7} className="px-5 py-10 text-center text-[#8A8172]">Ingen bookinger endnu.</td></tr>
                  )}
                  {bookings.map((b, i) => (
                    <tr key={i} className="border-t border-[#E2D9C9]">
                      <td className="px-5 py-3 text-[#4A4437]">{b.date}</td>
                      <td className="px-5 py-3 text-[#4A4437]">{String(b.hour).padStart(2,'0')}:00–{String(b.hour).padStart(2,'0')}:45</td>
                      <td className="px-5 py-3 text-[#4A4437]">{b.name}</td>
                      <td className="px-5 py-3 text-[#8A8172]">{b.email}<br/>{b.phone}</td>
                      <td className="px-5 py-3 text-[#4A4437]">{b.dogs}</td>
                      <td className="px-5 py-3 text-[#4A4437]">{b.amount || '-'} kr.</td>
                      <td className="px-5 py-3">{statusBadge(b)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, textarea }) {
  return (
    <div>
      <label className="block text-xs text-[#5F584B] mb-1.5">{label}</label>
      {textarea ? (
        <textarea
          value={value || ''} onChange={(e) => onChange(e.target.value)} rows={3}
          className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40 resize-none"
        />
      ) : (
        <input
          value={value || ''} onChange={(e) => onChange(e.target.value)}
          className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
        />
      )}
    </div>
  );
}
