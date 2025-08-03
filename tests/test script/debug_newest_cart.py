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

def debug_newest_cart():
    print("🔍 DEBUGGING NEWEST CART ISSUE")
    print("="*60)
    
    # Your newest cart from Swagger
    newest_cart_id = 'd7a594ac-9333-4213-985f-67942a3b638b'
    old_cart_id = '33dd806a-6989-47f5-a840-e588a73e11eb'
    
    try:
        # Get user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(phone="+919876543210")
        
        print(f"👤 User: {user.phone} ({user.email})")
        
        # Check all user's carts ordered by creation time
        print(f"\n📦 ALL USER'S CARTS (newest first):")
        all_carts = Cart.objects.filter(user=user).order_by('-created_at')[:5]
        
        for i, cart in enumerate(all_carts, 1):
            payment = PaymentOrder.objects.filter(cart_id=cart.cart_id).first()
            booking = Booking.objects.filter(cart=cart).first()
            
            print(f"   {i}. Cart: {cart.cart_id[:8]}...")
            print(f"      Created: {cart.created_at}")
            print(f"      Status: {cart.status}")
            print(f"      Payment: {payment.status if payment else 'None'}")
            print(f"      Booking: {booking.book_id if booking else 'None'}")
            
            if cart.cart_id == newest_cart_id:
                print(f"      🆕 THIS IS THE NEWEST CART")
            elif cart.cart_id == old_cart_id:
                print(f"      🔄 THIS IS THE OLD SIMULATED CART")
            print()
        
        # Check what redirect handler would find
        print(f"🔗 WHAT REDIRECT HANDLER FINDS:")
        latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
        print(f"   Latest cart: {latest_cart.cart_id[:8]}...")
        print(f"   Created: {latest_cart.created_at}")
        print(f"   Status: {latest_cart.status}")
        
        if latest_cart.cart_id == newest_cart_id:
            print(f"   ✅ Redirect handler should find NEWEST cart")
        else:
            print(f"   ❌ Redirect handler finding WRONG cart!")
            
        # Check payment for newest cart
        print(f"\n💳 NEWEST CART PAYMENT STATUS:")
        newest_payment = PaymentOrder.objects.filter(cart_id=newest_cart_id).first()
        if newest_payment:
            print(f"   Order ID: {newest_payment.merchant_order_id}")
            print(f"   Status: {newest_payment.status}")
            print(f"   Amount: ₹{newest_payment.amount}")
            
            if newest_payment.status == 'INITIATED':
                print(f"   ⚠️ Payment still INITIATED - no webhook received!")
                print(f"   💡 This is why no booking was created for newest cart")
            
        else:
            print(f"   ❌ No payment found for newest cart")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_newest_cart()
