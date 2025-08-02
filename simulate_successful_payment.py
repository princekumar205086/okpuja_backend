#!/usr/bin/env python
"""
Simulate successful payment and test booking creation
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append('.')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from payments.services import WebhookService

CART_ID = "44ae14e5-bf66-4ecc-8530-b2ad4ef064e7"

print(f"🧪 Simulating successful payment for cart: {CART_ID}")

try:
    # Get the payment
    payment = PaymentOrder.objects.filter(cart_id=CART_ID).first()
    if not payment:
        print(f"❌ No payment found for cart")
        exit(1)
        
    print(f"💳 Current payment status: {payment.status}")
    
    # Update payment status to SUCCESS
    payment.status = 'SUCCESS'
    payment.save()
    print(f"✅ Updated payment status to SUCCESS")
    
    # Now try to create booking using the webhook service
    webhook_service = WebhookService()
    booking = webhook_service._create_booking_from_cart(payment)
    
    if booking:
        print(f"✅ Booking created successfully!")
        print(f"🏷️  Booking ID: {booking.book_id}")
        print(f"📊 Booking Status: {booking.status}")
        print(f"📅 Selected Date: {booking.selected_date}")
        print(f"🕐 Selected Time: {booking.selected_time}")
        
        # Check cart status
        cart = Cart.objects.get(cart_id=CART_ID)
        print(f"🛒 Cart status after booking: {cart.status}")
    else:
        print(f"❌ Failed to create booking")
        
    print(f"\n🔄 Now testing the booking retrieval endpoint...")
    
    # Test the booking retrieval
    import requests
    BASE_URL = "http://127.0.0.1:8000/api"
    
    # Login first
    login_data = {"email": "asliprinceraj@gmail.com", "password": "testpass123"}
    login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if login_response.status_code == 200:
        access_token = login_response.json().get('access')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Try booking retrieval
        booking_response = requests.get(f"{BASE_URL}/booking/bookings/by-cart/{CART_ID}/", headers=headers)
        print(f"📊 Booking API Response: {booking_response.status_code}")
        
        if booking_response.status_code == 200:
            booking_result = booking_response.json()
            print(f"✅ Booking retrieved via API!")
            print(f"🏷️  API Booking ID: {booking_result.get('book_id')}")
        else:
            print(f"❌ API booking retrieval failed: {booking_response.json()}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
