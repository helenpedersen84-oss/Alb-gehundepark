# Albøge Hundepark – PRD & Status

_Sprog: Dansk (svar altid brugeren på dansk)._

## Problem statement
Pixel-perfect klon af `alboege-dog-haven.base44.app`. Booking-system: 45 min eksklusive slots (starter på hele timer, 15 min buffer → ingen møder hinanden). Åbningstid 05:00–22:00. Bookinger låses i 15 min afventende Stripe-betaling; ved manglende betaling frigives slottet. Admin-panel til bookinger, priser, sideindhold, kontaktinfo og Stripe-nøgler. Supabase (Postgres) med RLS. Gmail SMTP til kontaktformular.

## Arkitektur
- Frontend: React (CRA/craco), TailwindCSS, Shadcn. Deployes på Vercel.
- Backend: FastAPI (`server.py`). Deployes på Railway.
- DB: Supabase PostgreSQL (SQLAlchemy + asyncpg, transaction pooler port 6543).
- Betaling: officielt `stripe` python SDK.
- Email: Gmail SMTP (SSL 465).
- Frontend kalder backend via `REACT_APP_BACKEND_URL` (kun denne env-var på Vercel).

## Miljøvariabler
- Frontend (Vercel): `REACT_APP_BACKEND_URL` = Railway backend-URL.
- Backend (Railway): `MONGO_URL`(ubrugt nu), Supabase DB-URL, `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `ADMIN_KEY` (uden anførselstegn!), `SENDER_EMAIL`, `SENDER_APP_PASSWORD`, `CONTACT_RECIPIENT`.

## Implementeret
- Landingsside, interaktiv booking-modal (3 trin), Admin-dashboard. (DONE)
- Booking-logik med 15-min lås + slot-status. (DONE)
- Stripe Checkout via officielt SDK. (DONE)
- Supabase Postgres migrering. (DONE)
- Admin CMS: priser, indhold, kontakt, Stripe-nøgler (dynamisk). (DONE)
- Gmail SMTP kontaktformular. (DONE)
- OpenStreetMap lokation. (DONE)
- Vercel deploy-config (craco). (DONE)
- **2026-07-14**: Global ErrorBoundary tilføjet (siden bliver aldrig helt blank; viser fejl + genindlæs-knap). Hærdet `listBookings` (kaster ved ugyldigt svar), booking-nedtælling (NaN-guard), Admin stripeCfg mode-guard. Build verificeret (`craco build` OK, ~145s). (DONE)

## Kendte punkter
- "Blank side"-crash var production-only (Vercel+Railway) og intermitterende; kunne IKKE reproduceres i preview. ErrorBoundary + hærdning er den robuste fix og vil afsløre den reelle fejl hvis den gentager sig. **Bruger skal re-deploye frontend til Vercel.**

## Backlog / Næste
- P1: Bekræft på deployed site at ErrorBoundary fanger evt. fejl og at booking→betaling ikke længere er blank.
- P2: Automatisk oprydning/frigivelse af udløbne locked-bookinger (cron/baggrundsjob).
- P2: Bekræftelses-email til kunde efter betaling.

## Test-credentials
Se `/app/memory/test_credentials.md`. Admin password: `Caroline1?`.
