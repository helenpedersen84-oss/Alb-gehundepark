#!/usr/bin/env python3
"""
Backend API Test Suite for Albøge Hundepark Booking System
Tests all /api endpoints with realistic data
"""

import requests
import json
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# Configuration
BASE_URL = "https://dog-haven-checkout.preview.emergentagent.com/api"
ADMIN_KEY = "Caroline1?"
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Test data
def get_future_date(days_ahead=7):
    """Get a future date in YYYY-MM-DD format"""
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

def get_past_date():
    """Get a past date in YYYY-MM-DD format"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
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

# MongoDB helper for verification
async def check_payment_transaction(session_id):
    """Check if payment transaction exists in database"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    client.close()
    return txn

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

def test_2_get_slots():
    """Test 2: GET /api/slots returns 17 slots (5-21) with correct structure"""
    print_test("2. GET /api/slots - List available slots")
    
    future_date = get_future_date()
    print_info(f"Testing with date: {future_date}")
    
    try:
        response = requests.get(f"{BASE_URL}/slots", params={"date": future_date})
        print_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            record_result("Get slots", False, f"Status code {response.status_code}")
            return False, future_date
        
        data = response.json()
        print_info(f"Response keys: {data.keys()}")
        
        if "slots" not in data:
            record_result("Get slots", False, "No 'slots' key in response")
            return False, future_date
        
        slots = data["slots"]
        print_info(f"Number of slots: {len(slots)}")
        
        # Check we have 17 slots (hours 5-21)
        if len(slots) != 17:
            record_result("Get slots", False, f"Expected 17 slots, got {len(slots)}")
            return False, future_date
        
        # Check first and last slot
        first_slot = slots[0]
        last_slot = slots[-1]
        print_info(f"First slot: hour={first_slot.get('hour')}, status={first_slot.get('status')}")
        print_info(f"Last slot: hour={last_slot.get('hour')}, status={last_slot.get('status')}")
        
        # Verify structure
        required_keys = ["hour", "start", "end", "label", "status"]
        for key in required_keys:
            if key not in first_slot:
                record_result("Get slots", False, f"Missing key '{key}' in slot")
                return False, future_date
        
        # Verify hour range
        if first_slot["hour"] != 5 or last_slot["hour"] != 21:
            record_result("Get slots", False, f"Hour range incorrect: {first_slot['hour']}-{last_slot['hour']}")
            return False, future_date
        
        # Check all initially available
        all_available = all(slot["status"] == "available" for slot in slots)
        if all_available:
            print_info("All slots initially available ✓")
        
        record_result("Get slots", True, f"Returns 17 slots (5-21) with correct structure")
        return True, future_date
        
    except Exception as e:
        record_result("Get slots", False, f"Exception: {str(e)}")
        return False, future_date

