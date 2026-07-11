from fastapi import FastAPI, APIRouter, HTTPException, Request, Header, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone, timedelta

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout,
    CheckoutSessionResponse,
    CheckoutStatusResponse,
    CheckoutSessionRequest,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'admin')

# Booking configuration (server-authoritative)
OPEN_HOUR = 5          # first slot starts at 05:00
CLOSE_HOUR = 22        # last slot starts at 21:00 (ends 21:45, buffer until 22:00)
SESSION_MINUTES = 45
LOCK_MINUTES = 15
CURRENCY = "dkk"

# Default pricing (can be edited live via admin panel -> stored in db.settings)
DEFAULT_SETTINGS = {
    "id": "pricing",
    "single_visit_price": 60.0,   # DKK pr. time / 1 hund
    "extra_dog_price": 30.0,      # DKK pr. ekstra hund
    "ten_trip_price": 560.0,      # DKK for 10-turskort
    "currency": CURRENCY,
}


async def get_settings() -> dict:
    doc = await db.settings.find_one({"id": "pricing"})
    merged = dict(DEFAULT_SETTINGS)
    if doc:
        for k in ("single_visit_price", "extra_dog_price", "ten_trip_price", "currency"):
            if doc.get(k) is not None:
                merged[k] = doc[k]
    return merged


# Default editable site content (can be edited live via admin panel -> stored in db.site_content)
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


async def get_content() -> dict:
    doc = await db.site_content.find_one({"id": "main"})
    merged = {sec: dict(fields) for sec, fields in DEFAULT_CONTENT.items()}
    if doc:
        for sec in CONTENT_SECTIONS:
            saved = doc.get(sec)
            if isinstance(saved, dict):
                for k, v in saved.items():
                    if k in merged[sec] and v is not None:
                        merged[sec][k] = v
    return merged


app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ---------------- Models ----------------
class BookingCreate(BaseModel):
    date: str            # YYYY-MM-DD
    hour: int            # slot start hour
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


# ---------------- Helpers ----------------
def now_utc():
    return datetime.now(timezone.utc)


def compute_amount(dogs: int, settings: dict) -> float:
    dogs = max(1, int(dogs))
    base = float(settings.get("single_visit_price", 60.0))
    extra = float(settings.get("extra_dog_price", 30.0))
    return round(base + (dogs - 1) * extra, 2)


def slot_meta(hour: int):
    start = f"{hour:02d}:00"
    end = f"{hour:02d}:45"
    return start, end, f"{start} \u2013 {end}"


