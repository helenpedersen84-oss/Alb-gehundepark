# Albøge Hundepark – API Contracts

## Booking rules
- Slots: one exclusive slot per hour, start 05:00 → 21:00 (OPEN_HOUR=5, CLOSE_HOUR=22). Each 45 min (HH:00–HH:45), 15 min buffer.
- Price: 60 DKK (1 dog) + 30 DKK per extra dog. Server-authoritative.
- Lock: creating a booking locks the slot for 15 min (status=locked, expires_at). If unpaid past expiry → treated as available again. If paid → status=paid, permanently blocks the slot.

## Endpoints (prefix /api)
- GET /slots?date=YYYY-MM-DD → { date, slots:[{hour,start,end,label,status}] } status: available|locked|booked
- POST /bookings { date, hour, name, email, phone?, dogs } → { booking_id, expires_at, amount } (409 if slot taken)
- POST /checkout/session { booking_id, origin_url } → { url, session_id } (amount from server)
- GET /checkout/status/{session_id} → { payment_status, status, booking } (polls Stripe, marks paid once)
- POST /webhook/stripe → Stripe webhook, marks paid
- GET /admin/bookings (header X-Admin-Key) → { bookings:[...] }

## Collections
- bookings: id,date,hour,name,email,phone,dogs,amount,currency,status(locked|paid),session_id,expires_at,created_at
- payment_transactions: id,session_id,booking_id,amount,currency,payment_status,status,metadata,created_at,updated_at

## Frontend integration
- src/api.js: USE_MOCK=false → realApi. Booking modal uses api.getSlots/createBooking/createCheckout; BookingStatus polls api.getStatus; Admin uses api.listBookings(adminKey).
- Env: backend .env has STRIPE_API_KEY, ADMIN_KEY. Frontend uses REACT_APP_BACKEND_URL.

## Previously mocked (now real)
- Slot availability, booking creation, 15-min lock, payment, admin list — all moved to backend.
