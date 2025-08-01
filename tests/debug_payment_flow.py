#!/usr/bin/env python
import os
import sys
import django
import requests
import json
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User
from cart.models import Cart
from booking.models import Booking
from payments.models import PaymentOrder
from payments.services import PaymentService, WebhookService
from puja.models import PujaService, Package

def debug_payment_flow():
    """Debug the complete payment flow"""
    print("=== PAYMENT FLOW DEBUGGING ===\n")
    
    # 1. Check existing data
    print("1. Checking existing data...")
    print(f"   Total users: {User.objects.count()}")
    print(f"   Total carts: {Cart.objects.count()}")
    print(f"   Total payments: {PaymentOrder.objects.count()}")
    print(f"   Total bookings: {Booking.objects.count()}")
    
    # Check recent payments and their status
    recent_payments = PaymentOrder.objects.order_by('-created_at')[:5]
    print(f"\n   Recent payments:")
    for payment in recent_payments:
        print(f"   - {payment.merchant_order_id}: {payment.status} (cart: {payment.cart_id})")
        
        # Check if booking exists for cart-based payments
        if payment.cart_id:
            try:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                print(f"     Cart status: {cart.status}, Booking: {'YES' if booking else 'NO'}")
                if booking:
                    print(f"     Booking ID: {booking.book_id}, Status: {booking.status}")
            except Cart.DoesNotExist:
                print(f"     Cart not found!")
    
    # 2. Test payment status check logic
    print(f"\n2. Testing payment status check...")
    if recent_payments.exists():
        payment = recent_payments.first()
        print(f"   Testing payment: {payment.merchant_order_id}")
        
        payment_service = PaymentService()
        result = payment_service.check_payment_status(payment.merchant_order_id)
        
        print(f"   Status check result: {result['success']}")
        if result['success']:
            print(f"   Payment status: {result['payment_order'].status}")
            
            # If payment is successful but no booking, try to create one
            if payment.status == 'SUCCESS' and payment.cart_id:
                try:
                    cart = Cart.objects.get(cart_id=payment.cart_id)
                    booking = Booking.objects.filter(cart=cart).first()
                    if not booking:
                        print(f"   No booking found - trying to create one...")
                        webhook_service = WebhookService()
                        booking = webhook_service._create_booking_from_cart(payment)
                        if booking:
                            print(f"   ✓ Booking created: {booking.book_id}")
                        else:
                            print(f"   ✗ Failed to create booking")
                    else:
                        print(f"   Booking already exists: {booking.book_id}")
                except Exception as e:
                    print(f"   Error checking/creating booking: {e}")
    
    # 3. Test webhook processing
    print(f"\n3. Testing webhook processing...")
    if recent_payments.exists():
        payment = recent_payments.first()
        print(f"   Testing webhook for payment: {payment.merchant_order_id}")
        
        # Simulate success webhook data
        webhook_data = {
            'merchantOrderId': payment.merchant_order_id,
            'eventType': 'PAYMENT_SUCCESS',
            'transactionId': f'TXN_{payment.merchant_order_id}',
            'amount': int(payment.amount * 100),  # Convert to paisa
            'status': 'SUCCESS'
        }
        
        webhook_service = WebhookService()
        result = webhook_service.process_payment_webhook(webhook_data)
        
        print(f"   Webhook processing result: {result['success']}")
        if result['success']:
            print(f"   Event type: {result['event_type']}")
            print(f"   Payment status after webhook: {result['payment_order'].status}")
            
            # Check if booking was created
            if payment.cart_id:
                try:
                    cart = Cart.objects.get(cart_id=payment.cart_id)
                    booking = Booking.objects.filter(cart=cart).first()
                    if booking:
                        print(f"   ✓ Booking exists after webhook: {booking.book_id}")
                    else:
                        print(f"   ✗ No booking created by webhook")
                except Exception as e:
                    print(f"   Error checking booking: {e}")
    
    # 4. Check redirect handler logic
    print(f"\n4. Testing redirect handler logic...")
    if recent_payments.exists():
        payment = recent_payments.first()
        print(f"   Testing redirect for payment: {payment.merchant_order_id}")
        
        if payment.cart_id:
            try:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                if booking:
                    print(f"   ✓ Booking found for redirect: {booking.book_id}")
                    print(f"   Redirect URL would be: /confirmbooking?booking_id={booking.book_id}&order_id={payment.merchant_order_id}")
                else:
                    print(f"   ✗ No booking found for redirect")
                    print(f"   Redirect URL would be: /confirmbooking?order_id={payment.merchant_order_id}")
            except Exception as e:
                print(f"   Error in redirect logic: {e}")
    
    print(f"\n=== DEBUG COMPLETE ===")

def fix_missing_bookings():
    """Fix any successful payments that don't have bookings"""
    print("\n=== FIXING MISSING BOOKINGS ===\n")
    
    # Find successful cart-based payments without bookings
    successful_payments = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    )
    
    print(f"Found {successful_payments.count()} successful cart-based payments")
    
    fixed_count = 0
    for payment in successful_payments:
        try:
            cart = Cart.objects.get(cart_id=payment.cart_id)
            booking = Booking.objects.filter(cart=cart).first()
            
            if not booking:
                print(f"Creating booking for payment: {payment.merchant_order_id}")
                webhook_service = WebhookService()
                booking = webhook_service._create_booking_from_cart(payment)
                
                if booking:
                    print(f"   ✓ Created booking: {booking.book_id}")
                    fixed_count += 1
                else:
                    print(f"   ✗ Failed to create booking")
            else:
                print(f"Payment {payment.merchant_order_id} already has booking: {booking.book_id}")
                
        except Cart.DoesNotExist:
            print(f"Cart not found for payment: {payment.merchant_order_id}")
        except Exception as e:
            print(f"Error fixing payment {payment.merchant_order_id}: {e}")
    
    print(f"\nFixed {fixed_count} missing bookings")

if __name__ == "__main__":
    debug_payment_flow()
    fix_missing_bookings()
