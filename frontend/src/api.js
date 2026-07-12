import axios from 'axios';
import { buildSlots, BOOKING } from './mock';

const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || '').replace(/\/+$/, '');
export const API = `${BACKEND_URL}/api`;

// ---- MOCK MODE (frontend-only phase) ----
// Uses localStorage to simulate slot locking + payment. Will be replaced by
// real backend calls (see contracts.md) in the backend phase.
const USE_MOCK = false; // set to true only for pure frontend demo

function lsKey() { return 'ahp_bookings_v1'; }
function readLS() { try { return JSON.parse(localStorage.getItem(lsKey())) || {}; } catch { return {}; } }
function writeLS(d) { localStorage.setItem(lsKey(), JSON.stringify(d)); }

const mockApi = {
  async getSlots(date) {
    const data = readLS();
    const now = Date.now();
    return buildSlots().map((s) => {
      const key = `${date}T${s.hour}`;
      const rec = data[key];
      let status = 'available';
      if (rec) {
        if (rec.paid) status = 'booked';
        else if (rec.expires_at > now) status = 'locked';
      }
      return { ...s, status };
    });
  },
  async createBooking(payload) {
    const data = readLS();
    const key = `${payload.date}T${payload.hour}`;
    const now = Date.now();
    const rec = data[key];
    if (rec && (rec.paid || rec.expires_at > now)) {
      throw { response: { data: { detail: 'Tidspunktet er ikke længere ledigt.' } } };
    }
    const id = 'mock_' + Math.random().toString(36).slice(2);
    data[key] = { booking_id: id, ...payload, paid: false, expires_at: now + 15 * 60 * 1000 };
    writeLS(data);
    return { booking_id: id, expires_at: new Date(data[key].expires_at).toISOString(), amount: payload.dogs > 1 ? 60 + (payload.dogs - 1) * 30 : 60 };
  },
  async createCheckout({ booking_id }) {
    // simulate immediate success page
    return { url: `${window.location.origin}/booking/status?session_id=${booking_id}` };
  },
  async getStatus(session_id) {
    const data = readLS();
    const entry = Object.values(data).find((r) => r.booking_id === session_id);
    if (entry) { entry.paid = true; writeLS(data); }
    return { payment_status: 'paid', status: 'complete', booking: entry };
  },
  async listBookings() {
    const data = readLS();
    return Object.entries(data).map(([k, v]) => ({ ...v, slot: k }));
  },
};

// ---- REAL API ----
const realApi = {
  async getSlots(date) {
    const { data } = await axios.get(`${API}/slots`, { params: { date } });
    if (!data || !Array.isArray(data.slots)) {
      throw new Error('Ugyldigt svar fra serveren for tider');
    }
    return data.slots;
  },
  async createBooking(payload) {
    const { data } = await axios.post(`${API}/bookings`, payload);
    return data;
  },
  async createCheckout({ booking_id, origin }) {
    const { data } = await axios.post(`${API}/checkout/session`, { booking_id, origin_url: origin });
    return data;
  },
  async getStatus(session_id) {
    const { data } = await axios.get(`${API}/checkout/status/${session_id}`);
    return data;
  },
  async listBookings(adminKey) {
    const { data } = await axios.get(`${API}/admin/bookings`, { headers: { 'X-Admin-Key': adminKey } });
    return data.bookings;
  },
  async getSettings() {
    const { data } = await axios.get(`${API}/settings`);
    if (!data || typeof data.single_visit_price !== 'number') {
      throw new Error('Ugyldigt svar fra serveren for priser');
    }
    return data;
  },
  async updateSettings(adminKey, payload) {
    const { data } = await axios.put(`${API}/admin/settings`, payload, { headers: { 'X-Admin-Key': adminKey } });
    return data;
  },
  async getContent() {
    const { data } = await axios.get(`${API}/content`);
    if (!data || !data.hero || !data.contact) {
      throw new Error('Ugyldigt svar fra serveren for indhold');
    }
    return data;
  },
  async updateContent(adminKey, payload) {
    const { data } = await axios.put(`${API}/admin/content`, payload, { headers: { 'X-Admin-Key': adminKey } });
    return data;
  },
  async sendContact(payload) {
    const { data } = await axios.post(`${API}/contact`, payload);
    return data;
  },
};

const api = USE_MOCK ? mockApi : realApi;
export default api;
export { BOOKING };
