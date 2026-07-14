import React, { useEffect, useState } from 'react';
import api from '../api';
import { Link } from 'react-router-dom';
import { PawPrint, Loader2, RefreshCw, Save, Tag, FileText, CreditCard, Trash2, LogOut } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

export default function Admin() {
  const { toast } = useToast();
  const [key, setKey] = useState(localStorage.getItem('ahp_admin_key') || '');
  const [email, setEmail] = useState(localStorage.getItem('ahp_admin_email') || '');
  const [password, setPassword] = useState('');
  const [authed, setAuthed] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [prices, setPrices] = useState({ single_visit_price: 60, extra_dog_price: 30, ten_trip_price: 560 });
  const [savingPrices, setSavingPrices] = useState(false);
  const [content, setContent] = useState(null);
  const [savingContent, setSavingContent] = useState(false);
  const [stripeCfg, setStripeCfg] = useState(null);
  const [stripeInputs, setStripeInputs] = useState({ stripe_api_key: '', stripe_webhook_secret: '', edit_code: '' });
  const [savingStripe, setSavingStripe] = useState(false);

  const load = async (k) => {
    setLoading(true); setError('');
    try {
      const data = await api.listBookings(k);
      setBookings(data); setAuthed(true);
      const s = await api.getSettings();
      setPrices({ single_visit_price: s.single_visit_price, extra_dog_price: s.extra_dog_price, ten_trip_price: s.ten_trip_price });
      const c = await api.getContent();
      setContent(c);
      const sc = await api.getStripeConfig(k);
      setStripeCfg(sc);
    } catch (e) {
      const status = e?.response?.status;
      if (status === 401) {
        localStorage.removeItem('ahp_admin_key');
        setKey('');
        setError('Session udløbet. Log ind igen.');
      } else if (status) {
        setError(`Serverfejl (${status}). Prøv igen senere.`);
      } else {
        setError('Kunne ikke få forbindelse til serveren. Tjek at backend kører, og at REACT_APP_BACKEND_URL er sat korrekt i Vercel.');
      }
      setAuthed(false);
    } finally { setLoading(false); }
  };

  const doLogin = async () => {
    setLoading(true); setError('');
    try {
      const { token } = await api.adminLogin(email.trim(), password);
      setKey(token);
      setPassword('');
      localStorage.setItem('ahp_admin_key', token);
      localStorage.setItem('ahp_admin_email', email.trim());
      await load(token);
    } catch (e) {
      const status = e?.response?.status;
      if (status === 401) {
        setError('Forkert e-mail eller adgangskode.');
      } else if (status) {
        setError(`Serverfejl (${status}). Prøv igen senere.`);
      } else {
        setError('Kunne ikke få forbindelse til serveren.');
      }
      setLoading(false);
    }
  };

  useEffect(() => {
    if (key) load(key);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  const saveStripe = async () => {
    const payload = {};
    if (stripeInputs.stripe_api_key.trim()) payload.stripe_api_key = stripeInputs.stripe_api_key.trim();
    if (stripeInputs.stripe_webhook_secret.trim()) payload.stripe_webhook_secret = stripeInputs.stripe_webhook_secret.trim();
    if (!payload.stripe_api_key && !payload.stripe_webhook_secret) {
      toast({ title: 'Indtast mindst én nøgle' });
      return;
    }
    if (!stripeInputs.edit_code.trim()) {
      toast({ title: 'Hemmelig kode påkrævet', description: 'Indtast den hemmelige kode for at ændre Stripe-nøgler.' });
      return;
    }
    payload.edit_code = stripeInputs.edit_code.trim();
    setSavingStripe(true);
    try {
      const sc = await api.updateStripeConfig(key, payload);
      setStripeCfg(sc);
      setStripeInputs({ stripe_api_key: '', stripe_webhook_secret: '', edit_code: '' });
      toast({ title: 'Stripe-nøgler gemt', description: 'Betalinger bruger nu de nye nøgler med det samme.' });
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Kunne ikke gemme nøglerne.';
      toast({ title: 'Fejl', description: msg });
    } finally { setSavingStripe(false); }
  };

  const statusBadge = (b) => {
    const s = b.display_status;
    if (s === 'paid') return <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#DCE7D3] text-[#4E7A3E]">Betalt</span>;
    if (s === 'locked') return <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#F0DEC9] text-[#B4632F]">Reserveret</span>;
    return <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#E7DCDC] text-[#9A5252]">Udløbet</span>;
  };

  const deleteOne = async (b) => {
    if (!window.confirm('Slet denne udløbne reservation permanent?')) return;
    try {
      await api.deleteBooking(key, b.booking_id);
      setBookings((prev) => prev.filter((x) => x.booking_id !== b.booking_id));
      toast({ title: 'Reservation slettet' });
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Kunne ikke slette.';
      toast({ title: 'Fejl', description: msg });
    }
  };

  const purgeAll = async () => {
    if (!window.confirm('Slet ALLE udløbne reservationer permanent?')) return;
    try {
      const res = await api.purgeExpired(key);
      toast({ title: 'Udløbne ryddet', description: `${res.deleted || 0} slettet.` });
      load(key);
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Kunne ikke rydde udløbne.';
      toast({ title: 'Fejl', description: msg });
    }
  };

  const logout = () => {
    localStorage.removeItem('ahp_admin_key');
    setKey('');
    setPassword('');
    setAuthed(false);
    setBookings([]);
    setContent(null);
    setStripeCfg(null);
    setError('');
    toast({ title: 'Du er logget ud' });
  };

  const priceFields = [
    { key: 'single_visit_price', label: 'Enkeltbesøg (pr. time / 1 hund)' },
    { key: 'extra_dog_price', label: 'Ekstra hund (pr. styk)' },
  ];

  return (
    <div className="min-h-screen bg-[#EFE9DE]">
      <div className="bg-[#333D2E] px-6 lg:px-10 py-5 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-white"><PawPrint className="w-5 h-5" /><span className="font-serif-display text-lg font-semibold">Albøge Hundepark · Admin</span></Link>
        {authed && (
          <div className="flex items-center gap-4">
            <button data-testid="admin-refresh-btn" onClick={() => load(key)} className="text-white/80 hover:text-white flex items-center gap-2 text-sm"><RefreshCw className="w-4 h-4" /> Opdater</button>
            <button data-testid="admin-logout-btn" onClick={logout} className="text-white/80 hover:text-white flex items-center gap-2 text-sm"><LogOut className="w-4 h-4" /> Log ud</button>
          </div>
        )}
      </div>

      <div className="max-w-6xl mx-auto px-6 lg:px-10 py-10">
        {!authed ? (
          <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-3xl p-8 max-w-sm mx-auto mt-16">
            <h1 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-5">Admin login</h1>
            <input
              data-testid="admin-email-input"
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && doLogin()}
              placeholder="E-mail"
              className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
            />
            <input
              data-testid="admin-password-input"
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && doLogin()}
              placeholder="Adgangskode"
              className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
            />
            {error && <p className="text-[#9A5252] text-sm mb-3" data-testid="admin-login-error">{error}</p>}
            <button data-testid="admin-login-btn" onClick={doLogin} disabled={loading} className="w-full bg-[#9E5A3C] hover:bg-[#874A30] text-white py-3 rounded-full text-sm flex items-center justify-center gap-2 disabled:opacity-60">
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
                      <Field label="Facebook gruppe-link" value={content.contact.facebook_url} onChange={(v) => setField('contact', 'facebook_url', v)} />
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

            {/* Stripe keys editor */}
            {stripeCfg && (
              <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-2xl p-7 mb-10">
                <div className="flex items-center gap-2 mb-5">
                  <CreditCard className="w-5 h-5 text-[#9E5A3C]" />
                  <h2 className="font-serif-display text-2xl text-[#333D2E] font-semibold">Stripe-nøgler</h2>
                </div>
                <div className="bg-[#EADFCF] rounded-xl px-5 py-4 mb-6 text-sm text-[#5F584B]">
                  <p className="mb-1">
                    <span className="font-medium text-[#333D2E]">Aktiv nøgle: </span>
                    {stripeCfg.stripe_api_key_set ? (
                      <>
                        <span className={`font-medium ${stripeCfg.stripe_api_key_mode === 'live' ? 'text-[#4E7A3E]' : 'text-[#B4632F]'}`}>
                          {(stripeCfg.stripe_api_key_mode || 'ukendt').toUpperCase()}
                        </span>
                        {' '}· slutter på <code className="bg-white px-1.5 py-0.5 rounded">…{stripeCfg.stripe_api_key_last4}</code>
                        {' '}(kilde: {stripeCfg.source === 'admin' ? 'admin' : 'server'})
                      </>
                    ) : <span className="text-[#9A5252]">Ingen nøgle sat!</span>}
                  </p>
                  <p><span className="font-medium text-[#333D2E]">Webhook-secret: </span>{stripeCfg.stripe_webhook_secret_set ? 'sat ✓' : 'ikke sat'}</p>
                </div>
                <p className="text-[#8A8172] text-sm mb-4">Indsæt nye nøgler for at opdatere (efterlad tomt for at beholde de nuværende). Nøglerne bruges med det samme til betalinger og gemmes sikkert i databasen.</p>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-[#5F584B] mb-1.5">Hemmelig API-nøgle (starter med sk_live_ eller sk_test_)</label>
                    <input
                      type="password" autoComplete="off" value={stripeInputs.stripe_api_key}
                      onChange={(e) => setStripeInputs({ ...stripeInputs, stripe_api_key: e.target.value })}
                      placeholder="sk_live_..."
                      className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-[#5F584B] mb-1.5">Webhook-secret (starter med whsec_)</label>
                    <input
                      type="password" autoComplete="off" value={stripeInputs.stripe_webhook_secret}
                      onChange={(e) => setStripeInputs({ ...stripeInputs, stripe_webhook_secret: e.target.value })}
                      placeholder="whsec_..."
                      className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
                    />
                  </div>
                  <div className="border-t border-[#E2D9C9] pt-4">
                    <label className="block text-xs text-[#5F584B] mb-1.5">Hemmelig kode (påkrævet for at ændre Stripe-nøgler)</label>
                    <input
                      data-testid="admin-stripe-code-input"
                      type="password" autoComplete="off" value={stripeInputs.edit_code}
                      onChange={(e) => setStripeInputs({ ...stripeInputs, edit_code: e.target.value })}
                      placeholder="Hemmelig kode"
                      className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40"
                    />
                  </div>
                </div>
                <button onClick={saveStripe} disabled={savingStripe} className="mt-6 bg-[#9E5A3C] hover:bg-[#874A30] text-white px-8 py-3 rounded-full text-sm flex items-center gap-2 disabled:opacity-60">
                  {savingStripe ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Gem Stripe-nøgler
                </button>
              </div>
            )}

            <div className="flex items-center justify-between mb-6">
              <h1 className="font-serif-display text-3xl text-[#333D2E] font-semibold">Bookinger</h1>
              {bookings.some((b) => b.display_status === 'expired') && (
                <button
                  data-testid="admin-purge-expired-btn"
                  onClick={purgeAll}
                  className="flex items-center gap-2 text-sm bg-[#E7DCDC] hover:bg-[#dcc9c9] text-[#9A5252] px-4 py-2 rounded-full transition-colors"
                >
                  <Trash2 className="w-4 h-4" /> Ryd udløbne
                </button>
              )}
            </div>
            <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-2xl overflow-hidden overflow-x-auto">
              <table className="w-full text-sm min-w-[780px]">
                <thead className="bg-[#E8E1D3] text-[#5F584B]">
                  <tr>
                    {['Dato', 'Tid', 'Navn', 'Kontakt', 'Hunde', 'Beløb', 'Status', ''].map((h, idx) => (
                      <th key={idx} className="text-left px-5 py-3 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bookings.length === 0 && (
                    <tr><td colSpan={8} className="px-5 py-10 text-center text-[#8A8172]">Ingen bookinger endnu.</td></tr>
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
                      <td className="px-5 py-3">
                        {b.display_status !== 'paid' && (
                          <button
                            data-testid={`admin-delete-booking-${b.booking_id}`}
                            onClick={() => deleteOne(b)}
                            title="Slet reservation"
                            className="text-[#9A5252] hover:text-[#7a3d3d] p-1.5 rounded-lg hover:bg-[#E7DCDC] transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
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
