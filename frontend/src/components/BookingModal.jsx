import React, { useEffect, useMemo, useState } from 'react';
import { Dialog, DialogContent, DialogTitle } from './ui/dialog';
import { Calendar } from './ui/calendar';
import api from '../api';
import { useToast } from '../hooks/use-toast';
import { PawPrint, Clock, Loader2, Minus, Plus, ArrowLeft, ShieldCheck } from 'lucide-react';

function fmtDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function BookingModal({ open, onClose }) {
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [date, setDate] = useState(new Date());
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotsError, setSlotsError] = useState(false);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ name: '', email: '', phone: '', dogs: 1 });
  const [booking, setBooking] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [prices, setPrices] = useState({ single_visit_price: 60, extra_dog_price: 30 });

  const dateStr = useMemo(() => fmtDate(date), [date]);

  useEffect(() => {
    if (!open) return;
    setStep(1); setSelected(null); setBooking(null);
    setForm({ name: '', email: '', phone: '', dogs: 1 });
    api.getSettings().then(setPrices).catch(() => {});
  }, [open]);

  useEffect(() => {
    if (!open || step !== 1) return;
    let active = true;
    setLoadingSlots(true);
    setSlotsError(false);
    api.getSlots(dateStr)
      .then((s) => { if (active) { setSlots(s); setLoadingSlots(false); } })
      .catch(() => { if (active) { setSlots([]); setSlotsError(true); setLoadingSlots(false); } });
    return () => { active = false; };
  }, [open, step, dateStr]);

  // countdown on payment step
  useEffect(() => {
    if (step !== 3 || !booking) return;
    const expMs = booking?.expires_at ? new Date(booking.expires_at).getTime() : NaN;
    if (Number.isNaN(expMs)) { setSecondsLeft(0); return; }
    const tick = () => {
      const left = Math.max(0, Math.floor((expMs - Date.now()) / 1000));
      setSecondsLeft(left);
      if (left <= 0) {
        toast({ title: 'Reservationen udløb', description: 'Tidspunktet er frigivet igen.' });
        setStep(1); setBooking(null);
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, booking]);

  const amount = form.dogs > 1 ? prices.single_visit_price + (form.dogs - 1) * prices.extra_dog_price : prices.single_visit_price;

  const proceedToForm = () => {
    if (!selected) { toast({ title: 'Vælg venligst et tidspunkt.' }); return; }
    setStep(2);
  };

  const createBooking = async () => {
    if (!form.name || !form.email) { toast({ title: 'Udfyld navn og e-mail.' }); return; }
    setSubmitting(true);
    try {
      const res = await api.createBooking({
        date: dateStr, hour: selected.hour, name: form.name,
        email: form.email, phone: form.phone, dogs: form.dogs,
      });
      setBooking(res);
      setStep(3);
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Kunne ikke reservere tidspunktet.';
      toast({ title: msg });
      // refresh slots
      api.getSlots(dateStr).then(setSlots);
      setSelected(null); setStep(1);
    } finally { setSubmitting(false); }
  };

  const pay = async () => {
    setSubmitting(true);
    try {
      const { url } = await api.createCheckout({ booking_id: booking.booking_id, origin: window.location.origin });
      window.location.href = url;
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Kunne ikke starte betaling. Tjek forbindelsen til serveren.';
      toast({ title: 'Betaling mislykkedes', description: msg });
      setSubmitting(false);
    }
  };

  const mm = String(Math.floor(secondsLeft / 60)).padStart(2, '0');
  const ss = String(secondsLeft % 60).padStart(2, '0');

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="w-[calc(100%-1.5rem)] max-w-2xl bg-[#F7F3EC] border-[#E2D9C9] p-0 overflow-hidden max-h-[92vh] overflow-y-auto">
        <DialogTitle className="sr-only">Book din tid</DialogTitle>
        <div className="bg-[#333D2E] px-5 py-5 md:px-8 md:py-6 flex items-center gap-3">
          <PawPrint className="w-6 h-6 text-[#C98A5E] shrink-0" />
          <div>
            <h3 className="font-serif-display text-white text-xl md:text-2xl font-semibold">Book din tid</h3>
            <p className="text-white/60 text-xs tracking-wide">45 minutters eksklusiv adgang – ingen andre på pladsen</p>
          </div>
        </div>

        <div className="p-5 md:p-8">
          {/* Steps indicator */}
          <div className="flex items-center gap-2 mb-7">
            {[1, 2, 3].map((n) => (
              <div key={n} className={`h-1.5 flex-1 rounded-full transition-colors ${step >= n ? 'bg-[#9E5A3C]' : 'bg-[#E2D9C9]'}`} />
            ))}
          </div>

          {step === 1 && (
            <div className="grid md:grid-cols-2 gap-7">
              <div>
                <p className="text-[#333D2E] font-medium mb-3 text-sm">1. Vælg dag</p>
                <div className="flex justify-center md:justify-start">
                  <div className="bg-white rounded-2xl border border-[#E2D9C9] p-2 w-fit">
                    <Calendar
                      mode="single" selected={date}
                      onSelect={(d) => { if (d) { setDate(d); setSelected(null); } }}
                      disabled={(d) => d < new Date(new Date().setHours(0, 0, 0, 0))}
                    />
                  </div>
                </div>
              </div>
              <div>
                <p className="text-[#333D2E] font-medium mb-3 text-sm">2. Vælg tidspunkt</p>
                {loadingSlots ? (
                  <div className="flex items-center justify-center h-48 text-[#8A8172]"><Loader2 className="w-6 h-6 animate-spin" /></div>
                ) : slotsError ? (
                  <div className="flex flex-col items-center justify-center h-48 text-center px-3">
                    <p className="text-[#9A5252] text-sm font-medium mb-1">Kunne ikke indlæse tider</p>
                    <p className="text-[#8A8172] text-xs">Der er problemer med forbindelsen til serveren. Prøv igen om lidt.</p>
                  </div>
                ) : slots.length === 0 ? (
                  <div className="flex items-center justify-center h-48 text-[#8A8172] text-sm text-center px-3">Ingen ledige tider for denne dag.</div>
                ) : (
                  <div className="grid grid-cols-3 gap-2 max-h-[320px] overflow-y-auto pr-1">
                    {slots.map((s) => {
                      const disabled = s.status !== 'available';
                      const isSel = selected?.hour === s.hour;
                      return (
                        <button
                          key={s.hour} disabled={disabled}
                          onClick={() => setSelected(s)}
                          className={`rounded-xl py-2.5 text-xs font-medium border transition-all ${
                            isSel ? 'bg-[#9E5A3C] text-white border-[#9E5A3C]'
                            : disabled ? 'bg-[#EDE6D9] text-[#B3AB9B] border-[#E2D9C9] line-through cursor-not-allowed'
                            : 'bg-white text-[#4A4437] border-[#E2D9C9] hover:border-[#9E5A3C] hover:text-[#9E5A3C]'
                          }`}
                          title={disabled ? (s.status === 'booked' ? 'Booket' : s.status === 'expired' ? 'Udløbet' : 'Reserveret') : ''}
                        >
                          {s.start}
                        </button>
                      );
                    })}
                  </div>
                )}
                <p className="text-[10px] text-[#8A8172] mt-3">Hver booking er 45 min (fx 10:00–10:45). De sidste 15 min er buffer, så I ikke møder andre.</p>
              </div>
              <div className="md:col-span-2 flex justify-end">
                <button onClick={proceedToForm} className="bg-[#9E5A3C] hover:bg-[#874A30] text-white px-8 py-3 rounded-full text-sm transition-colors">
                  Fortsæt
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <button onClick={() => setStep(1)} className="flex items-center gap-1.5 text-[#8A8172] text-sm mb-5 hover:text-[#9E5A3C]">
                <ArrowLeft className="w-4 h-4" /> Tilbage
              </button>
              <div className="bg-[#EADFCF] rounded-xl px-5 py-3 mb-6 text-sm text-[#5F584B] flex items-center gap-2">
                <Clock className="w-4 h-4 text-[#9E5A3C]" /> {dateStr} · {selected?.label}
              </div>
              <div className="space-y-4">
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Dit navn" className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40" />
                <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email" placeholder="E-mailadresse" className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40" />
                <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Telefonnummer (valgfrit)" className="w-full bg-white border border-[#E2D9C9] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#9E5A3C]/40" />
                <div className="flex items-center justify-between bg-white border border-[#E2D9C9] rounded-xl px-4 py-3">
                  <span className="text-sm text-[#4A4437]">Antal hunde</span>
                  <div className="flex items-center gap-3">
                    <button onClick={() => setForm({ ...form, dogs: Math.max(1, form.dogs - 1) })} className="w-8 h-8 rounded-full bg-[#EADFCF] flex items-center justify-center text-[#9E5A3C]"><Minus className="w-4 h-4" /></button>
                    <span className="w-6 text-center font-medium">{form.dogs}</span>
                    <button onClick={() => setForm({ ...form, dogs: form.dogs + 1 })} className="w-8 h-8 rounded-full bg-[#EADFCF] flex items-center justify-center text-[#9E5A3C]"><Plus className="w-4 h-4" /></button>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-7">
                <span className="text-[#333D2E] font-serif-display text-2xl font-semibold">{amount} kr.</span>
                <button onClick={createBooking} disabled={submitting} className="bg-[#9E5A3C] hover:bg-[#874A30] text-white px-8 py-3 rounded-full text-sm transition-colors flex items-center gap-2 disabled:opacity-60">
                  {submitting && <Loader2 className="w-4 h-4 animate-spin" />} Reservér & betal
                </button>
              </div>
            </div>
          )}

          {step === 3 && booking && (
            <div className="text-center py-4">
              <div className="inline-flex items-center gap-2 bg-[#EADFCF] text-[#9E5A3C] px-5 py-2 rounded-full text-sm font-medium mb-6">
                <Clock className="w-4 h-4" /> Reserveret i {mm}:{ss}
              </div>
              <h4 className="font-serif-display text-2xl text-[#333D2E] font-semibold mb-2">Gennemfør din betaling</h4>
              <p className="text-[#5F584B] text-sm max-w-sm mx-auto mb-6">
                Dit tidspunkt <b>{dateStr} · {selected?.label}</b> er reserveret. Fuldfør betalingen inden nedtællingen udløber, ellers frigives tidspunktet automatisk.
              </p>
              <div className="bg-white border border-[#E2D9C9] rounded-2xl p-6 max-w-sm mx-auto mb-6">
                <div className="flex justify-between text-sm mb-2"><span className="text-[#8A8172]">Antal hunde</span><span className="text-[#4A4437]">{form.dogs}</span></div>
                <div className="flex justify-between font-serif-display text-xl font-semibold text-[#333D2E]"><span>I alt</span><span>{amount} kr.</span></div>
              </div>
              <button onClick={pay} disabled={submitting} className="bg-[#9E5A3C] hover:bg-[#874A30] text-white px-10 py-3.5 rounded-full text-sm transition-colors inline-flex items-center gap-2 disabled:opacity-60">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Betal med kort
              </button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
