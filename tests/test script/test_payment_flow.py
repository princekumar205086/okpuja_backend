#!/usr/bin/env python
"""
Test script to verify the complete payment -> booking flow
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder
from accounts.models import User

def test_current_flow():
    """Test the current cart -> payment -> booking flow"""
    print("=" * 60)
    print("TESTING CART -> PAYMENT -> BOOKING FLOW")
    print("=" * 60)
    
    # Get test user
    try:
        user = User.objects.get(email="asliprinceraj@gmail.com")
        print(f"✅ Found test user: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ Test user not found")
        return
    
    # Check latest cart
    latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
    if latest_cart:
        print(f"✅ Latest cart: {latest_cart.cart_id} (Status: {latest_cart.status})")
        print(f"   Service: {latest_cart.service_type}")
        print(f"   Total: ₹{latest_cart.total_price}")
    else:
        print("❌ No cart found for user")
        return
    
    # Check payment for this cart
    payment = PaymentOrder.objects.filter(cart_id=latest_cart.cart_id).order_by('-created_at').first()
    if payment:
        print(f"✅ Payment found: {payment.merchant_order_id}")
        print(f"   Status: {payment.status}")
        print(f"   Amount: ₹{payment.amount_in_rupees}")
    else:
        print("❌ No payment found for cart")
        return
    
    # Check booking for this cart
    booking = Booking.objects.filter(cart=latest_cart).first()
    if booking:
        print(f"✅ Booking found: {booking.book_id}")
        print(f"   Status: {booking.status}")
        print(f"   Created: {booking.created_at}")
    else:
        print("❌ No booking found for cart")
        
        # If payment is successful but no booking, try to create it
        if payment.status == 'SUCCESS':
            print("🔧 Payment successful but no booking - attempting to create...")
            try:
                from payments.services import WebhookService
                webhook_service = WebhookService()
                booking = webhook_service._create_booking_from_cart(payment)
                
                if booking:
                    print(f"✅ Booking created: {booking.book_id}")
                else:
                    print("❌ Failed to create booking")
            except Exception as e:
                print(f"❌ Error creating booking: {e}")
    
    print("\n" + "=" * 60)
    print("TESTING NEW REDIRECT FLOW")
    print("=" * 60)
    
    # Test new redirect URL structure
    cart_id = latest_cart.cart_id
    order_id = payment.merchant_order_id if payment else "NO_PAYMENT"
    
    new_redirect_url = f"http://localhost:3000/confirmbooking?cart_id={cart_id}&order_id={order_id}&redirect_source=phonepe"
    print(f"🌐 New redirect URL structure:")
    print(f"   {new_redirect_url}")
    
    # Test the new booking endpoint
    print(f"\n🔍 Testing new booking endpoint:")
    print(f"   GET /api/booking/bookings/by-cart/{cart_id}/")
    
    if booking:
        print(f"✅ Endpoint should return booking: {booking.book_id}")
    else:
        print("⚠️  Endpoint should create booking or show payment status")
    
    print("\n" + "=" * 60)
    print("FLOW ANALYSIS")
    print("=" * 60)
    
    if latest_cart and payment and booking:
        print("✅ Complete flow working: Cart → Payment → Booking")
    elif latest_cart and payment:
        print("⚠️  Partial flow: Cart → Payment (Booking missing)")
        print("   This is the issue you're experiencing!")
    else:
        print("❌ Flow broken at early stage")
    
    print(f"\n📊 Summary:")
    print(f"   Cart ID: {latest_cart.cart_id if latest_cart else 'None'}")
    print(f"   Payment Status: {payment.status if payment else 'None'}")
    print(f"   Booking ID: {booking.book_id if booking else 'None'}")

if __name__ == "__main__":
    test_current_flow()
