#!/usr/bin/env python
"""
Debug the cart selection issue
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from payments.models import PaymentOrder
from accounts.models import User

print("🔍 Debugging Cart Selection Issue...")
print("=" * 50)

try:
    # Get user
    user = User.objects.get(email='asliprinceraj@gmail.com')
    print(f"User: {user.email} (ID: {user.id})")
    
    # Get all carts for this user ordered by creation time
    carts = Cart.objects.filter(user=user).order_by('-created_at')[:5]
    
    print(f"\n📋 Last 5 carts for user:")
    for i, cart in enumerate(carts, 1):
        print(f"  {i}. Cart ID: {cart.cart_id}")
        print(f"     Status: {cart.status}")
        print(f"     Created: {cart.created_at}")
        
        # Check payments for this cart
        payments = PaymentOrder.objects.filter(cart_id=cart.cart_id)
        print(f"     Payments: {payments.count()}")
        
        for payment in payments:
            print(f"       - Order: {payment.merchant_order_id}")
            print(f"       - Status: {payment.status}")
            print(f"       - Created: {payment.created_at}")
        print()
    
    # Check which cart the redirect handler would pick
    latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
    print(f"🎯 Latest cart that redirect handler would pick:")
    print(f"   Cart ID: {latest_cart.cart_id}")
    print(f"   Status: {latest_cart.status}")
    print(f"   Created: {latest_cart.created_at}")
    
    # Check if this cart has payment
    latest_payment = PaymentOrder.objects.filter(
        user=user,
        cart_id=latest_cart.cart_id
    ).order_by('-created_at').first()
    
    if latest_payment:
        print(f"   Payment: {latest_payment.merchant_order_id}")
        print(f"   Payment Status: {latest_payment.status}")
    else:
        print(f"   Payment: None")
    
    print(f"\n🎯 Expected cart ID: 3aef7e52-1f83-4067-8bdd-e6f00f6ab5b9")
    print(f"🎯 Actual latest cart ID: {latest_cart.cart_id}")
    
    if latest_cart.cart_id == "3aef7e52-1f83-4067-8bdd-e6f00f6ab5b9":
        print("✅ Cart IDs match!")
    else:
        print("❌ Cart IDs don't match!")
        
        # Check if the expected cart exists
        expected_cart = Cart.objects.filter(cart_id="3aef7e52-1f83-4067-8bdd-e6f00f6ab5b9").first()
        if expected_cart:
            print(f"   Expected cart created: {expected_cart.created_at}")
            print(f"   Latest cart created: {latest_cart.created_at}")
            
            if expected_cart.created_at > latest_cart.created_at:
                print("   Expected cart is newer - there's a database issue")
            else:
                print("   Latest cart is newer - expected cart is older")
        else:
            print("   Expected cart doesn't exist in database")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
