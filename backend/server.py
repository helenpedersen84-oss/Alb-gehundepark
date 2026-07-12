from fastapi import FastAPI, APIRouter, HTTPException, Request, Header, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import ssl
import smtplib
import asyncio
from email.message import EmailMessage
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, insert, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database import engine
from models import (
    bookings as bookings_t,
    payment_transactions as txn_t,
    settings as settings_t,
    site_content as content_t,
)

import stripe

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
stripe.api_key = STRIPE_API_KEY
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'admin')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_APP_PASSWORD = os.environ.get('SENDER_APP_PASSWORD')
CONTACT_RECIPIENT = os.environ.get('CONTACT_RECIPIENT', SENDER_EMAIL)

# Booking configuration (server-authoritative)
OPEN_HOUR = 5          # first slot starts at 05:00
CLOSE_HOUR = 22        # last slot starts at 21:00 (ends 21:45, buffer until 22:00)
SESSION_MINUTES = 45
LOCK_MINUTES = 15
CURRENCY = "dkk"

DEFAULT_SETTINGS = {
    "single_visit_price": 60.0,
    "extra_dog_price": 30.0,
    "ten_trip_price": 560.0,
    "currency": CURRENCY,
}

DEFAULT_CONTENT = {
    "hero": {
        "kicker": "ALB\u00d8GE HUNDEPARK",
        "title1": "Frihed",
        "title2": "i det Fri",
        "subtitle": "Et natursk\u00f8nt fristed hvor hunde l\u00f8ber frit \u2014 omgivet af \u00e5bne marker og frisk luft.",
    },
    "about": {
        "kicker": "OM PARKEN",
        "title1": "Et sted skabt til",
        "title2": "naturlig gl\u00e6de",
        "p1": "Alb\u00f8ge Hundepark er et indhegnet naturomr\u00e5de i det smukke \u00f8stjyske landskab, hvor din hund kan l\u00f8be frit og udforske naturen i trygge omgivelser.",
        "p2": "Parken tilbyder \u00e5bne marker, naturlige stier og masser af plads til leg og motion \u2014 alt sammen omgivet af den smukke Djurslandske natur.",
    },
    "contact": {
        "subtitle": "Har du sp\u00f8rgsm\u00e5l til booking, priser eller pladsen? Vi vender tilbage hurtigst muligt.",
        "address": "Alb\u00f8ge, 8500 Grenaa, Djursland",
        "phone": "+45 93 84 18 68",
        "email": "hej@albogehundepark.dk",
    },
}
CONTENT_SECTIONS = list(DEFAULT_CONTENT.keys())

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ---------------- Models ----------------
class BookingCreate(BaseModel):
    date: str
    hour: int
    name: str
    email: str
    phone: Optional[str] = ""
    dogs: int = 1


class CheckoutRequest(BaseModel):
    booking_id: str
    origin_url: str


class SettingsUpdate(BaseModel):
    single_visit_price: Optional[float] = None
    extra_dog_price: Optional[float] = None
    ten_trip_price: Optional[float] = None