def test_3_create_booking(test_date):
    """Test 3: POST /api/bookings creates booking with correct amount"""
    print_test("3. POST /api/bookings - Create booking")
    
    print_info(f"Creating booking for date: {test_date}, hour: 10")
    
    booking_data = {
        "date": test_date,
        "hour": 10,
        "name": "Lars Nielsen",
        "email": "lars.nielsen@example.dk",
        "phone": "45123456",
        "dogs": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("Create booking", False, f"Status code {response.status_code}: {response.json()}")
            return False, None
        
        data = response.json()
        
        # Check required fields
        if "booking_id" not in data or "expires_at" not in data or "amount" not in data:
            record_result("Create booking", False, "Missing required fields in response")
            return False, None
        
        booking_id = data["booking_id"]
        amount = data["amount"]
        expires_at = data["expires_at"]
        
        print_info(f"Booking ID: {booking_id}")
        print_info(f"Amount: {amount} DKK")
        print_info(f"Expires at: {expires_at}")
        
        # Verify amount calculation: 60 + 30 for 2nd dog = 90
        expected_amount = 90.0
        if amount != expected_amount:
            record_result("Create booking", False, f"Amount incorrect: expected {expected_amount}, got {amount}")
            return False, booking_id
        
        # Verify expires_at is ~15 minutes in future
        try:
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            now = datetime.now(expires_dt.tzinfo)
            time_diff = (expires_dt - now).total_seconds() / 60
            print_info(f"Expiry time difference: {time_diff:.1f} minutes")
            
            if not (14 <= time_diff <= 16):
                print_fail(f"Expiry time not ~15 minutes: {time_diff:.1f} minutes")
        except Exception as e:
            print_fail(f"Could not parse expires_at: {e}")
        
        record_result("Create booking", True, f"Booking created with correct amount (90 DKK)")
        return True, booking_id
        
    except Exception as e:
        record_result("Create booking", False, f"Exception: {str(e)}")
        return False, None

def test_4_slot_lock_verification(test_date, booking_id):
    """Test 4: Verify slot is locked after booking and duplicate booking returns 409"""
    print_test("4. Slot Lock Verification")
    
    # Part A: Check slot is now locked
    print_info("Part A: Checking slot status after booking")
    try:
        response = requests.get(f"{BASE_URL}/slots", params={"date": test_date})
        if response.status_code != 200:
            record_result("Slot lock check", False, f"Could not fetch slots: {response.status_code}")
            return False
        
        slots = response.json()["slots"]
        hour_10_slot = next((s for s in slots if s["hour"] == 10), None)
        
        if not hour_10_slot:
            record_result("Slot lock check", False, "Hour 10 slot not found")
            return False
        
        print_info(f"Hour 10 slot status: {hour_10_slot['status']}")
        
        if hour_10_slot["status"] != "locked":
            record_result("Slot lock check", False, f"Expected 'locked', got '{hour_10_slot['status']}'")
            return False
        
        print_pass("Slot correctly marked as 'locked'")
        
    except Exception as e:
        record_result("Slot lock check", False, f"Exception: {str(e)}")
        return False
    
    # Part B: Try to book same slot again - should get 409
    print_info("Part B: Attempting duplicate booking (should fail with 409)")
    
    duplicate_booking = {
        "date": test_date,
        "hour": 10,
        "name": "Anna Hansen",
        "email": "anna@example.dk",
        "phone": "45987654",
        "dogs": 1
    }
    
    try:
        response = requests.post(f"{BASE_URL}/bookings", json=duplicate_booking)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code == 409:
            record_result("Slot lock verification", True, "Duplicate booking correctly rejected with 409")
            return True
        else:
            record_result("Slot lock verification", False, f"Expected 409, got {response.status_code}")
            return False
            
    except Exception as e:
        record_result("Slot lock verification", False, f"Exception: {str(e)}")
        return False

def test_5_validation():
    """Test 5: Validation - invalid hour, past date, missing fields"""
    print_test("5. Validation Tests")
    
    all_passed = True
    
    # Test A: Invalid hour (23 is outside 5-21 range)
    print_info("Test A: Invalid hour (23)")
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": get_future_date(),
            "hour": 23,
            "name": "Test User",
            "email": "test@example.dk",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        if response.status_code == 400:
            print_pass("Invalid hour correctly rejected with 400")
        else:
            print_fail(f"Expected 400, got {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        all_passed = False
    
    # Test B: Past date
    print_info("Test B: Past date")
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": get_past_date(),
            "hour": 10,
            "name": "Test User",
            "email": "test@example.dk",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        if response.status_code == 400:
            print_pass("Past date correctly rejected with 400")
        else:
            print_fail(f"Expected 400, got {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        all_passed = False
    
    # Test C: Missing name
    print_info("Test C: Missing name")
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": get_future_date(),
            "hour": 10,
            "name": "",
            "email": "test@example.dk",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        if response.status_code in [400, 422]:
            print_pass("Missing name correctly rejected")
        else:
            print_fail(f"Expected 400/422, got {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        all_passed = False
    
    # Test D: Missing email
    print_info("Test D: Missing email")
    try:
        response = requests.post(f"{BASE_URL}/bookings", json={
            "date": get_future_date(),
            "hour": 10,
            "name": "Test User",
            "email": "",
            "dogs": 1
        })
        print_info(f"Status: {response.status_code}")
        if response.status_code in [400, 422]:
            print_pass("Missing email correctly rejected")
        else:
            print_fail(f"Expected 400/422, got {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        all_passed = False
    
    if all_passed:
        record_result("Validation tests", True, "All validation tests passed")
    else:
        record_result("Validation tests", False, "Some validation tests failed")
    
    return all_passed

def test_6_checkout_session(booking_id):
    """Test 6: POST /api/checkout/session creates Stripe session and payment transaction"""
    print_test("6. POST /api/checkout/session - Create Stripe checkout")
    
    if not booking_id:
        record_result("Checkout session", False, "No booking_id available")
        return False, None
    
    print_info(f"Creating checkout session for booking: {booking_id}")
    
    checkout_data = {
        "booking_id": booking_id,
        "origin_url": "https://example.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/checkout/session", json=checkout_data)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("Checkout session", False, f"Status code {response.status_code}: {response.json()}")
            return False, None
        
        data = response.json()
        
        # Check required fields
        if "url" not in data or "session_id" not in data:
            record_result("Checkout session", False, "Missing 'url' or 'session_id' in response")
            return False, None
        
        session_id = data["session_id"]
        url = data["url"]
        
        print_info(f"Session ID: {session_id}")
        print_info(f"Checkout URL: {url[:80]}...")
        
        # Verify URL is a Stripe checkout URL
        if not url.startswith("https://checkout.stripe.com"):
            print_fail(f"URL doesn't look like Stripe checkout: {url}")
        
        # Verify payment_transactions record was created
        print_info("Checking payment_transactions record in database...")
        txn = asyncio.run(check_payment_transaction(session_id))
        
        if not txn:
            record_result("Checkout session", False, "No payment_transactions record found in database")
            return False, session_id
        
        print_info(f"Transaction found: payment_status={txn.get('payment_status')}")
        
        if txn.get("payment_status") != "initiated":
            print_fail(f"Expected payment_status 'initiated', got '{txn.get('payment_status')}'")
        else:
            print_pass("Payment transaction record created with status 'initiated'")
        
        record_result("Checkout session", True, "Session created and payment_transactions record exists")
        return True, session_id
        
    except Exception as e:
        record_result("Checkout session", False, f"Exception: {str(e)}")
        return False, None

def test_7_checkout_status(session_id):
    """Test 7: GET /api/checkout/status/{session_id} returns payment status"""
    print_test("7. GET /api/checkout/status - Check payment status")
    
    if not session_id:
        record_result("Checkout status", False, "No session_id available")
        return False
    
    print_info(f"Checking status for session: {session_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/checkout/status/{session_id}")
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("Checkout status", False, f"Status code {response.status_code}")
            return False
        
        data = response.json()
        
        # Check required fields
        if "payment_status" not in data or "status" not in data:
            record_result("Checkout status", False, "Missing 'payment_status' or 'status' in response")
            return False
        
        print_info(f"Payment status: {data['payment_status']}")
        print_info(f"Status: {data['status']}")
        
        # Since we didn't complete payment, should be unpaid/open
        if data["payment_status"] in ["unpaid", "initiated"]:
            print_pass("Payment status is unpaid/initiated (expected, no payment completed)")
        
        record_result("Checkout status", True, "Returns payment_status and status fields")
        return True
        
    except Exception as e:
        record_result("Checkout status", False, f"Exception: {str(e)}")
        return False

def test_8_admin_endpoint():
    """Test 8: GET /api/admin/bookings with and without admin key"""
    print_test("8. GET /api/admin/bookings - Admin authentication")
    
    # Test A: Without admin key - should get 401
    print_info("Test A: Request without X-Admin-Key header")
    try:
        response = requests.get(f"{BASE_URL}/admin/bookings")
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print_pass("Correctly rejected with 401")
        else:
            print_fail(f"Expected 401, got {response.status_code}")
            record_result("Admin endpoint", False, f"Without key: expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_result("Admin endpoint", False, f"Exception: {str(e)}")
        return False
    
    # Test B: With admin key - should get bookings
    print_info("Test B: Request with X-Admin-Key header")
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.get(f"{BASE_URL}/admin/bookings", headers=headers)
        print_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            record_result("Admin endpoint", False, f"With key: expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        print_info(f"Response keys: {data.keys()}")
        
        if "bookings" not in data:
            record_result("Admin endpoint", False, "No 'bookings' key in response")
            return False
        
        bookings = data["bookings"]
        print_info(f"Number of bookings: {len(bookings)}")
        
        # Check if our test booking is there
        if len(bookings) > 0:
            first_booking = bookings[0]
            print_info(f"First booking keys: {first_booking.keys()}")
            
            if "display_status" not in first_booking:
                print_fail("Missing 'display_status' field")
            else:
                print_info(f"Display status: {first_booking['display_status']}")
                print_pass("Bookings include display_status field")
        
        record_result("Admin endpoint", True, "Authentication works, returns bookings with display_status")
        return True
        
    except Exception as e:
        record_result("Admin endpoint", False, f"Exception: {str(e)}")
        return False

def test_9_error_cases():
    """Test 9: Error cases - nonexistent booking, nonexistent session"""
    print_test("9. Error Cases")
    
    all_passed = True
    
    # Test A: Checkout session for nonexistent booking
    print_info("Test A: Checkout session for nonexistent booking")
    try:
        response = requests.post(f"{BASE_URL}/checkout/session", json={
            "booking_id": "nonexistent-booking-id",
            "origin_url": "https://example.com"
        })
        print_info(f"Status: {response.status_code}")
        if response.status_code == 404:
            print_pass("Nonexistent booking correctly returns 404")
        else:
            print_fail(f"Expected 404, got {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        all_passed = False
    
    # Test B: Status for nonexistent session
    print_info("Test B: Status for nonexistent session_id")
    try:
        response = requests.get(f"{BASE_URL}/checkout/status/bad_session")
        print_info(f"Status: {response.status_code}")
        if response.status_code == 404:
            print_pass("Nonexistent session correctly returns 404")
        else:
            print_fail(f"Expected 404, got {response.status_code}")
            all_passed = False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        all_passed = False
    
    if all_passed:
        record_result("Error cases", True, "All error cases handled correctly")
    else:
        record_result("Error cases", False, "Some error cases not handled correctly")
    
    return all_passed

def test_10_settings_public():
    """Test 10: GET /api/settings - public endpoint returns pricing and hours"""
    print_test("10. GET /api/settings - Public settings endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/settings")
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("GET /api/settings", False, f"Status code {response.status_code}")
            return False, None
        
        data = response.json()
        
        # Check required fields
        required_fields = ["single_visit_price", "extra_dog_price", "ten_trip_price", "currency", "open_hour", "close_hour"]
        for field in required_fields:
            if field not in data:
                record_result("GET /api/settings", False, f"Missing field '{field}'")
                return False, None
        
        print_info(f"single_visit_price: {data['single_visit_price']}")
        print_info(f"extra_dog_price: {data['extra_dog_price']}")
        print_info(f"ten_trip_price: {data['ten_trip_price']}")
        print_info(f"currency: {data['currency']}")
        print_info(f"open_hour: {data['open_hour']}")
        print_info(f"close_hour: {data['close_hour']}")
        
        # Verify expected values
        if data['open_hour'] != 5:
            print_fail(f"Expected open_hour=5, got {data['open_hour']}")
        if data['close_hour'] != 22:
            print_fail(f"Expected close_hour=22, got {data['close_hour']}")
        
        record_result("GET /api/settings", True, "Returns all required fields with correct structure")
        return True, data
        
    except Exception as e:
        record_result("GET /api/settings", False, f"Exception: {str(e)}")
        return False, None

def test_11_admin_settings_no_auth():
    """Test 11: PUT /api/admin/settings without X-Admin-Key → 401"""
    print_test("11. PUT /api/admin/settings - Without authentication")
    
    try:
        response = requests.put(f"{BASE_URL}/admin/settings", json={
            "single_visit_price": 75
        })
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            record_result("PUT /api/admin/settings (no auth)", True, "Correctly rejected with 401")
            return True
        else:
            record_result("PUT /api/admin/settings (no auth)", False, f"Expected 401, got {response.status_code}")
            return False
            
    except Exception as e:
        record_result("PUT /api/admin/settings (no auth)", False, f"Exception: {str(e)}")
        return False

def test_12_admin_settings_update():
    """Test 12: PUT /api/admin/settings with auth → updates settings"""
    print_test("12. PUT /api/admin/settings - Update pricing with authentication")
    
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        update_data = {
            "single_visit_price": 75,
            "extra_dog_price": 40
        }
        
        response = requests.put(f"{BASE_URL}/admin/settings", json=update_data, headers=headers)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("PUT /api/admin/settings (with auth)", False, f"Status code {response.status_code}: {response.json()}")
            return False
        
        data = response.json()
        
        # Verify updated values
        if data.get('single_visit_price') != 75:
            record_result("PUT /api/admin/settings (with auth)", False, f"Expected single_visit_price=75, got {data.get('single_visit_price')}")
            return False
        
        if data.get('extra_dog_price') != 40:
            record_result("PUT /api/admin/settings (with auth)", False, f"Expected extra_dog_price=40, got {data.get('extra_dog_price')}")
            return False
        
        print_pass(f"Settings updated: single_visit_price={data['single_visit_price']}, extra_dog_price={data['extra_dog_price']}")
        record_result("PUT /api/admin/settings (with auth)", True, "Settings updated successfully")
        return True
        
    except Exception as e:
        record_result("PUT /api/admin/settings (with auth)", False, f"Exception: {str(e)}")
        return False

def test_13_settings_verify_update():
    """Test 13: GET /api/settings again → verify updated values"""
    print_test("13. GET /api/settings - Verify updated values persist")
    
    try:
        response = requests.get(f"{BASE_URL}/settings")
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("Verify settings update", False, f"Status code {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify updated values
        if data.get('single_visit_price') != 75:
            record_result("Verify settings update", False, f"Expected single_visit_price=75, got {data.get('single_visit_price')}")
            return False
        
        if data.get('extra_dog_price') != 40:
            record_result("Verify settings update", False, f"Expected extra_dog_price=40, got {data.get('extra_dog_price')}")
            return False
        
        print_pass("Settings correctly reflect updated values: 75/40")
        record_result("Verify settings update", True, "Updated settings persist correctly")
        return True
        
    except Exception as e:
        record_result("Verify settings update", False, f"Exception: {str(e)}")
        return False

def test_14_booking_with_live_pricing():
    """Test 14: Booking amount reflects live settings (3 dogs → 75 + 2*40 = 155)"""
    print_test("14. POST /api/bookings - Verify booking uses live pricing")
    
    future_date = get_future_date(14)  # Use a different date to avoid conflicts
    print_info(f"Creating booking for date: {future_date}, hour: 14, dogs: 3")
    
    booking_data = {
        "date": future_date,
        "hour": 14,
        "name": "Mette Frederiksen",
        "email": "mette.f@example.dk",
        "phone": "45234567",
        "dogs": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("Booking with live pricing", False, f"Status code {response.status_code}: {response.json()}")
            return False, None
        
        data = response.json()
        amount = data.get("amount")
        
        # Expected: 75 (base) + 2 * 40 (2 extra dogs) = 155
        expected_amount = 155.0
        
        print_info(f"Amount: {amount} DKK (expected: {expected_amount} DKK)")
        
        if amount != expected_amount:
            record_result("Booking with live pricing", False, f"Expected amount {expected_amount}, got {amount}")
            return False, data.get("booking_id")
        
        print_pass(f"Booking amount correctly calculated: 75 + 2*40 = 155 DKK")
        record_result("Booking with live pricing", True, "Booking uses live pricing settings")
        return True, data.get("booking_id")
        
    except Exception as e:
        record_result("Booking with live pricing", False, f"Exception: {str(e)}")
        return False, None

def test_15_negative_price_validation():
    """Test 15: PUT /api/admin/settings with negative value → 400"""
    print_test("15. PUT /api/admin/settings - Negative price validation")
    
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        update_data = {
            "single_visit_price": -5
        }
        
        response = requests.put(f"{BASE_URL}/admin/settings", json=update_data, headers=headers)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print_pass("Negative price correctly rejected with 400")
            record_result("Negative price validation", True, "Negative prices rejected")
            return True
        else:
            record_result("Negative price validation", False, f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        record_result("Negative price validation", False, f"Exception: {str(e)}")
        return False

def test_16_cleanup_reset_defaults():
    """Test 16: CLEANUP - Reset settings to defaults (60/30/560)"""
    print_test("16. CLEANUP - Reset settings to defaults")
    
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        reset_data = {
            "single_visit_price": 60,
            "extra_dog_price": 30,
            "ten_trip_price": 560
        }
        
        response = requests.put(f"{BASE_URL}/admin/settings", json=reset_data, headers=headers)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code != 200:
            record_result("Cleanup - reset defaults", False, f"Status code {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify reset values
        if data.get('single_visit_price') != 60:
            print_fail(f"Expected single_visit_price=60, got {data.get('single_visit_price')}")
            record_result("Cleanup - reset defaults", False, "Failed to reset single_visit_price")
            return False
        
        if data.get('extra_dog_price') != 30:
            print_fail(f"Expected extra_dog_price=30, got {data.get('extra_dog_price')}")
            record_result("Cleanup - reset defaults", False, "Failed to reset extra_dog_price")
            return False
        
        if data.get('ten_trip_price') != 560:
            print_fail(f"Expected ten_trip_price=560, got {data.get('ten_trip_price')}")
            record_result("Cleanup - reset defaults", False, "Failed to reset ten_trip_price")
            return False
        
        print_pass("Settings reset to defaults: 60/30/560")
        
        # Verify with GET
        print_info("Verifying with GET /api/settings...")
        verify_response = requests.get(f"{BASE_URL}/settings")
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            print_info(f"Verified: single_visit_price={verify_data.get('single_visit_price')}, extra_dog_price={verify_data.get('extra_dog_price')}, ten_trip_price={verify_data.get('ten_trip_price')}")
            
            if verify_data.get('single_visit_price') == 60 and verify_data.get('extra_dog_price') == 30 and verify_data.get('ten_trip_price') == 560:
                print_pass("GET /api/settings confirms defaults: 60/30/560")
                record_result("Cleanup - reset defaults", True, "Settings successfully reset to defaults")
                return True
            else:
                record_result("Cleanup - reset defaults", False, "GET /api/settings shows incorrect values after reset")
                return False
        else:
            record_result("Cleanup - reset defaults", False, "Could not verify reset with GET")
            return False
        
    except Exception as e:
        record_result("Cleanup - reset defaults", False, f"Exception: {str(e)}")
        return False

def print_summary():
    """Print test summary"""
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    total = test_results["total"]
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    
    print(f"\nTotal tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    
    if failed > 0:
        print(f"\n{Colors.RED}Failed tests:{Colors.END}")
        for test in test_results["failed"]:
            print(f"  - {test}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{'='*80}")
        print(f"ALL TESTS PASSED! ✓")
        print(f"{'='*80}{Colors.END}")
    else:
        print(f"\n{Colors.RED}{'='*80}")
        print(f"SOME TESTS FAILED")
        print(f"{'='*80}{Colors.END}")

def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"Albøge Hundepark Backend API Test Suite")
    print(f"{'='*80}{Colors.END}")
    print(f"Base URL: {BASE_URL}")
    print(f"Admin Key: {ADMIN_KEY}")
    print(f"{'='*80}\n")
    
    # Run tests in sequence
    test_1_root_endpoint()
    
    success, test_date = test_2_get_slots()
    
    if success:
        success, booking_id = test_3_create_booking(test_date)
        
        if success and booking_id:
            test_4_slot_lock_verification(test_date, booking_id)
            
            success, session_id = test_6_checkout_session(booking_id)
            
            if success and session_id:
                test_7_checkout_status(session_id)
    
    test_5_validation()
    test_8_admin_endpoint()
    test_9_error_cases()
    
    # New settings/pricing tests
    test_10_settings_public()
    test_11_admin_settings_no_auth()
    test_12_admin_settings_update()
    test_13_settings_verify_update()
    test_14_booking_with_live_pricing()
    test_15_negative_price_validation()
    test_16_cleanup_reset_defaults()
    
    print_summary()

if __name__ == "__main__":
    main()
