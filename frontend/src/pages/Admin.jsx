import React, { useEffect, useState } from 'react';
import api from '../api';
import { Link } from 'react-router-dom';
import { PawPrint, Loader2, RefreshCw } from 'lucide-react';

export default function Admin() {
  const [key, setKey] = useState(localStorage.getItem('ahp_admin_key') || '');
  const [authed, setAuthed] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async (k) => {
    setLoading(true); setError('');
    try {
      const data = await api.listBookings(k);
      setBookings(data); setAuthed(true);
      localStorage.setItem('ahp_admin_key', k);
    } catch (e) {
      setError('Forkert adgangskode eller serverfejl.');
      setAuthed(false);
    } finally { setLoading(false); }
  };

  useEffect(() => { if (key) load(key); /* eslint-disable-next-line */ }, []);

  const statusBadge = (b) => {
    const now = Date.now();
    let label = 'Ledig', cls = 'bg-[#E2D9C9] text-[#8A8172]';
    if (b.paid || b.payment_status === 'paid') { label = 'Betalt'; cls = 'bg-[#DCE7D3] text-[#4E7A3E]'; }
    else if (new Date(b.expires_at).getTime() > now) { label = 'Reserveret'; cls = 'bg-[#F0DEC9] text-[#B4632F]'; }
    else { label = 'Udløbet'; cls = 'bg-[#E7DCDC] text-[#9A5252]'; }
    return <span className={`px-3 py-1 rounded-full text-xs font-medium ${cls}`}>{label}</span>;
  };

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
            <h1 className="font-serif-display text-3xl text-[#333D2E] font-semibold mb-6">Bookinger</h1>
            <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
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