class ContactMessage(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    message: str


# ---------------- Helpers ----------------
def now_utc():
    return datetime.now(timezone.utc)


def compute_amount(dogs: int, s: dict) -> float:
    dogs = max(1, int(dogs))
    base = float(s.get("single_visit_price", 60.0))
    extra = float(s.get("extra_dog_price", 30.0))
    return round(base + (dogs - 1) * extra, 2)


def slot_meta(hour: int):
    start = f"{hour:02d}:00"
    end = f"{hour:02d}:45"
    return start, end, f"{start} \u2013 {end}"


def as_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


async def get_settings() -> dict:
    async with engine.connect() as conn:
        res = await conn.execute(select(settings_t).where(settings_t.c.id == "pricing"))
        row = res.mappings().first()
    merged = dict(DEFAULT_SETTINGS)
    if row:
        for k in ("single_visit_price", "extra_dog_price", "ten_trip_price", "currency"):
            if row.get(k) is not None:
                merged[k] = float(row[k]) if k != "currency" else row[k]
    return merged


async def get_content() -> dict:
    async with engine.connect() as conn:
        res = await conn.execute(select(content_t).where(content_t.c.id == "main"))
        row = res.mappings().first()
    merged = {sec: dict(fields) for sec, fields in DEFAULT_CONTENT.items()}
    if row:
        for sec in CONTENT_SECTIONS:
            saved = row.get(sec)
            if isinstance(saved, dict):
                for k, v in saved.items():
                    if k in merged[sec] and v is not None:
                        merged[sec][k] = v
    return merged


async def active_booking_for_slot(date: str, hour: int):
    now = now_utc()
    async with engine.connect() as conn:
        res = await conn.execute(
            select(bookings_t).where(bookings_t.c.date == date, bookings_t.c.hour == hour)
        )
        rows = res.mappings().all()
    for b in rows:
        if b["status"] == "paid":
            return b
        if b["status"] == "locked":
            exp = as_dt(b["expires_at"])
            if exp and exp > now:
                return b
    return None


def booking_public(b) -> dict:
    if b is None:
        return None
    return {
        "booking_id": b["id"],
        "date": b["date"],
        "hour": b["hour"],
        "name": b["name"],
        "email": b["email"],
        "phone": b.get("phone", "") if isinstance(b, dict) else b["phone"],
        "dogs": b["dogs"],
        "amount": float(b["amount"]) if b["amount"] is not None else None,
        "status": b["status"],
        "expires_at": as_dt(b["expires_at"]).isoformat() if b["expires_at"] else None,
        "created_at": as_dt(b["created_at"]).isoformat() if b["created_at"] else None,
    }


# ---------------- Routes ----------------
@api_router.get("/")
async def root():
    return {"message": "Alb\u00f8ge Hundepark API"}


@api_router.get("/slots")
async def get_slots(date: str = Query(...)):
    now = now_utc()
    blocking = {}
    async with engine.connect() as conn:
        res = await conn.execute(select(bookings_t).where(bookings_t.c.date == date))
        rows = res.mappings().all()
    for b in rows:
        h = b["hour"]
        if b["status"] == "paid":
            blocking[h] = "booked"
        elif b["status"] == "locked":
            exp = as_dt(b["expires_at"])
            if exp and exp > now and blocking.get(h) != "booked":
                blocking[h] = "locked"

    slots = []
    for hour in range(OPEN_HOUR, CLOSE_HOUR):
        start, end, label = slot_meta(hour)
        slots.append({"hour": hour, "start": start, "end": end, "label": label,
                      "status": blocking.get(hour, "available")})
    return {"date": date, "slots": slots}


@api_router.post("/bookings")
async def create_booking(payload: BookingCreate):
    if payload.hour < OPEN_HOUR or payload.hour >= CLOSE_HOUR:
        raise HTTPException(status_code=400, detail="Ugyldigt tidspunkt.")
    if not payload.name or not payload.email:
        raise HTTPException(status_code=400, detail="Navn og e-mail er p\u00e5kr\u00e6vet.")

    try:
        booking_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig dato.")
    if booking_date < now_utc().date():
        raise HTTPException(status_code=400, detail="Dato er i fortiden.")

    existing = await active_booking_for_slot(payload.date, payload.hour)
    if existing:
        raise HTTPException(status_code=409, detail="Tidspunktet er ikke l\u00e6ngere ledigt.")

    s = await get_settings()
    amount = compute_amount(payload.dogs, s)
    expires_at = now_utc() + timedelta(minutes=LOCK_MINUTES)
    booking = {
        "id": str(uuid.uuid4()),
        "date": payload.date,
        "hour": payload.hour,
        "name": payload.name.strip(),
        "email": payload.email.strip(),
        "phone": (payload.phone or "").strip(),
        "dogs": max(1, int(payload.dogs)),
        "amount": amount,
        "currency": CURRENCY,
        "status": "locked",
        "session_id": None,
        "expires_at": expires_at,
        "created_at": now_utc(),
    }
    async with engine.begin() as conn:
        await conn.execute(insert(bookings_t).values(**booking))
    return {"booking_id": booking["id"], "expires_at": expires_at.isoformat(), "amount": amount}


@api_router.post("/checkout/session")
async def create_checkout_session(req: CheckoutRequest, request: Request):
    async with engine.connect() as conn:
        res = await conn.execute(select(bookings_t).where(bookings_t.c.id == req.booking_id))
        booking = res.mappings().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking ikke fundet.")
    if booking["status"] == "paid":
        raise HTTPException(status_code=409, detail="Booking er allerede betalt.")
    exp = as_dt(booking["expires_at"])
    if not exp or exp <= now_utc():
        raise HTTPException(status_code=410, detail="Reservationen er udl\u00f8bet.")

    amount = float(booking["amount"] or compute_amount(booking["dogs"], await get_settings()))

    origin = req.origin_url.rstrip('/')
    success_url = f"{origin}/booking/status?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/"

    meta = {"booking_id": booking["id"], "date": booking["date"], "hour": str(booking["hour"]), "source": "booking"}

    def _create_session():
        return stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": CURRENCY,
                    "product_data": {"name": f"Booking {booking['date']} kl. {int(booking['hour']):02d}:00 - Alb\u00f8ge Hundepark"},
                    "unit_amount": int(round(amount * 100)),  # amount in \u00f8re
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=meta,
        )

    try:
        session = await asyncio.to_thread(_create_session)
    except Exception as e:
        logger.error(f"Stripe session error: {e}")
        raise HTTPException(status_code=502, detail=f"Stripe-fejl: {str(e)[:300]}")

    async with engine.begin() as conn:
        await conn.execute(insert(txn_t).values(
            id=str(uuid.uuid4()), session_id=session.id, booking_id=booking["id"],
            amount=amount, currency=CURRENCY, payment_status="initiated", status="initiated",
            meta=meta, created_at=now_utc(), updated_at=now_utc(),
        ))
        await conn.execute(update(bookings_t).where(bookings_t.c.id == booking["id"]).values(session_id=session.id))

    return {"url": session.url, "session_id": session.id}


