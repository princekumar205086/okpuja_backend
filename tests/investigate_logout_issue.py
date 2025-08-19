#!/usr/bin/env python
"""
Test script to investigate the logout issue during first-time booking
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder
from astrology.models import AstrologyBooking, AstrologyService
from accounts.models import Address

User = get_user_model()

def investigate_logout_issue():
    """Investigate why users get logged out during first-time booking"""
    print("🔍 INVESTIGATING LOGOUT ISSUE DURING FIRST-TIME BOOKING")
    print("=" * 70)
    
    # Test URLs
    BASE_URL = "http://127.0.0.1:8000"
    
    # Test credentials for both environments
    test_credentials = [
        {"env": "production", "email": "asliprinceraj@gmail.com", "password": "Testpass@123"},
        {"env": "uat", "email": "asliprinceraj@gmail.com", "password": "testpass123"}
    ]
    
    for cred in test_credentials:
        print(f"\n🧪 Testing {cred['env'].upper()} credentials...")
        
        # Step 1: Test login
        print(f"\n1️⃣ Testing login with {cred['env']} credentials")
        login_data = {
            "email": cred["email"],
            "password": cred["password"]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
            
            if response.status_code == 200:
                auth_data = response.json()
                access_token = auth_data['access']
                print(f"✅ Login successful for {cred['env']}")
                print(f"   Access token: {access_token[:50]}...")
                
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Step 2: Check existing bookings
                print(f"\n2️⃣ Checking existing bookings...")
                user = User.objects.filter(email=cred["email"]).first()
                if user:
                    puja_bookings = Booking.objects.filter(user=user).count()
                    astro_bookings = AstrologyBooking.objects.filter(user=user).count()
                    print(f"   Existing puja bookings: {puja_bookings}")
                    print(f"   Existing astrology bookings: {astro_bookings}")
                    
                    # Check if this would be a first-time booking
                    is_first_time = (puja_bookings == 0 and astro_bookings == 0)
                    print(f"   Is first-time user: {is_first_time}")
                    
                    # Step 3: Test cart creation (puja booking flow)
                    print(f"\n3️⃣ Testing puja booking flow...")
                    test_cart_creation(headers, user, is_first_time)
                    
                    # Step 4: Test astrology booking flow
                    print(f"\n4️⃣ Testing astrology booking flow...")
                    test_astrology_booking(headers, user, is_first_time)
                
                break  # Use the first working credential
            else:
                print(f"❌ Login failed for {cred['env']}: {response.status_code}")
                if response.content:
                    print(f"   Error: {response.json()}")
        
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to server at {BASE_URL}")
            continue
        except Exception as e:
            print(f"❌ Error testing {cred['env']}: {e}")
            continue

def test_cart_creation(headers, user, is_first_time):
    """Test cart creation and payment flow"""
    BASE_URL = "http://127.0.0.1:8000"
    
    try:
        # Create a test cart for puja booking
        from puja.models import PujaService
        puja_service = PujaService.objects.first()
        
        if not puja_service:
            print("   ⚠️ No puja services found - skipping puja test")
            return
            
        cart_data = {
            "puja_service": puja_service.id,
            "selected_date": "2024-12-25",
            "selected_time": "10:00 AM",
            "special_instructions": "Test booking for logout investigation"
        }
        
        print(f"   Creating cart for puja service: {puja_service.title}")
        response = requests.post(f"{BASE_URL}/api/cart/carts/", json=cart_data, headers=headers)
        
        if response.status_code == 201:
            cart_response = response.json()
            cart_id = cart_response['cart_id']
            print(f"   ✅ Cart created: {cart_id}")
            
            # Test payment creation
            payment_data = {
                "cart_id": cart_id,
                "redirect_url": "http://localhost:3000/confirmbooking"
            }
            
            response = requests.post(f"{BASE_URL}/api/payments/cart/", json=payment_data, headers=headers)
            
            if response.status_code == 201:
                payment_response = response.json()
                print(f"   ✅ Payment order created: {payment_response['data']['payment_order']['merchant_order_id']}")
                
                # Check if user session is still valid after payment creation
                test_session_validity(headers)
                
                # Simulate booking creation (what happens after successful payment)
                simulate_successful_payment_webhook(payment_response['data']['payment_order']['merchant_order_id'], user, is_first_time)
                
            else:
                print(f"   ❌ Payment creation failed: {response.status_code}")
                print(f"       {response.json()}")
        else:
            print(f"   ❌ Cart creation failed: {response.status_code}")
            if response.content:
                print(f"       {response.json()}")
                
    except Exception as e:
        print(f"   ❌ Error in cart creation test: {e}")

def test_astrology_booking(headers, user, is_first_time):
    """Test astrology booking flow"""
    BASE_URL = "http://127.0.0.1:8000"
    
    try:
        # Get astrology services
        astro_service = AstrologyService.objects.first()
        
        if not astro_service:
            print("   ⚠️ No astrology services found - skipping astrology test")
            return
            
        # Create astrology booking data
        booking_data = {
            "service_id": astro_service.id,
            "selected_date": "2024-12-25",
            "selected_time": "14:30",
            "phone_number": "+91-9876543210",
            "questions": "Test questions for logout investigation"
        }
        
        print(f"   Creating astrology booking for service: {astro_service.name}")
        response = requests.post(f"{BASE_URL}/api/astrology/bookings/book-with-payment/", json=booking_data, headers=headers)
        
        if response.status_code == 201:
            booking_response = response.json()
            print(f"   ✅ Astrology booking created: {booking_response}")
            
            # Check if user session is still valid after booking creation
            test_session_validity(headers)
            
        else:
            print(f"   ❌ Astrology booking failed: {response.status_code}")
            if response.content:
                print(f"       {response.json()}")
                
    except Exception as e:
        print(f"   ❌ Error in astrology booking test: {e}")

def test_session_validity(headers):
    """Test if the user session is still valid"""
    BASE_URL = "http://127.0.0.1:8000"
    
    try:
        # Try to access a protected endpoint
        response = requests.get(f"{BASE_URL}/api/auth/profile/", headers=headers)
        
        if response.status_code == 200:
            profile_data = response.json()
            print(f"   ✅ Session valid - User: {profile_data['email']}")
        elif response.status_code == 401:
            print(f"   ❌ SESSION EXPIRED/INVALID - This is the logout issue!")
            print(f"       Response: {response.json() if response.content else 'No content'}")
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing session validity: {e}")

def simulate_successful_payment_webhook(merchant_order_id, user, is_first_time):
    """Simulate what happens when payment webhook creates booking"""
    print(f"   📞 Simulating webhook for order: {merchant_order_id}")
    
    try:
        # Get the payment order
        payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
        
        # Simulate webhook service creating booking
        from payments.services import WebhookService
        webhook_service = WebhookService()
        
        if payment_order.cart_id:
            # This is a puja booking
            booking = webhook_service._create_booking_from_cart(payment_order)
            if booking:
                print(f"   ✅ Puja booking created via webhook: {booking.book_id}")
                
                # Check if this affects user session somehow
                print(f"   📊 First-time booking: {is_first_time}")
                
                # Check if email sending affects anything
                try:
                    from core.tasks import send_booking_confirmation
                    print(f"   📧 Email notification would be sent for booking {booking.book_id}")
                except Exception as e:
                    print(f"   ⚠️ Email notification issue: {e}")
                    
            else:
                print(f"   ❌ Failed to create booking from webhook")
                
    except PaymentOrder.DoesNotExist:
        print(f"   ❌ Payment order not found: {merchant_order_id}")
    except Exception as e:
        print(f"   ❌ Error in webhook simulation: {e}")

def check_jwt_blacklist():
    """Check if JWT tokens are being blacklisted unexpectedly"""
    print(f"\n🔒 CHECKING JWT TOKEN BLACKLISTING...")
    
    try:
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        
        # Get recent blacklisted tokens
        recent_blacklisted = BlacklistedToken.objects.all().order_by('-id')[:5]
        
        print(f"Recent blacklisted tokens ({recent_blacklisted.count()}):")
        for token in recent_blacklisted:
            print(f"   - Token ID: {token.token.id}, Created: {token.token.created_at}")
            
        # Check outstanding tokens
        recent_outstanding = OutstandingToken.objects.all().order_by('-id')[:5]
        print(f"\nRecent outstanding tokens ({recent_outstanding.count()}):")
        for token in recent_outstanding:
            print(f"   - User: {token.user.email if token.user else 'None'}, Created: {token.created_at}")
            
    except Exception as e:
        print(f"   ❌ Error checking JWT blacklist: {e}")

def check_middleware_and_signals():
    """Check if any middleware or signals might be causing logout"""
    print(f"\n⚙️ CHECKING MIDDLEWARE AND SIGNALS...")
    
    from django.conf import settings
    
    print("Current middleware:")
    for middleware in settings.MIDDLEWARE:
        print(f"   - {middleware}")
    
    # Check for any custom signals that might affect authentication
    print(f"\nChecking for authentication-related signals...")
    
    # Look for signal handlers in the apps
    try:
        import importlib
        from django.apps import apps
        
        for app_config in apps.get_app_configs():
            try:
                # Try to import signals module
                signals_module = importlib.import_module(f'{app_config.name}.signals')
                print(f"   Found signals in {app_config.name}")
            except ImportError:
                pass
                
    except Exception as e:
        print(f"   ❌ Error checking signals: {e}")

if __name__ == "__main__":
    investigate_logout_issue()
    check_jwt_blacklist()
    check_middleware_and_signals()
    
    print(f"\n" + "=" * 70)
    print("🏁 INVESTIGATION COMPLETE")
    print("Look for session validity issues above to identify the logout cause.")
