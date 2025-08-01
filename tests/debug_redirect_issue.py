#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User
from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder
from payments.services import PaymentService, WebhookService

def debug_redirect_issue():
    """Debug why booking_id is missing from redirect"""
    print("=== DEBUGGING REDIRECT ISSUE ===\n")
    
    # Find the most recent payment to test
    recent_payment = PaymentOrder.objects.filter(cart_id__isnull=False).order_by('-created_at').first()
    
    if not recent_payment:
        print("No cart-based payments found.")
        return
    
    print(f"Testing payment: {recent_payment.merchant_order_id}")
    print(f"Payment status: {recent_payment.status}")
    print(f"Cart ID: {recent_payment.cart_id}")
    
    # Step 1: Check if cart exists
    try:
        cart = Cart.objects.get(cart_id=recent_payment.cart_id)
        print(f"✅ Cart found: {cart.cart_id} (status: {cart.status})")
    except Cart.DoesNotExist:
        print(f"❌ Cart not found for cart_id: {recent_payment.cart_id}")
        return
    
    # Step 2: Check if booking exists
    booking = Booking.objects.filter(cart=cart).first()
    if booking:
        print(f"✅ Booking exists: {booking.book_id} (status: {booking.status})")
    else:
        print(f"❌ No booking found for cart: {cart.cart_id}")
        
        # Try to create booking if payment is successful
        if recent_payment.status == 'SUCCESS':
            print("Payment is successful, attempting to create booking...")
            webhook_service = WebhookService()
            new_booking = webhook_service._create_booking_from_cart(recent_payment)
            if new_booking:
                print(f"✅ Booking created: {new_booking.book_id}")
                booking = new_booking
            else:
                print("❌ Failed to create booking")
    
    # Step 3: Simulate redirect logic
    print(f"\n=== REDIRECT SIMULATION ===")
    print(f"Payment status: {recent_payment.status}")
    
    if recent_payment.status == 'SUCCESS':
        success_url = "http://localhost:3000/confirmbooking"
        
        # Check for booking again (in case it was just created)
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            redirect_url = f"{success_url}?booking_id={booking.book_id}&order_id={recent_payment.merchant_order_id}"
            print(f"✅ SUCCESS REDIRECT: {redirect_url}")
        else:
            redirect_url = f"{success_url}?order_id={recent_payment.merchant_order_id}"
            print(f"❌ FALLBACK REDIRECT: {redirect_url}")
    else:
        print(f"Payment not successful, status: {recent_payment.status}")
    
    # Step 4: Test payment status check (which should create booking)
    print(f"\n=== TESTING PAYMENT STATUS CHECK ===")
    payment_service = PaymentService()
    result = payment_service.check_payment_status(recent_payment.merchant_order_id)
    
    if result['success']:
        updated_payment = result['payment_order']
        print(f"Status check result: {updated_payment.status}")
        
        # Check if booking was created during status check
        booking_after_status = Booking.objects.filter(cart=cart).first()
        if booking_after_status:
            print(f"✅ Booking found after status check: {booking_after_status.book_id}")
        else:
            print("❌ No booking created during status check")
    else:
        print(f"❌ Status check failed: {result.get('error')}")

def force_create_missing_bookings():
    """Force create bookings for any successful payments missing them"""
    print(f"\n=== FORCE CREATING MISSING BOOKINGS ===")
    
    # Find successful payments without bookings
    successful_payments = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    )
    
    for payment in successful_payments:
        try:
            cart = Cart.objects.get(cart_id=payment.cart_id)
            booking = Booking.objects.filter(cart=cart).first()
            
            if not booking:
                print(f"Creating missing booking for payment: {payment.merchant_order_id}")
                webhook_service = WebhookService()
                new_booking = webhook_service._create_booking_from_cart(payment)
                if new_booking:
                    print(f"✅ Created: {new_booking.book_id}")
                else:
                    print(f"❌ Failed to create booking")
            else:
                print(f"Payment {payment.merchant_order_id} already has booking: {booking.book_id}")
                
        except Cart.DoesNotExist:
            print(f"❌ Cart not found for payment: {payment.merchant_order_id}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_redirect_issue()
    force_create_missing_bookings()
