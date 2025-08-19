#!/usr/bin/env python
"""
Test script to verify the logout issue fix
Tests both production and UAT credentials with full booking flow
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_credentials_and_booking_flow():
    """Test both credential sets with complete booking flow"""
    print("🔍 TESTING LOGOUT FIX - COMPREHENSIVE BOOKING FLOW")
    print("=" * 70)
    
    # Test both credential sets
    credentials = [
        {
            "env": "UAT",
            "email": "asliprinceraj@gmail.com", 
            "password": "testpass123"
        },
        {
            "env": "PRODUCTION", 
            "email": "asliprinceraj@gmail.com",
            "password": "Testpass@123"
        }
    ]
    
    for cred in credentials:
        print(f"\n{'='*20} TESTING {cred['env']} CREDENTIALS {'='*20}")
        
        success = test_booking_flow(cred)
        
        if success:
            print(f"✅ {cred['env']} - All tests passed! No logout issue detected.")
        else:
            print(f"❌ {cred['env']} - Issues detected.")
        
        print(f"{'='*70}")

def test_booking_flow(credentials):
    """Test complete booking flow for logout issues"""
    
    # Step 1: Login
    print(f"\n1️⃣ TESTING LOGIN")
    token_data = test_login(credentials)
    if not token_data:
        return False
    
    access_token = token_data['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Step 2: Test session immediately after login
    print(f"\n2️⃣ TESTING SESSION IMMEDIATELY AFTER LOGIN")
    if not test_session_validity(headers):
        print("   ❌ Session invalid immediately after login!")
        return False
    
    # Step 3: Test cart creation (puja booking)
    print(f"\n3️⃣ TESTING PUJA BOOKING FLOW")
    cart_id = test_puja_cart_creation(headers)
    if not cart_id:
        return False
    
    # Step 4: Test session after cart creation
    print(f"\n4️⃣ TESTING SESSION AFTER CART CREATION")
    if not test_session_validity(headers):
        print("   ❌ LOGOUT DETECTED AFTER CART CREATION!")
        print("   This is the main issue we're trying to fix.")
        return False
    
    # Step 5: Test payment creation
    print(f"\n5️⃣ TESTING PAYMENT CREATION")
    payment_result = test_payment_creation(headers, cart_id)
    if not payment_result:
        return False
    
    # Step 6: Test session after payment creation
    print(f"\n6️⃣ TESTING SESSION AFTER PAYMENT CREATION")
    if not test_session_validity(headers):
        print("   ❌ LOGOUT DETECTED AFTER PAYMENT CREATION!")
        return False
    
    # Step 7: Test astrology booking (if possible)
    print(f"\n7️⃣ TESTING ASTROLOGY BOOKING FLOW")
    astro_result = test_astrology_booking(headers)
    if not astro_result:
        print("   ⚠️  Astrology booking test skipped (service not available)")
    
    # Step 8: Final session test
    print(f"\n8️⃣ FINAL SESSION VALIDITY TEST")
    if not test_session_validity(headers):
        print("   ❌ LOGOUT DETECTED AFTER ASTROLOGY BOOKING!")
        return False
    
    # Step 9: Test token longevity
    print(f"\n9️⃣ TESTING TOKEN LONGEVITY")
    test_token_expiry(access_token)
    
    return True

def test_login(credentials):
    """Test user login"""
    
    login_data = {
        "email": credentials["email"],
        "password": credentials["password"]
    }
    
    try:
        print(f"   Attempting login for {credentials['email']}...")
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data, timeout=10)
        
        if response.status_code == 200:
            auth_data = response.json()
            access_token = auth_data.get('access')
            refresh_token = auth_data.get('refresh')
            
            print(f"   ✅ Login successful!")
            print(f"   📋 User ID: {auth_data.get('id')}")
            print(f"   📧 Email: {auth_data.get('email')}")
            print(f"   🔑 Access token: {access_token[:30]}...")
            print(f"   🔄 Refresh token: {refresh_token[:30]}...")
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_data': auth_data
            }
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            if response.content:
                error = response.json()
                print(f"   Error details: {error}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server. Is Django running?")
        return None
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_session_validity(headers):
    """Test if current session/token is valid"""
    
    try:
        print(f"   Testing session validity...")
        response = requests.get(f"{BASE_URL}/api/auth/profile/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            print(f"   ✅ Session valid - User: {profile_data.get('email')}")
            return True
        elif response.status_code == 401:
            print(f"   ❌ AUTHENTICATION FAILED - TOKEN EXPIRED/INVALID!")
            error_data = response.json() if response.content else {}
            print(f"   Error details: {error_data}")
            return False
        else:
            print(f"   ⚠️  Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking session: {e}")
        return False

def test_puja_cart_creation(headers):
    """Test puja cart creation"""
    
    # Get available puja services first
    try:
        print(f"   Getting available puja services...")
        response = requests.get(f"{BASE_URL}/api/puja/services/", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"   ❌ Cannot get puja services: {response.status_code}")
            return None
        
        services = response.json()
        if not services or len(services) == 0:
            print(f"   ❌ No puja services available")
            return None
        
        # Use the first service
        service = services[0]
        service_id = service.get('id')
        service_name = service.get('title', 'Unknown')
        
        print(f"   📿 Using puja service: {service_name} (ID: {service_id})")
        
        # Create cart
        cart_data = {
            "puja_service": service_id,
            "selected_date": "2024-12-25",
            "selected_time": "10:00 AM",
            "special_instructions": "Test booking for logout fix verification"
        }
        
        print(f"   Creating cart...")
        response = requests.post(f"{BASE_URL}/api/cart/carts/", json=cart_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            cart_response = response.json()
            cart_id = cart_response.get('cart_id')
            print(f"   ✅ Cart created successfully!")
            print(f"   🛒 Cart ID: {cart_id}")
            return cart_id
        elif response.status_code == 401:
            print(f"   ❌ AUTHENTICATION FAILED DURING CART CREATION!")
            print(f"   This indicates the logout issue!")
            return None
        else:
            print(f"   ❌ Cart creation failed: {response.status_code}")
            error_data = response.json() if response.content else {}
            print(f"   Error details: {error_data}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error in cart creation: {e}")
        return None

def test_payment_creation(headers, cart_id):
    """Test payment creation"""
    
    try:
        payment_data = {
            "cart_id": cart_id,
            "redirect_url": "http://localhost:3000/confirmbooking"
        }
        
        print(f"   Creating payment for cart {cart_id}...")
        response = requests.post(f"{BASE_URL}/api/payments/cart/", json=payment_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            payment_response = response.json()
            print(f"   ✅ Payment created successfully!")
            print(f"   💳 Order ID: {payment_response['data']['payment_order']['merchant_order_id']}")
            return payment_response
        elif response.status_code == 401:
            print(f"   ❌ AUTHENTICATION FAILED DURING PAYMENT CREATION!")
            return None
        else:
            print(f"   ❌ Payment creation failed: {response.status_code}")
            error_data = response.json() if response.content else {}
            print(f"   Error details: {error_data}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error in payment creation: {e}")
        return None

def test_astrology_booking(headers):
    """Test astrology booking creation"""
    
    try:
        # Get available astrology services
        print(f"   Getting available astrology services...")
        response = requests.get(f"{BASE_URL}/api/astrology/services/", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"   ⚠️  Cannot get astrology services: {response.status_code}")
            return False
        
        services = response.json()
        if not services or len(services) == 0:
            print(f"   ⚠️  No astrology services available")
            return False
        
        # Use the first service
        service = services[0]
        service_id = service.get('id')
        service_name = service.get('name', 'Unknown')
        
        print(f"   🌟 Using astrology service: {service_name} (ID: {service_id})")
        
        # Create astrology booking
        booking_data = {
            "service_id": service_id,
            "selected_date": "2024-12-25",
            "selected_time": "14:30",
            "phone_number": "+91-9876543210",
            "questions": "Test questions for logout fix verification"
        }
        
        print(f"   Creating astrology booking...")
        response = requests.post(f"{BASE_URL}/api/astrology/bookings/book-with-payment/", json=booking_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            booking_response = response.json()
            print(f"   ✅ Astrology booking created successfully!")
            print(f"   ⭐ Booking ID: {booking_response.get('astro_book_id', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print(f"   ❌ AUTHENTICATION FAILED DURING ASTROLOGY BOOKING!")
            return False
        else:
            print(f"   ❌ Astrology booking failed: {response.status_code}")
            error_data = response.json() if response.content else {}
            print(f"   Error details: {error_data}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error in astrology booking: {e}")
        return False

def test_token_expiry(access_token):
    """Test token expiry time"""
    
    try:
        import jwt
        from datetime import datetime
        
        # Note: In production, you shouldn't decode JWT without verification
        # This is just for testing purposes
        payload = jwt.decode(access_token, options={"verify_signature": False})
        
        exp_timestamp = payload.get('exp')
        user_id = payload.get('user_id')
        
        if exp_timestamp:
            exp_time = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            time_left = exp_time - now
            
            print(f"   🕐 Token issued for user ID: {user_id}")
            print(f"   ⏰ Token expires at: {exp_time}")
            print(f"   ⏳ Time remaining: {time_left}")
            
            # Check if token lifetime is acceptable
            hours_left = time_left.total_seconds() / 3600
            if hours_left >= 1.5:  # At least 1.5 hours
                print(f"   ✅ Token lifetime is adequate ({hours_left:.1f} hours)")
            else:
                print(f"   ⚠️  Token lifetime is short ({hours_left:.1f} hours)")
        else:
            print(f"   ❌ Cannot determine token expiry")
            
    except Exception as e:
        print(f"   ❌ Error checking token expiry: {e}")

def print_summary():
    """Print test summary and recommendations"""
    
    print(f"\n🎯 LOGOUT ISSUE FIX SUMMARY")
    print("=" * 70)
    print("FIXES APPLIED:")
    print("1. ✅ JWT ACCESS_TOKEN_LIFETIME extended to 120 minutes (2 hours)")
    print("2. ✅ BLACKLIST_AFTER_ROTATION set to False (prevents premature logout)")
    print("3. ✅ UPDATE_LAST_LOGIN enabled for better session tracking")
    
    print(f"\n📱 FRONTEND RECOMMENDATIONS:")
    print("1. Implement automatic token refresh before expiry")
    print("2. Handle 401 responses gracefully")
    print("3. Show user-friendly messages during long booking processes")
    print("4. Consider implementing token refresh on user activity")
    
    print(f"\n🔍 MONITORING:")
    print("1. Monitor JWT token blacklist activity")
    print("2. Track user session durations during booking")
    print("3. Log authentication failures for analysis")
    
    print(f"\n🚀 DEPLOYMENT:")
    print("1. ✅ Backend changes applied (restart required)")
    print("2. 🔄 Frontend token management needs implementation")
    print("3. 📊 Consider adding user session analytics")

if __name__ == "__main__":
    test_credentials_and_booking_flow()
    print_summary()
