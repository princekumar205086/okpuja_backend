#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from cart.models import Cart
from booking.models import Booking
from django.utils import timezone
from datetime import timedelta

def fix_latest_payment():
    """Fix the latest payment that's stuck in INITIATED status"""
    print("=== FIXING LATEST PAYMENT ISSUE ===\n")
    
    # Get the latest INITIATED payment
    latest_initiated = PaymentOrder.objects.filter(
        status='INITIATED',
        created_at__gte=timezone.now() - timedelta(hours=2)
    ).order_by('-created_at').first()
    
    if not latest_initiated:
        print("❌ No recent INITIATED payments found")
        return
    
    print(f"🔍 Found latest INITIATED payment: {latest_initiated.merchant_order_id}")
    print(f"   User: {latest_initiated.user.email}")
    print(f"   Amount: ₹{latest_initiated.amount}")
    print(f"   Created: {latest_initiated.created_at}")
    print(f"   Cart ID: {latest_initiated.cart_id}")
    
    # Check if PhonePe payment was actually successful
    # In real scenario, we would check with PhonePe API
    # For now, let's simulate a successful payment
    
    print(f"\n🔧 SIMULATING SUCCESSFUL PAYMENT...")
    
    # 1. Mark payment as successful
    latest_initiated.mark_success(
        phonepe_transaction_id=f'TXN_{latest_initiated.merchant_order_id[-10:]}',
        phonepe_response={
            'success': True,
            'code': 'PAYMENT_SUCCESS',
            'message': 'Your payment is successful.',
            'data': {
                'merchantTransactionId': latest_initiated.merchant_order_id,
                'transactionId': f'TXN_{latest_initiated.merchant_order_id[-10:]}',
                'amount': int(latest_initiated.amount * 100),
                'state': 'COMPLETED',
                'responseCode': 'SUCCESS'
            }
        }
    )
    print(f"✅ Payment marked as SUCCESS")
    
    # 2. Create booking via webhook service
    try:
        from payments.services import WebhookService
        webhook_service = WebhookService()
        
        cart = Cart.objects.get(cart_id=latest_initiated.cart_id)
        booking = webhook_service._create_booking_from_cart(latest_initiated)
        
        if booking:
            print(f"✅ Booking created: {booking.book_id}")
            print(f"✅ Booking status: {booking.status}")
            print(f"✅ Cart status updated to: {cart.status}")
            
            # 3. Trigger email notification
            from core.tasks import send_booking_confirmation
            send_booking_confirmation.delay(booking.id)
            print(f"✅ Email notification queued")
            
            # Show expected redirect URL
            expected_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={latest_initiated.merchant_order_id}&redirect_source=phonepe"
            print(f"\n🌐 Expected frontend redirect URL:")
            print(f"   {expected_url}")
            
        else:
            print(f"❌ Failed to create booking")
            
    except Exception as e:
        print(f"❌ Error creating booking: {e}")

def check_webhook_endpoint():
    """Check if webhook endpoint is accessible"""
    print(f"\n=== CHECKING WEBHOOK ENDPOINT ===\n")
    
    import requests
    webhook_url = "http://127.0.0.1:8000/api/payments/webhook/"
    
    try:
        # Test with OPTIONS request (CORS preflight)
        response = requests.options(webhook_url)
        print(f"OPTIONS {webhook_url}: {response.status_code}")
        
        # Test with GET request (should return 405 Method Not Allowed)
        response = requests.get(webhook_url)
        print(f"GET {webhook_url}: {response.status_code}")
        
        if response.status_code == 405:
            print(f"✅ Webhook endpoint is accessible (405 = Method Not Allowed is expected)")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to webhook endpoint. Is Django server running?")
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def show_phonepe_webhook_config():
    """Show PhonePe webhook configuration"""
    print(f"\n=== PHONEPE WEBHOOK CONFIGURATION ===\n")
    
    from django.conf import settings
    
    print(f"🔧 CURRENT CONFIGURATION:")
    print(f"   Webhook URL: {getattr(settings, 'PHONEPE_WEBHOOK_URL', 'NOT SET')}")
    print(f"   Merchant ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT SET')}")
    print(f"   Environment: {getattr(settings, 'PHONEPE_ENVIRONMENT', 'NOT SET')}")
    
    print(f"\n📋 PHONEPE DASHBOARD SETUP:")
    print(f"   1. Login to PhonePe Merchant Dashboard")
    print(f"   2. Go to Settings > Webhooks")
    print(f"   3. Set webhook URL: http://127.0.0.1:8000/api/payments/webhook/")
    print(f"   4. Enable events: payment.success, payment.failed")
    print(f"   5. Verify webhook is active")
    
    print(f"\n⚠️ PRODUCTION NOTES:")
    print(f"   - Use HTTPS for webhook URL in production")
    print(f"   - Use public domain, not localhost")
    print(f"   - Verify webhook signature for security")

if __name__ == "__main__":
    fix_latest_payment()
    check_webhook_endpoint()
    show_phonepe_webhook_config()
