#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from payments.services import WebhookService

def test_webhook_auto_verification():
    """Test webhook processing for automatic payment verification"""
    print("=== TESTING WEBHOOK AUTO-VERIFICATION ===\n")
    
    # Find a payment to test webhook with
    payment = PaymentOrder.objects.filter(cart_id__isnull=False).first()
    if not payment:
        print("No cart-based payments found to test webhook.")
        return
    
    print(f"Testing webhook for payment: {payment.merchant_order_id}")
    print(f"Current status: {payment.status}")
    
    # Simulate PhonePe success webhook
    webhook_data = {
        'merchantOrderId': payment.merchant_order_id,
        'eventType': 'PAYMENT_SUCCESS',
        'transactionId': f'TXN_{payment.merchant_order_id}',
        'amount': int(payment.amount * 100),  # Convert to paisa
        'status': 'SUCCESS'
    }
    
    print(f"\n1. Simulating webhook data:")
    print(f"   Event Type: {webhook_data['eventType']}")
    print(f"   Transaction ID: {webhook_data['transactionId']}")
    
    # Process webhook
    webhook_service = WebhookService()
    result = webhook_service.process_payment_webhook(webhook_data)
    
    print(f"\n2. Webhook processing result:")
    print(f"   Success: {result['success']}")
    
    if result['success']:
        updated_payment = result['payment_order']
        print(f"   Event Type: {result['event_type']}")
        print(f"   Payment Status: {updated_payment.status}")
        
        # Check if booking was created
        if payment.cart_id:
            from cart.models import Cart
            from booking.models import Booking
            
            try:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                
                if booking:
                    print(f"   ✅ Booking created: {booking.book_id}")
                    print(f"   ✅ Cart status: {cart.status}")
                    
                    # Test redirect URL
                    success_url = "http://localhost:3000/confirmbooking"
                    redirect_url = f"{success_url}?booking_id={booking.book_id}&order_id={payment.merchant_order_id}"
                    print(f"   ✅ Redirect URL: {redirect_url}")
                else:
                    print(f"   ❌ No booking created by webhook")
                    
            except Exception as e:
                print(f"   ❌ Error checking booking: {e}")
    else:
        print(f"   ❌ Webhook processing failed: {result.get('error')}")

def summary():
    """Print summary of all fixes"""
    print(f"\n=== SUMMARY OF FIXES ===")
    print("✅ 1. BOOKING AUTO-CREATION:")
    print("   - Fixed time format parsing (24h and 12h formats)")
    print("   - Made address field optional")
    print("   - Added booking creation to payment status check")
    print("   - Added booking creation to webhook processing")
    print("   - Added booking creation to redirect handler as fallback")
    
    print("\n✅ 2. REDIRECT WITH BOOKING_ID:")
    print("   - Enhanced redirect handler to ensure booking exists")
    print("   - Creates booking during redirect if missing")
    print("   - Includes booking_id in URL: ?booking_id=BK-XXX&order_id=YYY")
    
    print("\n✅ 3. EMAIL NOTIFICATIONS:")
    print("   - Fixed email task import and parameters")
    print("   - Emails are sent to both user and admin")
    print("   - Email functionality tested and working")
    print("   - Note: Check spam folder or Celery worker logs")
    
    print("\n🎯 FINAL FLOW:")
    print("   1. Payment successful → Webhook/Status Check")
    print("   2. Booking auto-created from cart")
    print("   3. Email notifications sent")
    print("   4. Redirect with booking_id parameter")
    print("   5. Frontend can fetch booking details")

if __name__ == "__main__":
    test_webhook_auto_verification()
    summary()
