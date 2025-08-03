#!/usr/bin/env python3
"""
Simple test to check existing cart and booking flow for user: asliprinceraj@gmail.com
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User, Address
from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder

def test_existing_flow():
    """Test what currently exists for the user"""
    
    print("🔍 Testing Existing User Data")
    print("=" * 50)
    
    # 1. Find user
    try:
        user = User.objects.get(email='asliprinceraj@gmail.com')
        print(f"✅ User: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ User not found!")
        return
    
    # 2. Check user's addresses
    addresses = Address.objects.filter(user=user)
    print(f"\n📍 User has {addresses.count()} addresses:")
    for addr in addresses:
        default_str = " (DEFAULT)" if addr.is_default else ""
        print(f"   - ID: {addr.id} | {addr.address_line1}, {addr.city}{default_str}")
    
    # 3. Check user's carts
    carts = Cart.objects.filter(user=user)
    print(f"\n📦 User has {carts.count()} carts:")
    for cart in carts:
        addr_info = f" | Address: {cart.selected_address.city}" if cart.selected_address else " | No address"
        service_info = f" | Service: {cart.puja_service.title}" if cart.puja_service else " | No service"
        print(f"   - Cart {cart.id} ({cart.status}){service_info}{addr_info}")
    
    # 4. Check user's payments
    payments = PaymentOrder.objects.filter(user=user)
    print(f"\n💳 User has {payments.count()} payments:")
    for payment in payments[:5]:  # Show last 5
        addr_info = f" | Address ID: {payment.address_id}" if hasattr(payment, 'address_id') and payment.address_id else " | No address"
        print(f"   - Payment {payment.id} ({payment.status}) ₹{payment.amount}{addr_info}")
    
    # 5. Check user's bookings
    bookings = Booking.objects.filter(user=user)
    print(f"\n🏗️ User has {bookings.count()} bookings:")
    for booking in bookings[:5]:  # Show last 5
        addr_info = f" | Address: {booking.address.city}" if booking.address else " | No address"
        print(f"   - Booking {booking.id} ({booking.status}){addr_info}")
    
    # 6. Analysis
    print(f"\n🔍 FLOW ANALYSIS")
    print("-" * 30)
    
    # Find the most recent cart
    recent_cart = carts.filter(status='ACTIVE').first()
    if recent_cart:
        print(f"✅ Recent cart: {recent_cart.id}")
        print(f"   📍 Cart address: {recent_cart.selected_address.city if recent_cart.selected_address else 'MISSING!'}")
        
        # Check if this cart has payments
        related_payments = PaymentOrder.objects.filter(cart_id=recent_cart.cart_id)
        print(f"   💳 Related payments: {related_payments.count()}")
        
        # Check if this cart has bookings
        related_bookings = Booking.objects.filter(cart=recent_cart)
        print(f"   🏗️ Related bookings: {related_bookings.count()}")
        
        # Specific address issue analysis
        if not recent_cart.selected_address:
            print("   ❌ ISSUE: Cart has no selected address!")
        else:
            print("   ✅ Cart has address selected")
            
        for payment in related_payments:
            if hasattr(payment, 'address_id'):
                if payment.address_id:
                    print(f"   ✅ Payment {payment.id} has address_id: {payment.address_id}")
                else:
                    print(f"   ❌ Payment {payment.id} missing address_id")
            else:
                print(f"   ❌ Payment {payment.id} has no address_id field")
                
        for booking in related_bookings:
            if booking.address:
                print(f"   ✅ Booking {booking.id} has address: {booking.address.city}")
            else:
                print(f"   ❌ Booking {booking.id} missing address")
    else:
        print("❌ No active cart found")

if __name__ == "__main__":
    test_existing_flow()