def parse_dt(value):
    """Return a tz-aware datetime from stored value."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


async def active_booking_for_slot(date: str, hour: int):
    """Return the blocking booking for a slot (paid, or an unexpired lock), else None."""
    now = now_utc()
    cursor = db.bookings.find({"date": date, "hour": hour})
    async for b in cursor:
        if b.get("status") == "paid":
            return b
        if b.get("status") == "locked":
            exp = parse_dt(b.get("expires_at"))
            if exp and exp > now:
                return b
    return None


def booking_public(b: dict) -> dict:
    return {
        "booking_id": b.get("id"),
        "date": b.get("date"),
        "hour": b.get("hour"),
        "name": b.get("name"),
        "email": b.get("email"),
        "phone": b.get("phone", ""),
        "dogs": b.get("dogs", 1),
        "amount": b.get("amount"),
        "status": b.get("status"),
        "expires_at": parse_dt(b.get("expires_at")).isoformat() if b.get("expires_at") else None,
        "created_at": parse_dt(b.get("created_at")).isoformat() if b.get("created_at") else None,
    }


# ---------------- Routes ----------------
@api_router.get("/")
async def root():
    return {"message": "Alb\u00f8ge Hundepark API"}


@api_router.get("/slots")
async def get_slots(date: str = Query(...)):
    now = now_utc()
    blocking = {}
    async for b in db.bookings.find({"date": date}):
        h = b.get("hour")
        if b.get("status") == "paid":
            blocking[h] = "booked"
        elif b.get("status") == "locked":
            exp = parse_dt(b.get("expires_at"))
            if exp and exp > now and blocking.get(h) != "booked":
                blocking[h] = "locked"

    slots = []
    for hour in range(OPEN_HOUR, CLOSE_HOUR):
        start, end, label = slot_meta(hour)
        status = blocking.get(hour, "available")
        slots.append({"hour": hour, "start": start, "end": end, "label": label, "status": status})
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

    settings = await get_settings()
    amount = compute_amount(payload.dogs, settings)
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
    await db.bookings.insert_one(booking)
    return {
        "booking_id": booking["id"],
        "expires_at": expires_at.isoformat(),
        "amount": amount,
    }


@api_router.post("/checkout/session")
async def create_checkout_session(req: CheckoutRequest, request: Request):
    booking = await db.bookings.find_one({"id": req.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking ikke fundet.")
    if booking.get("status") == "paid":
        raise HTTPException(status_code=409, detail="Booking er allerede betalt.")

    exp = parse_dt(booking.get("expires_at"))
    if not exp or exp <= now_utc():
        raise HTTPException(status_code=410, detail="Reservationen er udl\u00f8bet.")

    amount = float(booking.get("amount") or compute_amount(booking.get("dogs", 1), await get_settings()))

    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    origin = req.origin_url.rstrip('/')
    success_url = f"{origin}/booking/status?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/"

    metadata = {
        "booking_id": booking["id"],
        "date": booking["date"],
        "hour": str(booking["hour"]),
        "source": "booking",
    }
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency=CURRENCY,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)

    txn = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "booking_id": booking["id"],
        "amount": amount,
        "currency": CURRENCY,
        "payment_status": "initiated",
        "status": "initiated",
        "metadata": metadata,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    await db.payment_transactions.insert_one(txn)

    await db.bookings.update_one({"id": booking["id"]}, {"$set": {"session_id": session.session_id}})

    return {"url": session.url, "session_id": session.session_id}


async def _mark_paid(session_id: str):
    """Update transaction + booking to paid exactly once."""
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        return
    if txn.get("payment_status") == "paid":
        return
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": "paid", "status": "complete", "updated_at": now_utc()}},
    )
    await db.bookings.update_one(
        {"id": txn["booking_id"]},
        {"$set": {"status": "paid", "expires_at": None}},
    )


@api_router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str):
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Session ikke fundet.")

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)

    if status.payment_status == "paid":
        await _mark_paid(session_id)
    elif status.status == "expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": "expired", "updated_at": now_utc()}},
        )

    booking = await db.bookings.find_one({"id": txn["booking_id"]})
    return {
        "payment_status": status.payment_status,
        "status": status.status,
        "booking": booking_public(booking) if booking else None,
    }


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook")

    if webhook_response.payment_status == "paid" and webhook_response.session_id:
        await _mark_paid(webhook_response.session_id)
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
    updates["updated_at"] = now_utc()
    await db.settings.update_one({"id": "pricing"}, {"$set": {"id": "pricing", **updates}}, upsert=True)
    return await get_settings()


@api_router.get("/content")
async def public_content():
    return await get_content()


@api_router.put("/admin/content")
async def update_content(payload: dict, x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    update_doc = {"id": "main"}
    for sec in CONTENT_SECTIONS:
        incoming = payload.get(sec)
        if isinstance(incoming, dict):
            clean = {}
            for k, v in incoming.items():
                if k in DEFAULT_CONTENT[sec] and v is not None:
                    clean[k] = str(v)
            if clean:
                update_doc[sec] = clean
    if len(update_doc) == 1:
        raise HTTPException(status_code=400, detail="Ingen \u00e6ndringer.")
    update_doc["updated_at"] = now_utc()
    await db.site_content.update_one({"id": "main"}, {"$set": update_doc}, upsert=True)
    return await get_content()


@api_router.get("/admin/bookings")
async def admin_bookings(x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    now = now_utc()
    results = []
    async for b in db.bookings.find().sort("created_at", -1):
        pub = booking_public(b)
        if b.get("status") == "paid":
            pub["display_status"] = "paid"
        else:
            exp = parse_dt(b.get("expires_at"))
            pub["display_status"] = "locked" if (exp and exp > now) else "expired"
        results.append(pub)
    return {"bookings": results}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
