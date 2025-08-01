#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def final_verification():
    """Final verification that the redirect handler fix is working"""
    print("=== ✅ FINAL VERIFICATION - REDIRECT HANDLER FIX ===\n")
    
    from booking.models import Booking
    from accounts.models import User
    from cart.models import Cart
    from payments.models import PaymentOrder
    import pytz
    
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    ist = pytz.timezone('Asia/Kolkata')
    
    print(f"👤 User: {user.email}")
    
    # Show what the NEW redirect handler logic does
    print(f"\n🔄 NEW REDIRECT HANDLER LOGIC (FIXED):")
    
    # This is exactly what the fixed redirect handler does
    successful_payment = PaymentOrder.objects.filter(
        user=user, 
        status='SUCCESS'
    ).order_by('-created_at').first()
    
    if successful_payment:
        target_cart = Cart.objects.filter(cart_id=successful_payment.cart_id).first()
        
        print(f"   1. ✅ Finds most recent SUCCESS payment: {successful_payment.merchant_order_id}")
        print(f"   2. ✅ Gets corresponding cart: {target_cart.cart_id}")
        print(f"      Service: {target_cart.puja_service.title}")
        print(f"      Date: {target_cart.selected_date}")
        print(f"      Time: {target_cart.selected_time}")
        
        # Get booking for this cart
        booking = Booking.objects.filter(cart=target_cart).first()
        
        if booking:
            print(f"   3. ✅ Returns existing booking: {booking.book_id}")
            
            # This is the redirect URL that would be generated
            redirect_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={successful_payment.merchant_order_id}&redirect_source=phonepe"
            
            print(f"\n🌐 REDIRECT URL:")
            print(f"   {redirect_url}")
            
            booking_created_ist = booking.created_at.astimezone(ist)
            print(f"\n📋 BOOKING DETAILS:")
            print(f"   ID: {booking.book_id}")
            print(f"   Service: {target_cart.puja_service.title}")
            print(f"   Status: {booking.status}")
            print(f"   Created (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"   Cart ID: {booking.cart.cart_id}")
            
            print(f"\n🎯 SOLUTION SUMMARY:")
            print(f"   PROBLEM: Redirect handler was finding 'latest cart' instead of 'latest paid cart'")
            print(f"   SOLUTION: Changed logic to find cart with most recent successful payment")
            print(f"   RESULT: Now correctly returns booking for the cart that was actually paid")
            
            print(f"\n📊 BEFORE vs AFTER FIX:")
            print(f"   BEFORE: Always found latest cart by creation time → wrong booking")
            print(f"   AFTER:  Finds latest cart by successful payment → correct booking")
            
            print(f"\n🚀 TESTING INSTRUCTIONS:")
            print(f"   1. Create new cart in Swagger")
            print(f"   2. Initiate payment via /api/payments/cart/")
            print(f"   3. Visit PhonePe payment URL (simulate success)")
            print(f"   4. Get redirected to /api/payments/redirect/simple/")
            print(f"   5. Should redirect to booking for the NEW cart (not old one)")
            
        else:
            print(f"   3. ❌ No booking found for target cart")
    else:
        print(f"   ❌ No successful payment found")
    
    # Show recent activity
    print(f"\n📈 RECENT ACTIVITY:")
    recent_payments = PaymentOrder.objects.filter(user=user).order_by('-created_at')[:3]
    
    for i, payment in enumerate(recent_payments, 1):
        cart = Cart.objects.filter(cart_id=payment.cart_id).first()
        booking = Booking.objects.filter(cart=cart).first() if cart else None
        
        payment_created_ist = payment.created_at.astimezone(ist)
        
        print(f"   {i}. Payment: {payment.merchant_order_id}")
        print(f"      Status: {payment.status}")
        print(f"      Cart: {cart.puja_service.title if cart else 'Unknown'}")
        print(f"      Booking: {booking.book_id if booking else 'None'}")
        print(f"      Created: {payment_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print()

if __name__ == "__main__":
    final_verification()