async def _mark_paid(session_id: str):
    async with engine.begin() as conn:
        res = await conn.execute(select(txn_t).where(txn_t.c.session_id == session_id))
        txn = res.mappings().first()
        if not txn or txn["payment_status"] == "paid":
            return
        await conn.execute(update(txn_t).where(txn_t.c.session_id == session_id).values(
            payment_status="paid", status="complete", updated_at=now_utc()))
        await conn.execute(update(bookings_t).where(bookings_t.c.id == txn["booking_id"]).values(
            status="paid", expires_at=None))


@api_router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str):
    async with engine.connect() as conn:
        res = await conn.execute(select(txn_t).where(txn_t.c.session_id == session_id))
        txn = res.mappings().first()
    if not txn:
        raise HTTPException(status_code=404, detail="Session ikke fundet.")

    try:
        session = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
    except Exception as e:
        logger.error(f"Stripe status error: {e}")
        raise HTTPException(status_code=502, detail="Kunne ikke hente betalingsstatus.")

    payment_status = session.get("payment_status")  # 'paid' | 'unpaid' | 'no_payment_required'
    sess_status = session.get("status")             # 'open' | 'complete' | 'expired'

    if payment_status == "paid":
        await _mark_paid(session_id)
    elif sess_status == "expired":
        async with engine.begin() as conn:
            await conn.execute(update(txn_t).where(txn_t.c.session_id == session_id).values(
                status="expired", updated_at=now_utc()))

    async with engine.connect() as conn:
        res = await conn.execute(select(bookings_t).where(bookings_t.c.id == txn["booking_id"]))
        booking = res.mappings().first()
    return {
        "payment_status": payment_status,
        "status": sess_status,
        "booking": booking_public(booking) if booking else None,
    }


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(body, signature, STRIPE_WEBHOOK_SECRET)
        else:
            import json
            event = json.loads(body)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook")

    event_type = event.get("type")
    if event_type in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        session = event["data"]["object"]
        if session.get("payment_status") == "paid" and session.get("id"):
            await _mark_paid(session["id"])
    return {"received": True}


@api_router.get("/settings")
async def public_settings():
    s = await get_settings()
    return {
        "single_visit_price": s["single_visit_price"],
        "extra_dog_price": s["extra_dog_price"],
        "ten_trip_price": s["ten_trip_price"],
        "currency": s["currency"],
        "open_hour": OPEN_HOUR,
        "close_hour": CLOSE_HOUR,
    }


