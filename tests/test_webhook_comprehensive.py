#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from payments.services import WebhookService
from cart.models import Cart
from booking.models import Booking

def test_webhook_formats():
    """Test different webhook formats that PhonePe might send"""
    print("=== TESTING WEBHOOK FORMATS ===\n")
    
    # Find a payment to test with
    payment = PaymentOrder.objects.filter(cart_id__isnull=False).first()
    if not payment:
        print("No payments found to test webhook with.")
        return
    
    print(f"Testing webhook for payment: {payment.merchant_order_id}")
    print(f"Current status: {payment.status}")
    
    # Test different webhook formats that PhonePe might send
    webhook_formats = [
        {
            "name": "Format 1 - eventType",
            "data": {
                'merchantOrderId': payment.merchant_order_id,
                'eventType': 'PAYMENT_SUCCESS',
                'transactionId': f'TXN_{payment.merchant_order_id}',
                'amount': int(payment.amount * 100),
            }
        },
        {
            "name": "Format 2 - state",
            "data": {
                'merchantOrderId': payment.merchant_order_id,
                'state': 'COMPLETED',
                'transactionId': f'TXN_{payment.merchant_order_id}',
                'amount': int(payment.amount * 100),
            }
        },
        {
            "name": "Format 3 - status",
            "data": {
                'merchantOrderId': payment.merchant_order_id,
                'status': 'SUCCESS',
                'transactionId': f'TXN_{payment.merchant_order_id}',
                'amount': int(payment.amount * 100),
            }
        },
        {
            "name": "Format 4 - responseCode",
            "data": {
                'merchantOrderId': payment.merchant_order_id,
                'responseCode': 'SUCCESS',
                'transactionId': f'TXN_{payment.merchant_order_id}',
                'amount': int(payment.amount * 100),
            }
        }
    ]
    
    webhook_service = WebhookService()
    
    for webhook_format in webhook_formats:
        print(f"\n--- Testing {webhook_format['name']} ---")
        print(f"Data: {webhook_format['data']}")
        
        # Reset payment status for testing
        payment.status = 'INITIATED'
        payment.save()
        
        # Test webhook processing
        result = webhook_service.process_payment_webhook(webhook_format['data'])
        
        print(f"Success: {result['success']}")
        if result['success']:
            updated_payment = result['payment_order']
            print(f"Payment status after webhook: {updated_payment.status}")
            print(f"Event type detected: {result['event_type']}")
            
            # Check if booking was created
            if payment.cart_id:
                try:
                    cart = Cart.objects.get(cart_id=payment.cart_id)
                    booking = Booking.objects.filter(cart=cart).first()
                    if booking:
                        print(f"✅ Booking created: {booking.book_id}")
                    else:
                        print(f"❌ No booking created")
                except Exception as e:
                    print(f"❌ Error checking booking: {e}")
        else:
            print(f"❌ Error: {result.get('error')}")

def test_direct_webhook_endpoint():
    """Test the webhook endpoint directly via HTTP"""
    print(f"\n=== TESTING WEBHOOK ENDPOINT ===\n")
    
    # Find a payment to test with
    payment = PaymentOrder.objects.filter(cart_id__isnull=False).first()
    if not payment:
        print("No payments found to test webhook endpoint.")
        return
    
    webhook_url = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"
    
    # Test webhook data
    webhook_data = {
        'merchantOrderId': payment.merchant_order_id,
        'state': 'COMPLETED',
        'transactionId': f'TXN_{payment.merchant_order_id}',
        'amount': int(payment.amount * 100),
        'responseCode': 'SUCCESS'
    }
    
    print(f"Sending webhook to: {webhook_url}")
    print(f"Data: {webhook_data}")
    
    try:
        response = requests.post(webhook_url, json=webhook_data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        # Check if booking was created
        if payment.cart_id:
            try:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                if booking:
                    print(f"✅ Booking created via HTTP webhook: {booking.book_id}")
                    
                    # Test redirect URL
                    redirect_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}"
                    print(f"✅ Redirect URL: {redirect_url}")
                else:
                    print(f"❌ No booking created via HTTP webhook")
            except Exception as e:
                print(f"❌ Error checking booking: {e}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook endpoint. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error testing webhook endpoint: {e}")

def force_create_test_booking():
    """Force create a booking to test the redirect URL format"""
    print(f"\n=== FORCE CREATING TEST BOOKING ===\n")
    
    # Find a successful payment to create booking for
    payment = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).first()
    
    if not payment:
        # Create a successful payment if none exists
        payment = PaymentOrder.objects.filter(cart_id__isnull=False).first()
        if payment:
            payment.mark_success(
                phonepe_transaction_id=f'TEST_TXN_{payment.merchant_order_id}',
                phonepe_response={'test': True}
            )
            print(f"Marked payment as successful: {payment.merchant_order_id}")
    
    if payment and payment.cart_id:
        try:
            cart = Cart.objects.get(cart_id=payment.cart_id)
            existing_booking = Booking.objects.filter(cart=cart).first()
            
            if not existing_booking:
                webhook_service = WebhookService()
                booking = webhook_service._create_booking_from_cart(payment)
                if booking:
                    print(f"✅ Test booking created: {booking.book_id}")
                    redirect_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}"
                    print(f"✅ Final redirect URL: {redirect_url}")
                else:
                    print(f"❌ Failed to create test booking")
            else:
                print(f"✅ Booking already exists: {existing_booking.book_id}")
                redirect_url = f"http://localhost:3000/confirmbooking?book_id={existing_booking.book_id}&order_id={payment.merchant_order_id}"
                print(f"✅ Redirect URL: {redirect_url}")
                
        except Exception as e:
            print(f"❌ Error creating test booking: {e}")

if __name__ == "__main__":
    test_webhook_formats()
    test_direct_webhook_endpoint()
    force_create_test_booking()
