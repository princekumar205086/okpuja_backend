#!/usr/bin/env python
"""
Check database records for the cart
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

CART_ID = "44ae14e5-bf66-4ecc-8530-b2ad4ef064e7"

print(f"🔍 Checking database records for cart: {CART_ID}")

try:
    # Check cart
    cart = Cart.objects.filter(cart_id=CART_ID).first()
    if cart:
        print(f"✅ Cart found: ID={cart.id}, Status={cart.status}, User={cart.user.email}")
    else:
        print(f"❌ Cart not found")
        
    # Check payments for this cart
    payments = PaymentOrder.objects.filter(cart_id=CART_ID).order_by('-created_at')
    print(f"💳 Found {payments.count()} payments for this cart:")
    
    for payment in payments:
        print(f"  - Order ID: {payment.merchant_order_id}")
        print(f"  - Status: {payment.status}")
        print(f"  - Amount: {payment.amount}")
        print(f"  - Created: {payment.created_at}")
        print(f"  - User: {payment.user.email if payment.user else 'None'}")
        print()
        
    # Check bookings for this cart  
    if cart:
        bookings = Booking.objects.filter(cart=cart)
        print(f"📋 Found {bookings.count()} bookings for this cart:")
        
        for booking in bookings:
            print(f"  - Booking ID: {booking.book_id}")
            print(f"  - Status: {booking.status}")
            print(f"  - Created: {booking.created_at}")
            print()
    
except Exception as e:
    print(f"❌ Error: {e}")
