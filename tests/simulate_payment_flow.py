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

def simulate_successful_payment():
    """Simulate a successful payment flow"""
    print("=== SIMULATING SUCCESSFUL PAYMENT FLOW ===\n")
    
    # Find a pending payment to mark as successful
    pending_payment = PaymentOrder.objects.filter(
        status='INITIATED',
        cart_id__isnull=False
    ).first()
    
    if not pending_payment:
        print("No pending payments found to test with.")
        return
    
    print(f"1. Found pending payment: {pending_payment.merchant_order_id}")
    print(f"   Status: {pending_payment.status}")
    print(f"   Cart ID: {pending_payment.cart_id}")
    
    # Manually mark payment as successful (simulating PhonePe success)
    print(f"\n2. Marking payment as successful...")
    pending_payment.mark_success(
        phonepe_transaction_id=f"TXN_{pending_payment.merchant_order_id}",
        phonepe_response={"status": "SUCCESS", "simulated": True}
    )
    print(f"   ✅ Payment marked as successful")
    
    # Check if cart exists
    try:
        cart = Cart.objects.get(cart_id=pending_payment.cart_id)
        print(f"   ✅ Cart found: {cart.cart_id} (status: {cart.status})")
    except Cart.DoesNotExist:
        print(f"   ❌ Cart not found")
        return
    
    # Create booking using webhook service
    print(f"\n3. Creating booking from cart...")
    webhook_service = WebhookService()
    booking = webhook_service._create_booking_from_cart(pending_payment)
    
    if booking:
        print(f"   ✅ Booking created: {booking.book_id}")
        print(f"   ✅ Booking status: {booking.status}")
        print(f"   ✅ Email notification queued")
        
        # Update cart status
        cart.refresh_from_db()
        print(f"   ✅ Cart status updated to: {cart.status}")
        
    else:
        print(f"   ❌ Failed to create booking")
        return
    
    # Simulate redirect logic
    print(f"\n4. Simulating redirect logic...")
    success_url = "http://localhost:3000/confirmbooking"
    
    # Check for booking (as redirect handler would)
    booking_check = Booking.objects.filter(cart=cart).first()
    if booking_check:
        redirect_url = f"{success_url}?booking_id={booking_check.book_id}&order_id={pending_payment.merchant_order_id}"
        print(f"   ✅ SUCCESS REDIRECT: {redirect_url}")
    else:
        redirect_url = f"{success_url}?order_id={pending_payment.merchant_order_id}"
        print(f"   ❌ FALLBACK REDIRECT: {redirect_url}")
    
    return pending_payment, booking

def test_redirect_handler_directly():
    """Test the redirect handler logic directly"""
    print(f"\n=== TESTING REDIRECT HANDLER LOGIC ===\n")
    
    # Find a successful payment
    successful_payment = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).first()
    
    if not successful_payment:
        print("No successful payments found to test redirect with.")
        return
    
    print(f"Testing redirect for: {successful_payment.merchant_order_id}")
    
    # Simulate the exact logic from redirect handler
    from payments.redirect_handler import PaymentRedirectHandler
    from payments.services import PaymentService, WebhookService
    
    merchant_order_id = successful_payment.merchant_order_id
    
    # Check payment status (as redirect handler does)
    payment_service = PaymentService()
    result = payment_service.check_payment_status(merchant_order_id)
    
    if result['success']:
        payment_order = result['payment_order']
        status = payment_order.status
        print(f"Payment status from check: {status}")
        
        if status == 'SUCCESS':
            success_url = "http://localhost:3000/confirmbooking"
            
            # Check for booking
            booking_id = None
            if payment_order.cart_id:
                try:
                    from cart.models import Cart
                    from booking.models import Booking
                    cart = Cart.objects.get(cart_id=payment_order.cart_id)
                    booking = Booking.objects.filter(cart=cart).first()
                    
                    # If no booking exists, create it now
                    if not booking:
                        print("No booking found, creating during redirect...")
                        webhook_service = WebhookService()
                        booking = webhook_service._create_booking_from_cart(payment_order)
                        if booking:
                            print(f"✅ Booking created during redirect: {booking.book_id}")
                        else:
                            print("❌ Failed to create booking during redirect")
                    
                    if booking:
                        booking_id = booking.book_id
                        
                except Exception as e:
                    print(f"Error in booking logic: {e}")
            
            # Build redirect URL
            if booking_id:
                redirect_url = f"{success_url}?booking_id={booking_id}&order_id={merchant_order_id}"
                print(f"✅ FINAL REDIRECT: {redirect_url}")
            else:
                redirect_url = f"{success_url}?order_id={merchant_order_id}&status=no_booking"
                print(f"❌ FALLBACK REDIRECT: {redirect_url}")

if __name__ == "__main__":
    payment, booking = simulate_successful_payment()
    test_redirect_handler_directly()
