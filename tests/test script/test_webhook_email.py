#!/usr/bin/env python
"""
Test webhook processing and email notifications
"""

import requests
import json
import os
import sys
import django

# Setup Django for email testing
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.services import WebhookService
from booking.models import Booking
from core.tasks import send_booking_confirmation

# Test data
BASE_URL = "http://127.0.0.1:8000/api"

# Create a new cart and payment for webhook testing
def test_webhook_flow():
    print("🔔 Testing Webhook Flow...")
    print("=" * 40)
    
    # Login
    login_data = {"email": "asliprinceraj@gmail.com", "password": "testpass123"}
    
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed")
            return
            
        access_token = login_response.json().get('access')
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        
        # Create a new cart for webhook testing
        cart_data = {
            "service_type": "PUJA",
            "puja_service": 13,
            "package_id": 11,
            "selected_date": "2025-08-20",
            "selected_time": "14:00"
        }
        
        print("🛒 Creating cart for webhook test...")
        cart_response = requests.post(f"{BASE_URL}/cart/carts/", json=cart_data, headers=headers)
        
        if cart_response.status_code != 201:
            print(f"❌ Cart creation failed")
            return
            
        cart_result = cart_response.json()
        cart_id = cart_result.get('cart_id')
        print(f"✅ Cart created: {cart_id}")
        
        # Create payment
        print("💳 Creating payment...")
        payment_data = {"cart_id": cart_id}
        payment_response = requests.post(f"{BASE_URL}/payments/cart/", json=payment_data, headers=headers)
        
        if payment_response.status_code not in [200, 201]:
            print(f"❌ Payment creation failed")
            return
            
        payment_result = payment_response.json()
        order_id = payment_result.get('data', {}).get('payment_order', {}).get('merchant_order_id')
        print(f"✅ Payment created: {order_id}")
        
        # Simulate webhook call
        print("🔔 Simulating PhonePe webhook...")
        webhook_data = {
            "merchantOrderId": order_id,
            "state": "COMPLETED",
            "eventType": "PAYMENT_SUCCESS",
            "transactionId": f"T{order_id[-8:]}",
            "responseCode": "SUCCESS"
        }
        
        webhook_service = WebhookService()
        webhook_result = webhook_service.process_payment_webhook(webhook_data)
        
        if webhook_result.get('success'):
            print(f"✅ Webhook processed successfully")
            print(f"   Event Type: {webhook_result.get('event_type')}")
            
            # Check if booking was created
            booking_response = requests.get(f"{BASE_URL}/booking/bookings/by-cart/{cart_id}/", headers=headers)
            
            if booking_response.status_code == 200:
                booking_data = booking_response.json().get('data', {})
                booking_id = booking_data.get('book_id')
                print(f"✅ Booking created via webhook: {booking_id}")
                
                # Test email notification
                print("📧 Testing email notification...")
                try:
                    booking = Booking.objects.get(book_id=booking_id)
                    # Trigger email notification (this would normally be done by Celery)
                    send_booking_confirmation.delay(booking.id)
                    print(f"✅ Email notification queued for booking {booking_id}")
                except Exception as e:
                    print(f"❌ Email notification failed: {e}")
                    
            else:
                print(f"❌ Booking not created via webhook")
        else:
            print(f"❌ Webhook processing failed: {webhook_result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error during webhook test: {e}")
        import traceback
        traceback.print_exc()

def test_email_settings():
    print("\n📧 Testing Email Settings...")
    print("=" * 40)
    
    from django.conf import settings
    
    # Check email configuration
    print(f"Email Backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"Email Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"Email Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"Email Use TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
    print(f"Default From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    
    # Check if Celery is configured
    print(f"Celery Broker: {getattr(settings, 'CELERY_BROKER_URL', 'Not set')}")
    print(f"Celery Backend: {getattr(settings, 'CELERY_RESULT_BACKEND', 'Not set')}")

if __name__ == "__main__":
    test_email_settings()
    test_webhook_flow()
    
    print("\n🎉 All tests completed!")
    print("=" * 40)
