#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def debug_current_redirect_issue():
    """Debug why redirect handler is returning old booking for new cart"""
    print("=== 🔍 DEBUGGING CURRENT REDIRECT HANDLER ISSUE ===\n")
    
    from booking.models import Booking
    from accounts.models import User
    from cart.models import Cart
    from payments.models import PaymentOrder
    import pytz
    
    # Get the user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found!")
        return
    
    print(f"👤 User: {user.email} (ID: {user.id})")
    
    # Get the NEWEST cart from your Swagger test
    latest_cart_id = "ee52ccd4-31ca-4f4d-b436-33b649c1ef49"
    latest_cart = Cart.objects.filter(cart_id=latest_cart_id).first()
    
    print(f"\n🛒 SWAGGER TEST CART:")
    if latest_cart:
        print(f"   ID: {latest_cart.cart_id}")
        print(f"   User: {latest_cart.user.email} (ID: {latest_cart.user.id})")
        print(f"   Status: {latest_cart.status}")
        print(f"   Service: {latest_cart.puja_service.title}")
        print(f"   Created: {latest_cart.created_at}")
        
        # Check if this is actually the latest for this user
        user_latest = Cart.objects.filter(user=user).order_by('-created_at').first()
        if user_latest and user_latest.cart_id == latest_cart_id:
            print(f"   ✅ This IS the latest cart for user")
        else:
            print(f"   ❌ This is NOT the latest cart for user!")
            if user_latest:
                print(f"   User's actual latest: {user_latest.cart_id}")
                print(f"   Created: {user_latest.created_at}")
    else:
        print(f"   ❌ Cart {latest_cart_id} not found!")
        return
    
    # Get payment for this cart
    payment = PaymentOrder.objects.filter(cart_id=latest_cart_id).order_by('-created_at').first()
    
    print(f"\n💳 PAYMENT FOR SWAGGER CART:")
    if payment:
        print(f"   Order ID: {payment.merchant_order_id}")
        print(f"   Status: {payment.status}")
        print(f"   User: {payment.user.email} (ID: {payment.user.id})")
        print(f"   Cart ID: {payment.cart_id}")
        print(f"   Created: {payment.created_at}")
    else:
        print(f"   ❌ No payment found for cart {latest_cart_id}")
    
    # Check if booking exists for this cart
    booking = Booking.objects.filter(cart=latest_cart).first()
    
    print(f"\n📋 BOOKING FOR SWAGGER CART:")
    if booking:
        print(f"   ID: {booking.book_id}")
        print(f"   Status: {booking.status}")
        print(f"   User: {booking.user.email} (ID: {booking.user.id})")
        print(f"   Cart ID: {booking.cart.cart_id}")
        print(f"   Created: {booking.created_at}")
    else:
        print(f"   ❌ No booking found for cart {latest_cart_id}")
    
    # Show what the redirect handler logic would do
    print(f"\n🔄 REDIRECT HANDLER SIMULATION:")
    
    # Find user's latest cart (what redirect handler does)
    user_latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
    
    print(f"   1. User's latest cart: {user_latest_cart.cart_id if user_latest_cart else 'None'}")
    
    if user_latest_cart:
        print(f"      Status: {user_latest_cart.status}")
        print(f"      Service: {user_latest_cart.puja_service.title}")
        print(f"      Created: {user_latest_cart.created_at}")
        
        # Check if it's the expected cart
        if user_latest_cart.cart_id == latest_cart_id:
            print(f"   ✅ Would find CORRECT cart")
        else:
            print(f"   ❌ Would find WRONG cart!")
            print(f"      Expected: {latest_cart_id}")
            print(f"      Found: {user_latest_cart.cart_id}")
        
        # Check payment for user's latest cart
        user_payment = PaymentOrder.objects.filter(
            cart_id=user_latest_cart.cart_id, 
            status='SUCCESS'
        ).order_by('-created_at').first()
        
        print(f"   2. SUCCESS payment for latest cart: {'Yes' if user_payment else 'No'}")
        
        if not user_payment:
            # Check any payment
            any_payment = PaymentOrder.objects.filter(
                cart_id=user_latest_cart.cart_id
            ).order_by('-created_at').first()
            if any_payment:
                print(f"      But found payment with status: {any_payment.status}")
        
        # Check existing booking for user's latest cart
        user_booking = Booking.objects.filter(cart=user_latest_cart).first()
        print(f"   3. Existing booking for latest cart: {user_booking.book_id if user_booking else 'None'}")
        
        if user_booking:
            print(f"   ✅ Redirect would return booking: {user_booking.book_id}")
            # Check if this is the old booking causing the issue
            if user_booking.book_id == 'BK-9DCB7B55':
                print(f"   ⚠️  THIS IS THE OLD BOOKING CAUSING THE ISSUE!")
        else:
            print(f"   ⚠️  Redirect would try to create new booking")
    
    # Show recent carts for this user
    print(f"\n📦 USER'S RECENT CARTS:")
    user_carts = Cart.objects.filter(user=user).order_by('-created_at')[:5]
    
    for i, cart in enumerate(user_carts, 1):
        is_swagger_cart = "🎯" if cart.cart_id == latest_cart_id else "  "
        print(f"   {i}. {is_swagger_cart} {cart.cart_id[:8]}... ({cart.status}) - {cart.created_at}")
        
        # Check if has payment
        cart_payment = PaymentOrder.objects.filter(cart_id=cart.cart_id).first()
        if cart_payment:
            print(f"        └── Payment: {cart_payment.status}")
        
        # Check if has booking
        cart_booking = Booking.objects.filter(cart=cart).first()
        if cart_booking:
            print(f"        └── Booking: {cart_booking.book_id}")
    
    print(f"\n🔧 ANALYSIS:")
    print(f"   The issue is likely that:")
    print(f"   1. Payment status is not SUCCESS yet (webhook delay)")
    print(f"   2. OR redirect handler is finding wrong cart")
    print(f"   3. OR existing booking logic is returning old booking")

if __name__ == "__main__":
    debug_current_redirect_issue()
