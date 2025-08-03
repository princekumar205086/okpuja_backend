#!/usr/bin/env python3
"""
Quick test to verify:
1. Cart cleanup is working (cart status changes to CONVERTED)
2. Payment details can be retrieved from bookings
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from accounts.models import User
from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder

def test_cart_cleanup_and_payment_details():
    print("🔍 TESTING CART CLEANUP & PAYMENT DETAILS")
    print("=" * 50)
    
    # Get test user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ Test user not found")
        return
    
    print(f"✅ User: {user.email}")
    
    # Check recent bookings with payment details
    recent_bookings = Booking.objects.filter(user=user).order_by('-created_at')[:3]
    
    for booking in recent_bookings:
        print(f"\n📋 Booking: {booking.book_id}")
        print(f"   Status: {booking.status}")
        print(f"   Cart Status: {booking.cart.status if booking.cart else 'No Cart'}")
        
        # Test payment details
        payment_details = booking.payment_details
        print(f"   Payment ID: {payment_details['payment_id']}")
        print(f"   Amount: ₹{payment_details['amount']}")
        print(f"   Payment Status: {payment_details['status']}")
        print(f"   Payment Method: {payment_details['payment_method']}")
        print(f"   Transaction ID: {payment_details['transaction_id']}")
        
        # Check if cart was properly cleaned up
        if booking.cart and booking.cart.status == 'CONVERTED':
            print("   ✅ Cart properly cleaned up (status: CONVERTED)")
        elif booking.cart:
            print(f"   ⚠️ Cart status: {booking.cart.status}")
        else:
            print("   ℹ️ No cart associated")
    
    # Check for any active carts that should have been converted
    active_carts = Cart.objects.filter(user=user, status='ACTIVE')
    print(f"\n🛒 Active carts: {active_carts.count()}")
    
    if active_carts.count() == 0:
        print("✅ Good: No lingering active carts")
    else:
        print("⚠️ Warning: There are still active carts after bookings")
        for cart in active_carts[:3]:
            print(f"   - Cart {cart.cart_id}: {cart.status}")
    
    print("\n" + "=" * 50)
    print("✅ TEST COMPLETE")

if __name__ == "__main__":
    test_cart_cleanup_and_payment_details()
