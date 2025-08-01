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
from accounts.models import User
from django.utils import timezone
from datetime import timedelta

def debug_recent_payments():
    """Debug recent payments and booking creation"""
    print("=== DEBUGGING RECENT PAYMENTS ===\n")
    
    # Get payments from last hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_payments = PaymentOrder.objects.filter(
        created_at__gte=one_hour_ago
    ).order_by('-created_at')
    
    print(f"Recent payments (last hour): {recent_payments.count()}")
    
    for payment in recent_payments:
        print(f"\n📋 Payment: {payment.merchant_order_id}")
        print(f"   Status: {payment.status}")
        print(f"   User: {payment.user.email}")
        print(f"   Cart ID: {payment.cart_id}")
        print(f"   Created: {payment.created_at}")
        print(f"   Updated: {payment.updated_at}")
        
        # Check if cart exists
        if payment.cart_id:
            try:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                print(f"   ✅ Cart exists: {cart.cart_id}")
                print(f"   Cart status: {cart.status}")
                print(f"   Cart service: {cart.puja_service.title if cart.puja_service else 'N/A'}")
                print(f"   Cart package: {str(cart.package) if cart.package else 'N/A'}")
                
                # Check if booking exists for this cart
                booking = Booking.objects.filter(cart=cart).first()
                if booking:
                    print(f"   ✅ Booking exists: {booking.book_id}")
                    print(f"   Booking status: {booking.status}")
                    print(f"   Booking created: {booking.created_at}")
                else:
                    print(f"   ❌ NO BOOKING found for this cart!")
                    print(f"   🔧 This is the problem - booking should be auto-created")
                    
            except Cart.DoesNotExist:
                print(f"   ❌ Cart does not exist: {payment.cart_id}")
        else:
            print(f"   ❌ No cart_id in payment")

def check_webhook_logs():
    """Check if webhook is being called"""
    print(f"\n=== CHECKING WEBHOOK STATUS ===\n")
    
    # Look for recent successful payments without bookings
    from django.db.models import Q
    
    problematic_payments = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False,
        created_at__gte=timezone.now() - timedelta(hours=1)
    )
    
    # Check which ones don't have bookings
    payments_without_bookings = []
    for payment in problematic_payments:
        try:
            cart = Cart.objects.get(cart_id=payment.cart_id)
            booking = Booking.objects.filter(cart=cart).first()
            if not booking:
                payments_without_bookings.append(payment)
        except Cart.DoesNotExist:
            payments_without_bookings.append(payment)
    
    print(f"Successful payments WITHOUT bookings: {len(payments_without_bookings)}")
    
    for payment in payments_without_bookings:
        print(f"\n⚠️ Problem Payment: {payment.merchant_order_id}")
        print(f"   User: {payment.user.email}")
        print(f"   Cart: {payment.cart_id}")
        print(f"   Status: {payment.status}")
        print(f"   PhonePe TXN: {payment.phonepe_transaction_id}")
        
        # Try to manually create booking
        try:
            from payments.services import WebhookService
            webhook_service = WebhookService()
            
            cart = Cart.objects.get(cart_id=payment.cart_id)
            booking = webhook_service._create_booking_from_cart(payment)
            
            if booking:
                print(f"   ✅ Manually created booking: {booking.book_id}")
            else:
                print(f"   ❌ Failed to create booking manually")
                
        except Exception as e:
            print(f"   ❌ Error creating booking: {e}")

def check_celery_status():
    """Check if Celery tasks are working"""
    print(f"\n=== CHECKING CELERY STATUS ===\n")
    
    try:
        from celery import current_app
        from core.tasks import send_booking_confirmation
        
        # Check if Celery is configured
        print(f"Celery app: {current_app}")
        print(f"Broker URL: {current_app.conf.broker_url}")
        
        # Try to send a test task (don't actually execute)
        print(f"✅ send_booking_confirmation task available")
        
        # Check recent bookings and see if emails were sent
        recent_bookings = Booking.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1)
        )
        
        print(f"Recent bookings: {recent_bookings.count()}")
        for booking in recent_bookings:
            print(f"   Booking: {booking.book_id} - {booking.created_at}")
            
    except Exception as e:
        print(f"❌ Celery error: {e}")

def simulate_webhook_call():
    """Simulate a webhook call for the latest payment"""
    print(f"\n=== SIMULATING WEBHOOK CALL ===\n")
    
    latest_payment = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).order_by('-created_at').first()
    
    if not latest_payment:
        print("❌ No successful payments found")
        return
    
    print(f"Testing webhook for payment: {latest_payment.merchant_order_id}")
    
    # Simulate PhonePe webhook payload
    webhook_data = {
        "success": True,
        "code": "PAYMENT_SUCCESS",
        "message": "Your payment is successful.",
        "data": {
            "merchantId": "OKPUJAT",
            "merchantTransactionId": latest_payment.merchant_order_id,
            "transactionId": f"T{latest_payment.merchant_order_id[-10:]}",
            "amount": int(latest_payment.amount * 100),  # Convert to paise
            "state": "COMPLETED",
            "responseCode": "SUCCESS",
            "paymentInstrument": {
                "type": "UPI",
                "utr": f"UTR{latest_payment.merchant_order_id[-8:]}"
            }
        }
    }
    
    try:
        from payments.services import WebhookService
        webhook_service = WebhookService()
        result = webhook_service.process_webhook(webhook_data)
        
        print(f"✅ Webhook processed successfully")
        print(f"   Result: {result}")
        
        # Check if booking was created
        cart = Cart.objects.get(cart_id=latest_payment.cart_id)
        booking = Booking.objects.filter(cart=cart).first()
        
        if booking:
            print(f"✅ Booking created/found: {booking.book_id}")
        else:
            print(f"❌ Still no booking after webhook simulation")
            
    except Exception as e:
        print(f"❌ Webhook simulation failed: {e}")

if __name__ == "__main__":
    debug_recent_payments()
    check_webhook_logs() 
    check_celery_status()
    simulate_webhook_call()
