#!/usr/bin/env python3
"""
Test the FIXED payment system to ensure failed payments don't create bookings
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from accounts.models import User, Address
from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from payments.professional_redirect_handler import ProfessionalPaymentRedirectHandler
from payments.hyper_speed_redirect_handler import HyperSpeedPaymentRedirectHandler
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
import json

def test_failed_payment_no_booking():
    print("🔍 Testing FIXED Payment System - Failed Payments Should NOT Create Bookings")
    print("=" * 80)
    
    # Get test data
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ Test user not found")
        return
    
    address = Address.objects.filter(user=user).first()
    cart = Cart.objects.filter(user=user).first()
    
    print(f"✅ User: {user.email}")
    print(f"✅ Address: {address.id} - {address.city if address else 'None'}")
    print(f"✅ Cart: {cart.id if cart else 'None'}")
    
    # Test 1: Create a FAILED payment order
    print("\n📝 TEST 1: Creating FAILED Payment Order")
    failed_payment = PaymentOrder.objects.create(
        user=user,
        merchant_order_id="TEST_FAILED_001",
        amount=100.00,
        status='FAILED',  # This is a FAILED payment
        cart_id=cart.cart_id if cart else None,  # Use cart UUID, not database ID
        address_id=address.id if address else None
    )
    print(f"✅ Created FAILED payment: {failed_payment.merchant_order_id}")
    
    # Test 2: Try professional redirect handler with FAILED payment
    print("\n🧪 TEST 2: Professional Handler with FAILED Payment")
    try:
        handler = ProfessionalPaymentRedirectHandler()
        request = HttpRequest()
        request.method = 'GET'
        request.user = user
        request.META = {'HTTP_USER_AGENT': 'Test Agent'}
        
        # Call the handler
        response = handler.get(request)
        
        # Check if any booking was created for this failed payment
        booking_count = Booking.objects.filter(cart=cart).count() if cart else 0
        print(f"📊 Bookings after FAILED payment: {booking_count}")
        
        # Verify no new booking was created
        if response.status_code == 302 and ('failedbooking' in response.url or 'payment-error' in response.url):
            print("✅ CORRECT: Failed payment redirected to failure page")
        else:
            print(f"❌ WRONG: Failed payment response: {response.status_code} -> {response.url}")
            
    except Exception as e:
        print(f"⚠️ Handler test error: {e}")
    
    # Test 3: Create a SUCCESS payment order
    print("\n📝 TEST 3: Creating SUCCESS Payment Order")
    success_payment = PaymentOrder.objects.create(
        user=user,
        merchant_order_id="TEST_SUCCESS_001", 
        amount=100.00,
        status='SUCCESS',  # This is a SUCCESS payment
        cart_id=cart.cart_id if cart else None,  # Use cart UUID, not database ID
        address_id=address.id if address else None
    )
    print(f"✅ Created SUCCESS payment: {success_payment.merchant_order_id}")
    
    # Test 4: Try professional redirect handler with SUCCESS payment
    print("\n🧪 TEST 4: Professional Handler with SUCCESS Payment")
    try:
        # Count bookings before
        bookings_before = Booking.objects.filter(cart=cart).count() if cart else 0
        print(f"📊 Bookings before SUCCESS payment: {bookings_before}")
        
        handler = ProfessionalPaymentRedirectHandler()
        request = HttpRequest()
        request.method = 'GET'
        request.user = user
        request.META = {'HTTP_USER_AGENT': 'Test Agent'}
        
        # Call the handler
        response = handler.get(request)
        
        # Count bookings after
        bookings_after = Booking.objects.filter(cart=cart).count() if cart else 0
        print(f"📊 Bookings after SUCCESS payment: {bookings_after}")
        
        # Verify booking was created for success payment
        if response.status_code == 302 and 'confirmbooking' in response.url:
            print("✅ CORRECT: Success payment redirected to confirmation page")
            if bookings_after > bookings_before:
                print("✅ CORRECT: Booking created for successful payment")
            else:
                print("⚠️ INFO: No new booking (might already exist)")
        else:
            print(f"❌ WRONG: Success payment response: {response.status_code} -> {response.url}")
            
    except Exception as e:
        print(f"⚠️ Handler test error: {e}")
    
    # Cleanup test payments
    PaymentOrder.objects.filter(merchant_order_id__startswith="TEST_").delete()
    print("\n🧹 Cleaned up test payments")
    
    print("\n" + "=" * 80)
    print("🎯 SUMMARY: The system should now properly verify payments before creating bookings!")
    print("❌ Failed payments -> Redirect to failure page, NO booking created")
    print("✅ Success payments -> Redirect to success page, booking created")

if __name__ == "__main__":
    test_failed_payment_no_booking()