@api_router.put("/admin/settings")
async def update_settings(payload: SettingsUpdate, x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    updates = {}
    for field in ("single_visit_price", "extra_dog_price", "ten_trip_price"):
        val = getattr(payload, field)
        if val is not None:
            if val < 0:
                raise HTTPException(status_code=400, detail="Pris kan ikke v\u00e6re negativ.")
            updates[field] = round(float(val), 2)
    if not updates:
        raise HTTPException(status_code=400, detail="Ingen \u00e6ndringer.")

    current = await get_settings()
    current.update(updates)
    values = {
        "id": "pricing",
        "single_visit_price": current["single_visit_price"],
        "extra_dog_price": current["extra_dog_price"],
        "ten_trip_price": current["ten_trip_price"],
        "currency": current["currency"],
        "updated_at": now_utc(),
    }
    stmt = pg_insert(settings_t).values(**values)
    stmt = stmt.on_conflict_do_update(index_elements=[settings_t.c.id], set_={
        k: values[k] for k in ("single_visit_price", "extra_dog_price", "ten_trip_price", "currency", "updated_at")
    })
    async with engine.begin() as conn:
        await conn.execute(stmt)
    return await get_settings()


@api_router.get("/content")
async def public_content():
    return await get_content()


@api_router.put("/admin/content")
async def update_content(payload: dict, x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    current = await get_content()
    changed = False
    for sec in CONTENT_SECTIONS:
        incoming = payload.get(sec)
        if isinstance(incoming, dict):
            for k, v in incoming.items():
                if k in DEFAULT_CONTENT[sec] and v is not None:
                    current[sec][k] = str(v)
                    changed = True
    if not changed:
        raise HTTPException(status_code=400, detail="Ingen \u00e6ndringer.")

    values = {
        "id": "main",
        "hero": current["hero"],
        "about": current["about"],
        "contact": current["contact"],
        "updated_at": now_utc(),
    }
    stmt = pg_insert(content_t).values(**values)
    stmt = stmt.on_conflict_do_update(index_elements=[content_t.c.id], set_={
        "hero": values["hero"], "about": values["about"], "contact": values["contact"], "updated_at": values["updated_at"],
    })
    async with engine.begin() as conn:
        await conn.execute(stmt)
    return await get_content()


def _send_contact_email(payload: ContactMessage):
    msg = EmailMessage()
    msg["Subject"] = f"Ny besked fra hjemmesiden \u2013 {payload.name}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = CONTACT_RECIPIENT
    msg["Reply-To"] = payload.email
    body = (
        "Du har modtaget en ny besked via kontaktformularen p\u00e5 Alb\u00f8ge Hundepark:\n\n"
        f"Navn: {payload.name}\n"
        f"E-mail: {payload.email}\n"
        f"Telefon: {payload.phone or '(ikke angivet)'}\n\n"
        f"Besked:\n{payload.message}\n"
    )
    msg.set_content(body)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=20) as server:
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)


@api_router.post("/contact")
async def contact(payload: ContactMessage):
    if not payload.name or not payload.email or not payload.message:
        raise HTTPException(status_code=400, detail="Navn, e-mail og besked er p\u00e5kr\u00e6vet.")
    if not SENDER_EMAIL or not SENDER_APP_PASSWORD:
        raise HTTPException(status_code=500, detail="E-mail er ikke konfigureret.")
    try:
        await asyncio.to_thread(_send_contact_email, payload)
    except Exception as e:
        logger.error(f"Contact email error: {e}")
        raise HTTPException(status_code=502, detail="Kunne ikke sende beskeden. Pr\u00f8v igen senere.")
    return {"sent": True}


@api_router.get("/admin/bookings")
async def admin_bookings(x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    now = now_utc()
    async with engine.connect() as conn:
        res = await conn.execute(select(bookings_t).order_by(bookings_t.c.created_at.desc()))
        rows = res.mappings().all()
    results = []
    for b in rows:
        pub = booking_public(b)
        if b["status"] == "paid":
            pub["display_status"] = "paid"
        else:
            exp = as_dt(b["expires_at"])
            pub["display_status"] = "locked" if (exp and exp > now) else "expired"
        results.append(pub)
    return {"bookings": results}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    await engine.dispose()
