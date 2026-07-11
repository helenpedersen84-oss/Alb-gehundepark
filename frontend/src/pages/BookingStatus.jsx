import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../api';
import { PawPrint, CheckCircle2, Loader2, XCircle, Clock } from 'lucide-react';

export default function BookingStatus() {
  const [params] = useSearchParams();
  const sessionId = params.get('session_id');
  const [state, setState] = useState('checking'); // checking | success | expired | error
  const [booking, setBooking] = useState(null);

  useEffect(() => {
    if (!sessionId) { setState('error'); return; }
    let attempts = 0;
    let stop = false;
    const poll = async () => {
      if (stop) return;
      try {
        const data = await api.getStatus(sessionId);
        if (data.payment_status === 'paid') {
          setBooking(data.booking); setState('success'); return;
        }
        if (data.status === 'expired') { setState('expired'); return; }
      } catch (e) { /* keep polling */ }
      attempts += 1;
      if (attempts >= 8) { setState('error'); return; }
      setTimeout(poll, 2000);
    };
    poll();
    return () => { stop = true; };
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-[#EFE9DE] flex flex-col items-center justify-center px-6">
      <div className="bg-[#F7F3EC] border border-[#E2D9C9] rounded-3xl p-10 max-w-md w-full text-center shadow-xl">
        <div className="flex items-center justify-center gap-2 text-[#333D2E] mb-8">
          <PawPrint className="w-5 h-5" /><span className="font-serif-display text-lg font-semibold">Albøge Hundepark</span>
        </div>

        {state === 'checking' && (
          <>
            <Loader2 className="w-14 h-14 text-[#9E5A3C] animate-spin mx-auto mb-6" />
            <h1 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-2">Bekræfter betaling…</h1>
            <p className="text-[#5F584B] text-sm">Vent venligst mens vi bekræfter din booking.</p>
          </>
        )}
        {state === 'success' && (
          <>
            <CheckCircle2 className="w-16 h-16 text-[#4E7A3E] mx-auto mb-6" />
            <h1 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-2">Booking bekræftet!</h1>
            <p className="text-[#5F584B] text-sm mb-6">Tak! Dit tidspunkt er nu reserveret eksklusivt til dig.</p>
            {booking && (
              <div className="bg-white border border-[#E2D9C9] rounded-2xl p-5 text-left text-sm mb-6 space-y-1.5">
                <div className="flex items-center gap-2 text-[#333D2E] font-medium"><Clock className="w-4 h-4 text-[#9E5A3C]" /> {booking.date} · {String(booking.hour).padStart(2,'0')}:00 – {String(booking.hour).padStart(2,'0')}:45</div>
                <p className="text-[#8A8172]">Navn: {booking.name}</p>
                <p className="text-[#8A8172]">Antal hunde: {booking.dogs}</p>
              </div>
            )}
            <Link to="/" className="inline-block bg-[#9E5A3C] hover:bg-[#874A30] text-white px-8 py-3 rounded-full text-sm transition-colors">Tilbage til forsiden</Link>
          </>
        )}
        {state === 'expired' && (
          <>
            <XCircle className="w-16 h-16 text-[#B4632F] mx-auto mb-6" />
            <h1 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-2">Reservationen udløb</h1>
            <p className="text-[#5F584B] text-sm mb-6">Betalingen blev ikke gennemført i tide, og tidspunktet er frigivet igen.</p>
            <Link to="/" className="inline-block bg-[#9E5A3C] text-white px-8 py-3 rounded-full text-sm">Prøv igen</Link>
          </>
        )}
        {state === 'error' && (
          <>
            <XCircle className="w-16 h-16 text-[#B4632F] mx-auto mb-6" />
            <h1 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-2">Noget gik galt</h1>
            <p className="text-[#5F584B] text-sm mb-6">Vi kunne ikke bekræfte din betaling. Tjek din e-mail eller kontakt os.</p>
            <Link to="/" className="inline-block bg-[#9E5A3C] text-white px-8 py-3 rounded-full text-sm">Tilbage til forsiden</Link>
          </>
        )}
      </div>
    </div>
  );
}
