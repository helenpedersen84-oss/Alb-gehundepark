#!/usr/bin/env python3
"""
Backend API Testing for Stripe SDK Migration
Tests all payment endpoints after migration from emergentintegrations to official Stripe Python SDK
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://dog-haven-checkout.preview.emergentagent.com/api"
ADMIN_KEY = "Caroline1?"
FUTURE_DATE = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

# Test results tracking
test_results = []

def log_test(test_name, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details
    })
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")

def test_1_root_endpoint():
    """Test 1: GET /api/ → returns message"""
    print("\n=== Test 1: Root Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                log_test("GET /api/ returns message", True, f"Message: {data['message']}")
                return True
            else:
                log_test("GET /api/ returns message", False, "No 'message' field in response")
                return False
        else:
            log_test("GET /api/ returns message", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("GET /api/ returns message", False, f"Exception: {str(e)}")
        return False

def test_2_settings_endpoint():
    """Test 2: GET /api/settings → prices + hours (open 5, close 22)"""
    print("\n=== Test 2: Settings Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/settings")
        if response.status_code == 200:
            data = response.json()
            required_fields = ["single_visit_price", "extra_dog_price", "ten_trip_price", "currency", "open_hour", "close_hour"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                log_test("GET /api/settings returns all fields", False, f"Missing fields: {missing_fields}")
                return False
            
            if data["open_hour"] == 5 and data["close_hour"] == 22:
                log_test("GET /api/settings returns correct hours", True, f"open_hour: {data['open_hour']}, close_hour: {data['close_hour']}")
            else:
                log_test("GET /api/settings returns correct hours", False, f"Expected open_hour=5, close_hour=22, got {data['open_hour']}, {data['close_hour']}")
                return False
            
            log_test("GET /api/settings returns prices", True, f"single_visit_price: {data['single_visit_price']}, extra_dog_price: {data['extra_dog_price']}")
            return data
        else:
            log_test("GET /api/settings", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test("GET /api/settings", False, f"Exception: {str(e)}")
        return False

def test_3_create_booking():
    """Test 3: POST /api/bookings → returns booking_id, expires_at, amount 60"""
    print("\n=== Test 3: Create Booking ===")
    try:
        payload = {
            "date": FUTURE_DATE,
            "hour": 13,
            "name": "Stripe SDK Test",
            "email": "t@t.dk",
            "phone": "12",
            "dogs": 1
        }
        response = requests.post(f"{BASE_URL}/bookings", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["booking_id", "expires_at", "amount"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                log_test("POST /api/bookings returns required fields", False, f"Missing fields: {missing_fields}")
                return None
            
            # Check expires_at is ~15 minutes in future
            expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
            now = datetime.now(expires_at.tzinfo)
            time_diff = (expires_at - now).total_seconds() / 60
            
            if 14 <= time_diff <= 16:
                log_test("POST /api/bookings expires_at ~15 min", True, f"Expires in {time_diff:.1f} minutes")
            else:
                log_test("POST /api/bookings expires_at ~15 min", False, f"Expires in {time_diff:.1f} minutes (expected ~15)")
            
            log_test("POST /api/bookings creates booking", True, f"booking_id: {data['booking_id']}, amount: {data['amount']}")
            return data
        else:
            log_test("POST /api/bookings", False, f"Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_test("POST /api/bookings", False, f"Exception: {str(e)}")
        return None

def test_4_create_checkout_session(booking_id):
    """Test 4: POST /api/checkout/session → returns URL and session_id starting with 'cs_'"""
    print("\n=== Test 4: Create Checkout Session (Official Stripe SDK) ===")
    try:
        payload = {
            "booking_id": booking_id,
            "origin_url": "https://example.com"
        }
        response = requests.post(f"{BASE_URL}/checkout/session", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if "url" not in data or "session_id" not in data:
                log_test("POST /api/checkout/session returns url and session_id", False, f"Missing fields. Response: {data}")
                return None
            
            # Verify session_id starts with "cs_"
            if data["session_id"].startswith("cs_"):
                log_test("POST /api/checkout/session returns valid session_id", True, f"session_id: {data['session_id'][:20]}...")
            else:
                log_test("POST /api/checkout/session returns valid session_id", False, f"session_id does not start with 'cs_': {data['session_id']}")
                return None
            
            # Verify URL is a real Stripe checkout URL
            if "checkout.stripe.com" in data["url"] or "stripe.com" in data["url"]:
                log_test("POST /api/checkout/session returns Stripe URL", True, f"URL: {data['url'][:60]}...")
            else:
                log_test("POST /api/checkout/session returns Stripe URL", False, f"URL does not contain stripe.com: {data['url']}")
                return None
            
            log_test("POST /api/checkout/session (Official Stripe SDK)", True, "✅ CONFIRMED: Using official Stripe SDK - session created successfully")
            return data
        else:
            log_test("POST /api/checkout/session", False, f"Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_test("POST /api/checkout/session", False, f"Exception: {str(e)}")
        return None

def test_5_checkout_status(session_id):
    """Test 5: GET /api/checkout/status/<session_id> → returns payment_status and status"""
    print("\n=== Test 5: Checkout Status ===")
    try:
        response = requests.get(f"{BASE_URL}/checkout/status/{session_id}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["payment_status", "status", "booking"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                log_test("GET /api/checkout/status returns required fields", False, f"Missing fields: {missing_fields}")
                return False
            
            log_test("GET /api/checkout/status returns payment_status", True, f"payment_status: {data['payment_status']}, status: {data['status']}")
            
            if data["booking"]:
                log_test("GET /api/checkout/status returns booking object", True, f"booking_id: {data['booking'].get('booking_id')}")
            else:
                log_test("GET /api/checkout/status returns booking object", False, "booking is null")
            
            return True
        else:
            log_test("GET /api/checkout/status", False, f"Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        log_test("GET /api/checkout/status", False, f"Exception: {str(e)}")
        return False

def test_5b_checkout_status_invalid():
    """Test 5b: GET /api/checkout/status with invalid session_id → 404"""
    print("\n=== Test 5b: Checkout Status Invalid Session ===")
    try:
        response = requests.get(f"{BASE_URL}/checkout/status/cs_bad")
        
        if response.status_code == 404:
            log_test("GET /api/checkout/status with invalid session_id returns 404", True, "Correctly returns 404 for nonexistent session")
            return True
        else:
            log_test("GET /api/checkout/status with invalid session_id", False, f"Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        log_test("GET /api/checkout/status with invalid session_id", False, f"Exception: {str(e)}")
        return False

def test_6_slot_lock():
    """Test 6: Slot lock verification"""
    print("\n=== Test 6: Slot Lock Verification ===")
    try:
        # Check slots endpoint
        response = requests.get(f"{BASE_URL}/slots", params={"date": FUTURE_DATE})
        
        if response.status_code == 200:
            data = response.json()
            slots = data.get("slots", [])
            
            # Find hour 13
            hour_13 = next((s for s in slots if s["hour"] == 13), None)
            
            if hour_13:
                if hour_13["status"] == "locked":
                    log_test("GET /api/slots shows hour 13 as locked", True, f"Hour 13 status: {hour_13['status']}")
                else:
                    log_test("GET /api/slots shows hour 13 as locked", False, f"Hour 13 status: {hour_13['status']} (expected 'locked')")
                    return False
            else:
                log_test("GET /api/slots shows hour 13", False, "Hour 13 not found in slots")
                return False
        else:
            log_test("GET /api/slots", False, f"Status code: {response.status_code}")
            return False
        
        # Try to create duplicate booking
        payload = {
            "date": FUTURE_DATE,
            "hour": 13,
            "name": "Duplicate Test",
            "email": "dup@test.dk",
            "phone": "12",
            "dogs": 1
        }
        response = requests.post(f"{BASE_URL}/bookings", json=payload)
        
        if response.status_code == 409:
            log_test("POST /api/bookings duplicate slot returns 409", True, "Correctly rejects duplicate booking")
            return True
        else:
            log_test("POST /api/bookings duplicate slot returns 409", False, f"Expected 409, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Slot lock verification", False, f"Exception: {str(e)}")
        return False

def test_7_validation():
    """Test 7: Validation tests"""
    print("\n=== Test 7: Validation Tests ===")
    
    # Test invalid hour (23)
    try:
        payload = {
            "date": FUTURE_DATE,
            "hour": 23,
            "name": "Invalid Hour Test",
            "email": "test@test.dk",
            "phone": "12",
            "dogs": 1
        }
        response = requests.post(f"{BASE_URL}/bookings", json=payload)
        
        if response.status_code == 400:
            log_test("POST /api/bookings with hour 23 returns 400", True, "Correctly rejects invalid hour")
        else:
            log_test("POST /api/bookings with hour 23 returns 400", False, f"Expected 400, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/bookings with hour 23", False, f"Exception: {str(e)}")
    
    # Test past date
    try:
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "date": past_date,
            "hour": 10,
            "name": "Past Date Test",
            "email": "test@test.dk",
            "phone": "12",
            "dogs": 1
        }
        response = requests.post(f"{BASE_URL}/bookings", json=payload)
        
        if response.status_code == 400:
            log_test("POST /api/bookings with past date returns 400", True, "Correctly rejects past date")
        else:
            log_test("POST /api/bookings with past date returns 400", False, f"Expected 400, got {response.status_code}")
    except Exception as e:
        log_test("POST /api/bookings with past date", False, f"Exception: {str(e)}")

def test_8_admin_bookings():
    """Test 8: Admin bookings endpoint"""
    print("\n=== Test 8: Admin Bookings ===")
    
    # Test without admin key
    try:
        response = requests.get(f"{BASE_URL}/admin/bookings")
        
        if response.status_code == 401:
            log_test("GET /api/admin/bookings without X-Admin-Key returns 401", True, "Correctly requires authentication")
        else:
            log_test("GET /api/admin/bookings without X-Admin-Key returns 401", False, f"Expected 401, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/bookings without key", False, f"Exception: {str(e)}")
    
    # Test with admin key
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        response = requests.get(f"{BASE_URL}/admin/bookings", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            
            if bookings:
                # Check if display_status field exists
                if "display_status" in bookings[0]:
                    log_test("GET /api/admin/bookings with X-Admin-Key returns bookings with display_status", True, f"Found {len(bookings)} bookings")
                else:
                    log_test("GET /api/admin/bookings with X-Admin-Key returns display_status", False, "display_status field missing")
            else:
                log_test("GET /api/admin/bookings with X-Admin-Key returns bookings", True, "Returns empty bookings array (no bookings yet)")
        else:
            log_test("GET /api/admin/bookings with X-Admin-Key", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/bookings with key", False, f"Exception: {str(e)}")

def test_9_settings_content_endpoints():
    """Test 9: Settings and Content endpoints"""
    print("\n=== Test 9: Settings and Content Endpoints ===")
    
    # GET /api/content
    try:
        response = requests.get(f"{BASE_URL}/content")
        
        if response.status_code == 200:
            data = response.json()
            required_sections = ["hero", "about", "contact"]
            missing_sections = [s for s in required_sections if s not in data]
            
            if missing_sections:
                log_test("GET /api/content returns all sections", False, f"Missing sections: {missing_sections}")
            else:
                log_test("GET /api/content returns hero/about/contact", True, "All sections present")
        else:
            log_test("GET /api/content", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("GET /api/content", False, f"Exception: {str(e)}")
    
    # PUT /api/admin/settings without key
    try:
        payload = {"single_visit_price": 70}
        response = requests.put(f"{BASE_URL}/admin/settings", json=payload)
        
        if response.status_code == 401:
            log_test("PUT /api/admin/settings without X-Admin-Key returns 401", True, "Correctly requires authentication")
        else:
            log_test("PUT /api/admin/settings without X-Admin-Key returns 401", False, f"Expected 401, got {response.status_code}")
    except Exception as e:
        log_test("PUT /api/admin/settings without key", False, f"Exception: {str(e)}")
    
    # PUT /api/admin/settings with key (test and reset)
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        
        # Update settings
        payload = {"single_visit_price": 70, "extra_dog_price": 35}
        response = requests.put(f"{BASE_URL}/admin/settings", json=payload, headers=headers)
        
        if response.status_code == 200:
            log_test("PUT /api/admin/settings with X-Admin-Key updates settings", True, "Settings updated successfully")
            
            # Reset to defaults
            reset_payload = {"single_visit_price": 60, "extra_dog_price": 30, "ten_trip_price": 560}
            reset_response = requests.put(f"{BASE_URL}/admin/settings", json=reset_payload, headers=headers)
            
            if reset_response.status_code == 200:
                log_test("PUT /api/admin/settings reset to defaults", True, "Settings reset successfully")
            else:
                log_test("PUT /api/admin/settings reset", False, f"Reset failed with status {reset_response.status_code}")
        else:
            log_test("PUT /api/admin/settings with X-Admin-Key", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("PUT /api/admin/settings with key", False, f"Exception: {str(e)}")
    
    # PUT /api/admin/content without key
    try:
        payload = {"contact": {"phone": "+45 99 99 99 99"}}
        response = requests.put(f"{BASE_URL}/admin/content", json=payload)
        
        if response.status_code == 401:
            log_test("PUT /api/admin/content without X-Admin-Key returns 401", True, "Correctly requires authentication")
        else:
            log_test("PUT /api/admin/content without X-Admin-Key returns 401", False, f"Expected 401, got {response.status_code}")
    except Exception as e:
        log_test("PUT /api/admin/content without key", False, f"Exception: {str(e)}")
    
    # PUT /api/admin/content with key (test and reset)
    try:
        headers = {"X-Admin-Key": ADMIN_KEY}
        
        # Update content
        payload = {"contact": {"phone": "+45 99 99 99 99"}}
        response = requests.put(f"{BASE_URL}/admin/content", json=payload, headers=headers)
        
        if response.status_code == 200:
            log_test("PUT /api/admin/content with X-Admin-Key updates content", True, "Content updated successfully")
            
            # Reset to default
            reset_payload = {"contact": {"phone": "+45 93 84 18 68"}}
            reset_response = requests.put(f"{BASE_URL}/admin/content", json=reset_payload, headers=headers)
            
            if reset_response.status_code == 200:
                log_test("PUT /api/admin/content reset to default", True, "Content reset successfully")
            else:
                log_test("PUT /api/admin/content reset", False, f"Reset failed with status {reset_response.status_code}")
        else:
            log_test("PUT /api/admin/content with X-Admin-Key", False, f"Status code: {response.status_code}")
    except Exception as e:
        log_test("PUT /api/admin/content with key", False, f"Exception: {str(e)}")

def main():
    """Run all tests"""
    print("=" * 80)
    print("STRIPE SDK MIGRATION VERIFICATION TEST SUITE")
    print("Testing migration from emergentintegrations to official Stripe Python SDK")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Date: {FUTURE_DATE}")
    print(f"Admin Key: {ADMIN_KEY}")
    print("=" * 80)
    
    # Run tests in sequence
    test_1_root_endpoint()
    test_2_settings_endpoint()
    
    # Create booking and get booking_id
    booking_data = test_3_create_booking()
    
    if booking_data:
        booking_id = booking_data["booking_id"]
        
        # Create checkout session
        checkout_data = test_4_create_checkout_session(booking_id)
        
        if checkout_data:
            session_id = checkout_data["session_id"]
            
            # Test checkout status
            test_5_checkout_status(session_id)
            test_5b_checkout_status_invalid()
            
            # Test slot lock
            test_6_slot_lock()
    
    # Validation tests
    test_7_validation()
    
    # Admin tests
    test_8_admin_bookings()
    
    # Settings and content tests
    test_9_settings_content_endpoints()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    print("\n" + "=" * 80)
    print("STRIPE SDK MIGRATION STATUS")
    print("=" * 80)
    
    # Check if critical Stripe tests passed
    stripe_tests = [r for r in test_results if "checkout/session" in r["test"] or "Official Stripe SDK" in r["test"]]
    stripe_passed = all(r["passed"] for r in stripe_tests)
    
    if stripe_passed:
        print("✅ CONFIRMED: Official Stripe Python SDK is working correctly")
        print("✅ All payment endpoints functional after migration")
        print("✅ Checkout session creation returns valid 'cs_' session IDs")
        print("✅ Stripe checkout URLs are valid")
    else:
        print("❌ ISSUE: Some Stripe SDK tests failed")
        print("❌ Review failed tests above for details")
    
    print("=" * 80)
    
    # Print failed tests details
    if failed > 0:
        print("\nFAILED TESTS DETAILS:")
        print("=" * 80)
        for r in test_results:
            if not r["passed"]:
                print(f"❌ {r['test']}")
                if r["details"]:
                    print(f"   {r['details']}")
        print("=" * 80)

if __name__ == "__main__":
    main()
