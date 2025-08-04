#!/usr/bin/env python
"""
Test script for Astrology Booking with Payment Integration
"""

import os
import sys
import django
import json
import requests
from datetime import date, time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from astrology.models import AstrologyService, AstrologyBooking
from payments.models import PaymentOrder

User = get_user_model()

BASE_URL = "http://localhost:8000"

def test_astrology_booking_with_payment():
    """Test the complete astrology booking with payment flow"""
    
    print("🔮 Testing Astrology Booking with Payment Integration")
    print("=" * 60)
    
    # 1. Check if we have an astrology service
    try:
        service = AstrologyService.objects.filter(is_active=True).first()
        if not service:
            print("❌ No active astrology service found. Creating one...")
            service = AstrologyService.objects.create(
                title="Gemstone Consultation",
                service_type="GEMSTONE",
                description="Professional gemstone recommendation based on your birth chart",
                price=1999.00,
                duration_minutes=60,
                is_active=True
            )
            print(f"✅ Created test service: {service.title}")
        else:
            print(f"✅ Found service: {service.title} - ₹{service.price}")
            
    except Exception as e:
        print(f"❌ Error setting up service: {e}")
        return False
    
    # 2. Check if we have a test user
    try:
        user = User.objects.filter(email="astrotest@example.com").first()
        if not user:
            print("❌ No test user found. Please run create_test_data.py first")
            return False
        else:
            print(f"✅ Found test user: {user.email}")
            
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return False
    
    # 3. Get authentication token
    print("\n📝 Getting authentication token...")
    try:
        auth_response = requests.post(f"{BASE_URL}/api/auth/login/", {
            "email": "astrotest@example.com",
            "password": "testpass123"
        })
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            token = auth_data.get('access_token') or auth_data.get('access')
            print("✅ Authentication successful")
            print(f"📊 Auth response: {auth_data}")
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(auth_response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return False
    
    # 4. Test astrology booking with payment
    print("\n💳 Testing astrology booking with payment...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    booking_data = {
        "service": service.id,
        "language": "Hindi",
        "preferred_date": "2025-08-10",
        "preferred_time": "10:00:00",
        "birth_place": "Delhi, India",
        "birth_date": "1995-05-15",
        "birth_time": "08:30:00",
        "gender": "MALE",
        "questions": "I want to know about career prospects and suitable gemstones for success.",
        "contact_email": "astrotest@example.com",
        "contact_phone": "9123456789",
        "redirect_url": "http://localhost:3000/payment-success"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/astrology/bookings/book-with-payment/",
            headers=headers,
            json=booking_data
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Booking with payment created successfully!")
            print(f"🎯 Booking ID: {data['data']['booking']['id']}")
            print(f"💰 Amount: ₹{data['data']['payment']['amount_in_rupees']}")
            print(f"🔗 Payment URL: {data['data']['payment']['payment_url'][:80]}...")
            print(f"📋 Merchant Order ID: {data['data']['payment']['merchant_order_id']}")
            
            # 5. Verify booking was created in database
            booking_id = data['data']['booking']['id']
            booking = AstrologyBooking.objects.get(id=booking_id)
            print(f"✅ Booking verified in database: Status = {booking.status}")
            
            # 6. Verify payment order was created
            merchant_order_id = data['data']['payment']['merchant_order_id']
            payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
            print(f"✅ Payment order verified: Status = {payment_order.status}")
            print(f"💾 Payment metadata: {payment_order.metadata}")
            
            return True
            
        else:
            print(f"❌ Booking creation failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error during booking creation: {e}")
        return False

def test_available_endpoints():
    """Test that the new endpoint is available"""
    print("\n🔗 Testing API endpoints availability...")
    
    endpoints_to_test = [
        "/api/astrology/services/",
        "/api/astrology/bookings/",
        "/api/astrology/bookings/book-with-payment/",
        "/api/payments/create/",
        "/api/docs/"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code in [200, 401, 405]:  # 405 for POST-only endpoints
                print(f"✅ {endpoint} - Available ({response.status_code})")
            else:
                print(f"❌ {endpoint} - Error ({response.status_code})")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Astrology Payment Integration Tests")
    print("=" * 60)
    
    # Test endpoint availability
    test_available_endpoints()
    
    # Test the main functionality
    success = test_astrology_booking_with_payment()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Astrology booking with payment integration is working!")
    else:
        print("💥 TESTS FAILED! Please check the errors above.")
    print("=" * 60)
