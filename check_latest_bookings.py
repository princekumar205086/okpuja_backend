#!/usr/bin/env python
"""
Check the latest booking in database
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

print("🔍 Checking latest bookings in database...")

try:
    # Get latest 3 bookings
    bookings = Booking.objects.select_related('cart', 'user').order_by('-created_at')[:3]
    
    print(f"📋 Found {bookings.count()} bookings:")
    
    for booking in bookings:
        print(f"\n  Booking ID: {booking.book_id}")
        print(f"  User: {booking.user.email}")
        print(f"  Cart ID: {booking.cart.cart_id if booking.cart else 'None'}")
        print(f"  Status: {booking.status}")
        print(f"  Date: {booking.selected_date}")
        print(f"  Time: {booking.selected_time}")
        print(f"  Created: {booking.created_at}")
        
        # Check cart status
        if booking.cart:
            print(f"  Cart Status: {booking.cart.status}")
    
    # Check latest cart for our user
    print(f"\n🛒 Latest carts for user:")
    carts = Cart.objects.filter(user__email='asliprinceraj@gmail.com').order_by('-created_at')[:3]
    
    for cart in carts:
        print(f"\n  Cart ID: {cart.cart_id}")
        print(f"  Status: {cart.status}")
        print(f"  Created: {cart.created_at}")
        
        # Check if this cart has payments
        payments = PaymentOrder.objects.filter(cart_id=cart.cart_id)
        print(f"  Payments: {payments.count()}")
        for payment in payments:
            print(f"    - Order: {payment.merchant_order_id}")
            print(f"    - Status: {payment.status}")
        
        # Check if this cart has bookings
        bookings_for_cart = Booking.objects.filter(cart=cart)
        print(f"  Bookings: {bookings_for_cart.count()}")
        for booking in bookings_for_cart:
            print(f"    - Booking: {booking.book_id}")
            print(f"    - Status: {booking.status}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
