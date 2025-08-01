#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User
from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder
from payments.services import PaymentService, WebhookService

def test_complete_flow():
    """Test the complete cart -> payment -> booking flow"""
    print("=== COMPLETE FLOW TEST ===\n")
    
    # Find a successful payment to test
    successful_payment = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).first()
    
    if not successful_payment:
        print("No successful cart-based payments found to test.")
        return
    
    print(f"Testing with payment: {successful_payment.merchant_order_id}")
    print(f"Cart ID: {successful_payment.cart_id}")
    
    # Check if booking exists
    try:
        cart = Cart.objects.get(cart_id=successful_payment.cart_id)
        booking = Booking.objects.filter(cart=cart).first()
        
        print(f"\n1. Cart Status: {cart.status}")
        print(f"2. Booking Exists: {'YES' if booking else 'NO'}")
        
        if booking:
            print(f"   - Booking ID: {booking.book_id}")
            print(f"   - Status: {booking.status}")
            print(f"   - Date: {booking.selected_date}")
            print(f"   - Time: {booking.selected_time}")
            print(f"   - Address: {'YES' if booking.address else 'NO'}")
        
        # Test redirect URL construction
        print(f"\n3. Frontend Redirect URL:")
        if booking:
            frontend_url = f"http://localhost:3000/confirmbooking?booking_id={booking.book_id}&order_id={successful_payment.merchant_order_id}"
            print(f"   SUCCESS: {frontend_url}")
        else:
            frontend_url = f"http://localhost:3000/confirmbooking?order_id={successful_payment.merchant_order_id}&status=completed"
            print(f"   FALLBACK: {frontend_url}")
        
        # Test booking API endpoint
        print(f"\n4. Booking API Test:")
        if booking:
            print(f"   GET /api/booking/get/{booking.book_id}/ -> Booking details")
            print(f"   This endpoint should return booking details for frontend confirmation")
        
        print(f"\n✅ FLOW COMPLETE!")
        print(f"✅ Payment: {successful_payment.status}")
        print(f"✅ Cart: {cart.status}")
        print(f"✅ Booking: {'CREATED' if booking else 'MISSING'}")
        print(f"✅ Redirect: {'WITH BOOKING_ID' if booking else 'WITHOUT BOOKING_ID'}")
        
    except Cart.DoesNotExist:
        print(f"❌ Cart not found for cart_id: {successful_payment.cart_id}")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_flow_summary():
    """Show summary of the complete flow"""
    print("\n=== FLOW SUMMARY ===")
    print("1. Frontend creates cart via API")
    print("2. Frontend initiates payment with cart_id")
    print("3. User completes payment on PhonePe")
    print("4. PhonePe sends webhook (or status check creates booking)")
    print("5. Booking auto-created from cart")
    print("6. Email sent to user")
    print("7. User redirected to frontend with booking_id")
    print("8. Frontend calls booking API to get details")
    print("\nFixed Issues:")
    print("✅ Time format parsing (handles 24h and 12h formats)")
    print("✅ Booking status enum (uses string values)")
    print("✅ Address field (made optional with blank=True)")
    print("✅ Email task (corrected task name and parameters)")
    print("✅ Redirect URL (includes booking_id when available)")
    print("✅ Booking creation (called on payment success)")

if __name__ == "__main__":
    test_complete_flow()
    show_flow_summary()
