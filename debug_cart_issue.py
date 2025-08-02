#!/usr/bin/env python
import os
import django

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking

def check_new_cart_status():
    new_cart_id = '33dd806a-6989-47f5-a840-e588a73e11eb'
    old_cart_id = '5c4dad97-f37f-4afb-85e5-3d87075cf2ac'
    
    print("🔍 CART STATUS ANALYSIS")
    print("="*50)
    
    # Check new cart
    try:
        new_cart = Cart.objects.get(cart_id=new_cart_id)
        print(f"📦 NEW Cart: {new_cart.cart_id}")
        print(f"   Status: {new_cart.status}")
        print(f"   Created: {new_cart.created_at}")
        print(f"   User: {new_cart.user.phone}")
        
        # Check payment for new cart
        new_payment = PaymentOrder.objects.filter(cart_id=new_cart_id).first()
        if new_payment:
            print(f"   💳 Payment: {new_payment.merchant_order_id}")
            print(f"   Payment Status: {new_payment.status}")
        else:
            print(f"   💳 Payment: None")
        
        # Check booking for new cart
        new_booking = Booking.objects.filter(cart=new_cart).first()
        if new_booking:
            print(f"   📋 Booking: {new_booking.book_id}")
        else:
            print(f"   📋 Booking: None")
            
    except Cart.DoesNotExist:
        print(f"❌ NEW cart not found")
    
    print()
    
    # Check old cart
    try:
        old_cart = Cart.objects.get(cart_id=old_cart_id)
        print(f"📦 OLD Cart: {old_cart.cart_id}")
        print(f"   Status: {old_cart.status}")
        print(f"   Created: {old_cart.created_at}")
        print(f"   User: {old_cart.user.phone}")
        
        # Check payment for old cart
        old_payment = PaymentOrder.objects.filter(cart_id=old_cart_id).first()
        if old_payment:
            print(f"   💳 Payment: {old_payment.merchant_order_id}")
            print(f"   Payment Status: {old_payment.status}")
        else:
            print(f"   💳 Payment: None")
        
        # Check booking for old cart
        old_booking = Booking.objects.filter(cart=old_cart).first()
        if old_booking:
            print(f"   📋 Booking: {old_booking.book_id}")
        else:
            print(f"   📋 Booking: None")
            
    except Cart.DoesNotExist:
        print(f"❌ OLD cart not found")
    
    print()
    
    # Check latest cart for user
    try:
        user = new_cart.user
        latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
        print(f"🔄 LATEST Cart for user {user.phone}: {latest_cart.cart_id}")
        print(f"   Created: {latest_cart.created_at}")
        print(f"   Status: {latest_cart.status}")
        
        if latest_cart.cart_id == new_cart_id:
            print("   ✅ Latest cart matches NEW cart")
        elif latest_cart.cart_id == old_cart_id:
            print("   ⚠️ Latest cart is OLD cart - this explains the issue!")
        else:
            print("   ❓ Latest cart is different from both")
            
    except Exception as e:
        print(f"❌ Error checking latest cart: {e}")

if __name__ == "__main__":
    check_new_cart_status()
