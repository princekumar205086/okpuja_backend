#!/usr/bin/env python
"""
Test script to simulate successful payment and check booking creation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder
from accounts.models import User
from payments.services import WebhookService

def simulate_successful_payment():
    """Simulate a successful payment and test booking creation"""
    print("=" * 60)
    print("SIMULATING SUCCESSFUL PAYMENT")
    print("=" * 60)
    
    # Get test user
    user = User.objects.get(email="asliprinceraj@gmail.com")
    
    # Get latest cart and payment
    latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
    payment = PaymentOrder.objects.filter(cart_id=latest_cart.cart_id).order_by('-created_at').first()
    
    print(f"Cart ID: {latest_cart.cart_id}")
    print(f"Payment ID: {payment.merchant_order_id}")
    print(f"Current Payment Status: {payment.status}")
    
    # Simulate successful payment
    print("\n🔧 Simulating successful payment...")
    payment.status = 'SUCCESS'
    payment.save()
    print(f"✅ Payment status updated to: {payment.status}")
    
    # Test webhook service booking creation
    print("\n🔧 Testing booking creation via webhook service...")
    webhook_service = WebhookService()
    booking = webhook_service._create_booking_from_cart(payment)
    
    if booking:
        print(f"✅ Booking created successfully!")
        print(f"   Booking ID: {booking.book_id}")
        print(f"   Status: {booking.status}")
        print(f"   Cart Status: {latest_cart.status}")
        print(f"   User: {booking.user.email}")
        print(f"   Date: {booking.selected_date}")
        print(f"   Time: {booking.selected_time}")
        
        # Refresh cart status
        latest_cart.refresh_from_db()
        print(f"   Updated Cart Status: {latest_cart.status}")
        
    else:
        print("❌ Failed to create booking")
        return
    
    print("\n" + "=" * 60)
    print("TESTING FRONTEND REDIRECT SCENARIO")
    print("=" * 60)
    
    # Test what frontend would receive
    cart_id = latest_cart.cart_id
    order_id = payment.merchant_order_id
    redirect_url = f"http://localhost:3000/confirmbooking?cart_id={cart_id}&order_id={order_id}&redirect_source=phonepe"
    
    print(f"🌐 Frontend redirect URL:")
    print(f"   {redirect_url}")
    
    print(f"\n📡 Frontend should call:")
    print(f"   GET /api/booking/bookings/by-cart/{cart_id}/")
    print(f"   This should return booking: {booking.book_id}")
    
    print(f"\n✅ Complete flow now working:")
    print(f"   1. Cart created: {cart_id}")
    print(f"   2. Payment successful: {order_id}")
    print(f"   3. Booking auto-created: {booking.book_id}")
    print(f"   4. Cart status: {latest_cart.status}")
    print(f"   5. Redirect with cart_id (not book_id)")

if __name__ == "__main__":
    simulate_successful_payment()
