#!/usr/bin/env python3
"""
Backend API Regression Test Suite for Albøge Hundepark
Tests all /api endpoints after Supabase Postgres migration
"""

import requests
import json
from datetime import datetime, timedelta
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# Configuration
BASE_URL = "https://dog-haven-checkout.preview.emergentagent.com/api"
ADMIN_KEY = "Caroline1?"
DATABASE_URL = os.environ.get('DATABASE_URL')

# Setup async database connection for verification
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=2,
    max_overflow=2,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

# Import models for database verification
import sys
sys.path.insert(0, str(Path(__file__).parent / "backend"))
from models import payment_transactions as txn_t, bookings as bookings_t

# Test data - using 2026 dates as requested
def get_future_date(days_ahead=60):
    """Get a future date in 2026 in YYYY-MM-DD format"""
    # Use September 2026 as requested
    base_date = datetime(2026, 9, 1)
    return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

def get_past_date():
    """Get a past date in YYYY-MM-DD format"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

def print_pass(message):
    print(f"{Colors.GREEN}✓ PASS: {message}{Colors.END}")

def print_fail(message):
    print(f"{Colors.RED}✗ FAIL: {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ INFO: {message}{Colors.END}")

def print_section(message):
    print(f"\n{Colors.CYAN}{'─'*80}{Colors.END}")
    print(f"{Colors.CYAN}{message}{Colors.END}")
    print(f"{Colors.CYAN}{'─'*80}{Colors.END}")

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "total": 0
}

def record_result(test_name, passed, message=""):
    test_results["total"] += 1
    if passed:
        test_results["passed"].append(test_name)
        print_pass(f"{test_name} - {message}")
    else:
        test_results["failed"].append(test_name)
        print_fail(f"{test_name} - {message}")

# Database verification helpers
async def check_payment_transaction(session_id):
    """Check if payment transaction exists in Postgres database"""
    async with engine.connect() as conn:
        res = await conn.execute(select(txn_t).where(txn_t.c.session_id == session_id))
        txn = res.mappings().first()
    return txn

async def check_booking(booking_id):
    """Check if booking exists in Postgres database"""
    async with engine.connect() as conn:
        res = await conn.execute(select(bookings_t).where(bookings_t.c.id == booking_id))
        booking = res.mappings().first()
    return booking

# Test functions
def test_1_root_endpoint():
    """Test 1: GET /api/ returns message"""
    print_test("1. GET /api/ - Root endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code == 200 and "message" in response.json():
            record_result("Root endpoint", True, "Returns message successfully")
            return True
        else:
            record_result("Root endpoint", False, f"Unexpected response: {response.json()}")
            return False
    except Exception as e:
        record_result("Root endpoint", False, f"Exception: {str(e)}")
        return False


def test_2_get_settings():
    """Test 2: GET /api/settings returns all required fields"""
    print_test("2. GET /api/settings - Public settings")
    
    try:
        response = requests.get(f"{BASE_URL}/settings")
        print_info(f"Status: {response.status_code}")
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        required_fields = {
            "single_visit_price": 60,
            "extra_dog_price": 30,
            "ten_trip_price": 560,
            "currency": "dkk",
            "open_hour": 5,
            "close_hour": 22
        }
        
        all_present = True
        for field, expected_value in required_fields.items():
            if field not in data:
                print_fail(f"Missing field: {field}")
                all_present = False
            else:
                print_info(f"{field}: {data[field]} (expected: {expected_value})")
        
        if response.status_code == 200 and all_present:
            record_result("GET settings", True, "All required fields present")
            return True, data
        else:
            record_result("GET settings", False, "Missing required fields")
            return False, None
    except Exception as e:
        record_result("GET settings", False, f"Exception: {str(e)}")
        return False, None


def test_3_get_slots():
    """Test 3: GET /api/slots returns 17 slots (hours 5-21)"""
    print_test("3. GET /api/slots - List slots for a date")
    
    future_date = get_future_date(1)
    print_info(f"Testing with date: {future_date}")
    
    try:
        response = requests.get(f"{BASE_URL}/slots", params={"date": future_date})
        print_info(f"Status: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            slots = data.get("slots", [])
            print_info(f"Number of slots: {len(slots)}")
            
            if len(slots) == 17:
                # Verify slot structure
                first_slot = slots[0]
                last_slot = slots[-1]
                print_info(f"First slot: hour={first_slot['hour']}, status={first_slot['status']}")
                print_info(f"Last slot: hour={last_slot['hour']}, status={last_slot['status']}")
                
                if first_slot['hour'] == 5 and last_slot['hour'] == 21:
                    record_result("GET slots", True, "Returns 17 slots (hours 5-21) with correct structure")
                    return True, future_date
                else:
                    record_result("GET slots", False, f"Incorrect hour range: {first_slot['hour']}-{last_slot['hour']}")
                    return False, future_date
            else:
                record_result("GET slots", False, f"Expected 17 slots, got {len(slots)}")
                return False, future_date
        else:
            record_result("GET slots", False, f"Status {response.status_code}")
            return False, future_date
    except Exception as e:
        record_result("GET slots", False, f"Exception: {str(e)}")
        return False, None


def test_4_create_booking():
    """Test 4: POST /api/bookings creates booking with correct amount"""
    print_test("4. POST /api/bookings - Create booking")
    
    future_date = get_future_date(2)
    print_info(f"Testing with date: {future_date}")
    
    booking_data = {
        "date": future_date,
        "hour": 11,
        "name": "Regression Test User",
        "email": "regtest@example.dk",
        "phone": "12345678",
        "dogs": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
        print_info(f"Status: {response.status_code}")
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            # Verify response structure
            required_fields = ["booking_id", "expires_at", "amount"]
            all_present = all(field in data for field in required_fields)
            
            if all_present:
                # Verify amount calculation: 60 + 30*(2-1) = 90
                expected_amount = 90
                actual_amount = data["amount"]
                
                if actual_amount == expected_amount:
                    print_info(f"Amount calculation correct: {actual_amount} DKK for 2 dogs")
                    record_result("POST bookings", True, f"Booking created with correct amount ({actual_amount} DKK)")
                    return True, data["booking_id"], future_date
                else:
                    record_result("POST bookings", False, f"Amount mismatch: expected {expected_amount}, got {actual_amount}")
                    return False, None, future_date
            else:
                record_result("POST bookings", False, "Missing required fields in response")
                return False, None, future_date
        else:
            record_result("POST bookings", False, f"Status {response.status_code}: {data}")
            return False, None, future_date
    except Exception as e:
        record_result("POST bookings", False, f"Exception: {str(e)}")
        return False, None, None


def test_5_slot_lock_verification(booking_date):
    """Test 5: Verify slot is locked and duplicate booking returns 409"""
    print_test("5. Slot Lock Verification")
    
    print_section("5a. Verify slot status changed to 'locked'")
    try:
        response = requests.get(f"{BASE_URL}/slots", params={"date": booking_date})
        data = response.json()
        
        slots = data.get("slots", [])
        hour_11_slot = next((s for s in slots if s["hour"] == 11), None)
        
        if hour_11_slot:
            print_info(f"Hour 11 slot status: {hour_11_slot['status']}")
            if hour_11_slot['status'] == "locked":
                record_result("Slot lock status", True, "Slot correctly marked as 'locked'")
            else:
                record_result("Slot lock status", False, f"Expected 'locked', got '{hour_11_slot['status']}'")
        else:
            record_result("Slot lock status", False, "Hour 11 slot not found")
    except Exception as e:
        record_result("Slot lock status", False, f"Exception: {str(e)}")
    
    print_section("5b. Attempt duplicate booking (should return 409)")
    booking_data = {
        "date": booking_date,
        "hour": 11,
        "name": "Duplicate Test",
        "email": "dup@test.dk",
        "phone": "99999999",
        "dogs": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 409:
            record_result("Duplicate booking prevention", True, "Returns 409 Conflict as expected")
        else:
            record_result("Duplicate booking prevention", False, f"Expected 409, got {response.status_code}")
    except Exception as e:
        record_result("Duplicate booking prevention", False, f"Exception: {str(e)}")


def test_6_validation():
    """Test 6: Validation - invalid hour, past date, missing fields"""
    print_test("6. Validation Tests")
    
    future_date = get_future_date(3)
    
    print_section("6a. Invalid hour (23) - should return 400")
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": future_date,
            "hour": 23,
            "name": "Test User",
            "email": "test@test.dk",
            "phone": "12345678",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 400:
            record_result("Validation: invalid hour", True, "Returns 400 for hour 23")
        else:
            record_result("Validation: invalid hour", False, f"Expected 400, got {response.status_code}")
    except Exception as e:
        record_result("Validation: invalid hour", False, f"Exception: {str(e)}")
    
    print_section("6b. Past date - should return 400")
    past_date = get_past_date()
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": past_date,
            "hour": 10,
            "name": "Test User",
            "email": "test@test.dk",
            "phone": "12345678",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 400:
            record_result("Validation: past date", True, "Returns 400 for past date")
        else:
            record_result("Validation: past date", False, f"Expected 400, got {response.status_code}")
    except Exception as e:
        record_result("Validation: past date", False, f"Exception: {str(e)}")
    
    print_section("6c. Missing name - should return 400/422")
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": future_date,
            "hour": 10,
            "email": "test@test.dk",
            "phone": "12345678",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code in [400, 422]:
            record_result("Validation: missing name", True, f"Returns {response.status_code} for missing name")
        else:
            record_result("Validation: missing name", False, f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        record_result("Validation: missing name", False, f"Exception: {str(e)}")
    
    print_section("6d. Missing email - should return 400/422")
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": future_date,
            "hour": 10,
            "name": "Test User",
            "phone": "12345678",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code in [400, 422]:
            record_result("Validation: missing email", True, f"Returns {response.status_code} for missing email")
        else:
            record_result("Validation: missing email", False, f"Expected 400/422, got {response.status_code}")
    except Exception as e:
        record_result("Validation: missing email", False, f"Exception: {str(e)}")


def test_7_checkout_session(booking_id):
    """Test 7: POST /api/checkout/session creates Stripe session and payment_transactions row"""
    print_test("7. POST /api/checkout/session - Create Stripe checkout")
    
    if not booking_id:
        print_fail("No booking_id provided, skipping test")
        record_result("Checkout session", False, "No booking_id available")
        return False, None
    
    checkout_data = {
        "booking_id": booking_id,
        "origin_url": "https://example.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/checkout/session", json=checkout_data)
        print_info(f"Status: {response.status_code}")
        data = response.json()
        print_info(f"Response keys: {list(data.keys())}")
        
        if response.status_code == 200:
            if "url" in data and "session_id" in data:
                session_id = data["session_id"]
                print_info(f"Stripe session created: {session_id}")
                print_info(f"Checkout URL: {data['url'][:50]}...")
                
                # Verify payment_transactions row in database
                print_section("Verifying payment_transactions record in Postgres")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                txn = loop.run_until_complete(check_payment_transaction(session_id))
                loop.close()
                
                if txn:
                    print_info(f"Transaction found in database:")
                    print_info(f"  - payment_status: {txn['payment_status']}")
                    print_info(f"  - status: {txn['status']}")
                    print_info(f"  - amount: {txn['amount']}")
                    
                    if txn['payment_status'] == 'initiated':
                        record_result("Checkout session", True, "Session created and payment_transactions row verified")
                        return True, session_id
                    else:
                        record_result("Checkout session", False, f"Unexpected payment_status: {txn['payment_status']}")
                        return False, session_id
                else:
                    record_result("Checkout session", False, "payment_transactions row not found in database")
                    return False, session_id
            else:
                record_result("Checkout session", False, "Missing url or session_id in response")
                return False, None
        else:
            record_result("Checkout session", False, f"Status {response.status_code}: {data}")
            return False, None
    except Exception as e:
        record_result("Checkout session", False, f"Exception: {str(e)}")
        return False, None


def test_8_checkout_status(session_id):
    """Test 8: GET /api/checkout/status returns payment_status and booking"""
    print_test("8. GET /api/checkout/status - Check payment status")
    
    if not session_id:
        print_fail("No session_id provided, skipping test")
        record_result("Checkout status", False, "No session_id available")
        return
    
    print_section("8a. Valid session_id")
    try:
        response = requests.get(f"{BASE_URL}/checkout/status/{session_id}")
        print_info(f"Status: {response.status_code}")
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            required_fields = ["payment_status", "status", "booking"]
            all_present = all(field in data for field in required_fields)
            
            if all_present:
                print_info(f"payment_status: {data['payment_status']}")
                print_info(f"status: {data['status']}")
                print_info(f"booking present: {data['booking'] is not None}")
                record_result("Checkout status", True, "Returns payment_status, status, and booking")
            else:
                record_result("Checkout status", False, "Missing required fields")
        else:
            record_result("Checkout status", False, f"Status {response.status_code}")
    except Exception as e:
        record_result("Checkout status", False, f"Exception: {str(e)}")
    
    print_section("8b. Nonexistent session_id - should return 404")
    try:
        response = requests.get(f"{BASE_URL}/checkout/status/bad_session_id_12345")
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 404:
            record_result("Checkout status: nonexistent session", True, "Returns 404 for invalid session_id")
        else:
            record_result("Checkout status: nonexistent session", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        record_result("Checkout status: nonexistent session", False, f"Exception: {str(e)}")


def test_9_admin_bookings():
    """Test 9: GET /api/admin/bookings with authentication"""
    print_test("9. GET /api/admin/bookings - Admin authentication")
    
    print_section("9a. Without X-Admin-Key header - should return 401")
    try:
        response = requests.get(f"{BASE_URL}/admin/bookings")
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            record_result("Admin bookings: no auth", True, "Returns 401 without header")
        else:
            record_result("Admin bookings: no auth", False, f"Expected 401, got {response.status_code}")
    except Exception as e:
        record_result("Admin bookings: no auth", False, f"Exception: {str(e)}")
    
    print_section("9b. With X-Admin-Key header - should return bookings")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.get(f"{BASE_URL}/admin/bookings", headers=headers)
        print_info(f"Status: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            if "bookings" in data:
                bookings = data["bookings"]
                print_info(f"Number of bookings: {len(bookings)}")
                
                if len(bookings) > 0:
                    first_booking = bookings[0]
                    print_info(f"First booking keys: {list(first_booking.keys())}")
                    
                    if "display_status" in first_booking:
                        record_result("Admin bookings: with auth", True, f"Returns bookings array with display_status ({len(bookings)} bookings)")
                    else:
                        record_result("Admin bookings: with auth", False, "Missing display_status field")
                else:
                    record_result("Admin bookings: with auth", True, "Returns empty bookings array (no bookings yet)")
            else:
                record_result("Admin bookings: with auth", False, "Missing 'bookings' key in response")
        else:
            record_result("Admin bookings: with auth", False, f"Status {response.status_code}")
    except Exception as e:
        record_result("Admin bookings: with auth", False, f"Exception: {str(e)}")


def test_10_admin_settings():
    """Test 10: PUT /api/admin/settings with authentication and validation"""
    print_test("10. Admin Settings Management")
    
    print_section("10a. PUT without X-Admin-Key - should return 401")
    try:
        response = requests.put(f"{BASE_URL}/admin/settings", json={
            "single_visit_price": 75,
            "extra_dog_price": 40
        })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            record_result("Admin settings: no auth", True, "Returns 401 without header")
        else:
            record_result("Admin settings: no auth", False, f"Expected 401, got {response.status_code}")
    except Exception as e:
        record_result("Admin settings: no auth", False, f"Exception: {str(e)}")
    
    print_section("10b. PUT with X-Admin-Key - update settings")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.put(f"{BASE_URL}/admin/settings", 
                               headers=headers,
                               json={
                                   "single_visit_price": 75,
                                   "extra_dog_price": 40
                               })
        print_info(f"Status: {response.status_code}")
        data = response.json()
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            if data.get("single_visit_price") == 75 and data.get("extra_dog_price") == 40:
                record_result("Admin settings: update", True, "Settings updated successfully")
            else:
                record_result("Admin settings: update", False, "Settings not updated correctly")
        else:
            record_result("Admin settings: update", False, f"Status {response.status_code}")
    except Exception as e:
        record_result("Admin settings: update", False, f"Exception: {str(e)}")
    
    print_section("10c. GET /api/settings - verify changes persisted")
    try:
        response = requests.get(f"{BASE_URL}/settings")
        data = response.json()
        print_info(f"Current settings: single_visit_price={data.get('single_visit_price')}, extra_dog_price={data.get('extra_dog_price')}")
        
        if data.get("single_visit_price") == 75 and data.get("extra_dog_price") == 40:
            record_result("Admin settings: persistence", True, "Updated settings persisted in database")
        else:
            record_result("Admin settings: persistence", False, "Settings not persisted correctly")
    except Exception as e:
        record_result("Admin settings: persistence", False, f"Exception: {str(e)}")
    
    print_section("10d. Reset to defaults")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.put(f"{BASE_URL}/admin/settings", 
                               headers=headers,
                               json={
                                   "single_visit_price": 60,
                                   "extra_dog_price": 30,
                                   "ten_trip_price": 560
                               })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            record_result("Admin settings: reset", True, "Settings reset to defaults")
        else:
            record_result("Admin settings: reset", False, f"Failed to reset: {response.status_code}")
    except Exception as e:
        record_result("Admin settings: reset", False, f"Exception: {str(e)}")


def test_11_admin_content():
    """Test 11: GET /api/content and PUT /api/admin/content"""
    print_test("11. Content Management (CMS)")
    
    print_section("11a. GET /api/content - public access")
    try:
        response = requests.get(f"{BASE_URL}/content")
        print_info(f"Status: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            required_sections = ["hero", "about", "contact"]
            all_present = all(section in data for section in required_sections)
            
            if all_present:
                print_info(f"Sections present: {list(data.keys())}")
                print_info(f"Hero fields: {list(data['hero'].keys())}")
                print_info(f"Contact phone: {data['contact'].get('phone')}")
                record_result("Content: GET", True, "Returns all sections (hero, about, contact)")
            else:
                record_result("Content: GET", False, "Missing required sections")
        else:
            record_result("Content: GET", False, f"Status {response.status_code}")
    except Exception as e:
        record_result("Content: GET", False, f"Exception: {str(e)}")
    
    print_section("11b. PUT /api/admin/content without X-Admin-Key - should return 401")
    try:
        response = requests.put(f"{BASE_URL}/admin/content", json={
            "contact": {"phone": "+45 99 99 99 99"}
        })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            record_result("Content: PUT no auth", True, "Returns 401 without header")
        else:
            record_result("Content: PUT no auth", False, f"Expected 401, got {response.status_code}")
    except Exception as e:
        record_result("Content: PUT no auth", False, f"Exception: {str(e)}")
    
    print_section("11c. PUT /api/admin/content with X-Admin-Key - partial update")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.put(f"{BASE_URL}/admin/content", 
                               headers=headers,
                               json={
                                   "contact": {"phone": "+45 99 99 99 99"}
                               })
        print_info(f"Status: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            if data.get("contact", {}).get("phone") == "+45 99 99 99 99":
                print_info("Phone number updated successfully")
                # Verify other fields preserved
                if "hero" in data and "about" in data:
                    record_result("Content: PUT update", True, "Partial update successful, other sections preserved")
                else:
                    record_result("Content: PUT update", False, "Other sections not preserved")
            else:
                record_result("Content: PUT update", False, "Phone not updated correctly")
        else:
            record_result("Content: PUT update", False, f"Status {response.status_code}")
    except Exception as e:
        record_result("Content: PUT update", False, f"Exception: {str(e)}")
    
    print_section("11d. GET /api/content - verify changes persisted")
    try:
        response = requests.get(f"{BASE_URL}/content")
        data = response.json()
        phone = data.get("contact", {}).get("phone")
        print_info(f"Current phone: {phone}")
        
        if phone == "+45 99 99 99 99":
            record_result("Content: persistence", True, "Updated content persisted in database")
        else:
            record_result("Content: persistence", False, f"Expected '+45 99 99 99 99', got '{phone}'")
    except Exception as e:
        record_result("Content: persistence", False, f"Exception: {str(e)}")
    
    print_section("11e. Reset to default phone")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.put(f"{BASE_URL}/admin/content", 
                               headers=headers,
                               json={
                                   "contact": {"phone": "+45 93 84 18 68"}
                               })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            record_result("Content: reset", True, "Content reset to defaults")
        else:
            record_result("Content: reset", False, f"Failed to reset: {response.status_code}")
    except Exception as e:
        record_result("Content: reset", False, f"Exception: {str(e)}")


def print_summary():
    """Print test summary"""
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}TEST SUMMARY{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}")
    
    total = test_results["total"]
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    
    print(f"\nTotal Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    
    if failed > 0:
        print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
        for test in test_results["failed"]:
            print(f"  {Colors.RED}✗ {test}{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}ALL TESTS PASSED! ✓{Colors.END}")
        print(f"{Colors.GREEN}{'='*80}{Colors.END}")
    else:
        print(f"\n{Colors.RED}{'='*80}{Colors.END}")
        print(f"{Colors.RED}SOME TESTS FAILED{Colors.END}")
        print(f"{Colors.RED}{'='*80}{Colors.END}")


def main():
    """Run all tests"""
    print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}ALBØGE HUNDEPARK - BACKEND REGRESSION TEST SUITE{Colors.END}")
    print(f"{Colors.CYAN}Testing Supabase Postgres Migration{Colors.END}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"\n{Colors.YELLOW}Base URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.YELLOW}Admin Key: {ADMIN_KEY}{Colors.END}")
    print(f"{Colors.YELLOW}Database: Supabase Postgres (SQLAlchemy + asyncpg){Colors.END}\n")
    
    # Run all tests in sequence
    test_1_root_endpoint()
    
    success, settings = test_2_get_settings()
    
    success, test_date = test_3_get_slots()
    
    success, booking_id, booking_date = test_4_create_booking()
    
    if booking_date:
        test_5_slot_lock_verification(booking_date)
    
    test_6_validation()
    
    success, session_id = test_7_checkout_session(booking_id)
    
    test_8_checkout_status(session_id)
    
    test_9_admin_bookings()
    
    test_10_admin_settings()
    
    test_11_admin_content()
    
    # Print summary
    print_summary()
    
    # Cleanup
    asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
