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
CLOSE_HOUR = 22        # last slot starts at 21:00 (ends 21:45)
SESSION_MINUTES = 45
LOCK_MINUTES = 15
BASE_PRICE = 60.0      # DKK for 1 dog
EXTRA_DOG_PRICE = 30.0 # DKK per extra dog
CURRENCY = "dkk"

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


# ---------------- Helpers ----------------
def now_utc():
    return datetime.now(timezone.utc)


def compute_amount(dogs: int) -> float:
    dogs = max(1, int(dogs))
    return round(BASE_PRICE + (dogs - 1) * EXTRA_DOG_PRICE, 2)


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

    amount = compute_amount(payload.dogs)
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

    amount = float(booking.get("amount") or compute_amount(booking.get("dogs", 1)))

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
