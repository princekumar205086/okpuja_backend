#!/usr/bin/env python
import os
import django
import hashlib
import json
import requests
import time

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payments.models import PaymentOrder
from cart.models import Cart
from booking.models import Booking

def test_live_webhook():
    """Test webhook with live Django server"""
    print("🌐 TESTING LIVE WEBHOOK ENDPOINT")
    print("="*50)
    
    # Wait for server to start
    print("⏳ Waiting for Django server to start...")
    time.sleep(3)
    
    # Calculate auth hash
    username = getattr(settings, 'PHONEPE_WEBHOOK_USERNAME', 'okpuja_webhook_user')
    password = getattr(settings, 'PHONEPE_WEBHOOK_PASSWORD', 'Okpuja2025')
    credentials_string = f"{username}:{password}"
    auth_hash = hashlib.sha256(credentials_string.encode('utf-8')).hexdigest()
    
    print(f"🔐 Auth Hash: {auth_hash}")
    
    # Find a payment order to test with
    payment_order = PaymentOrder.objects.filter(
        cart_id__isnull=False,
        status__in=['INITIATED', 'PENDING']
    ).order_by('-created_at').first()
    
    if not payment_order:
        print("❌ No payment order available for testing")
        return
    
    print(f"📦 Testing with order: {payment_order.merchant_order_id}")
    
    # Create PhonePe V2 webhook payload
    webhook_payload = {
        "event": "checkout.order.completed",
        "payload": {
            "orderId": f"OMO{payment_order.merchant_order_id[-15:]}",
            "merchantId": "M22G7HGSSB3SC",
            "merchantOrderId": payment_order.merchant_order_id,
            "state": "COMPLETED",
            "amount": int(payment_order.amount * 100),  # Convert to paisa
            "expireAt": 1724866793837,
            "paymentDetails": [
                {
                    "paymentMode": "UPI_QR",
                    "transactionId": f"TXN{payment_order.merchant_order_id[-8:]}",
                    "timestamp": 1724866793837,
                    "amount": int(payment_order.amount * 100),
                    "state": "COMPLETED"
                }
            ]
        }
    }
    
    # Test webhook endpoint
    url = "http://localhost:8000/api/payments/webhook/phonepe/"
    headers = {
        'Authorization': auth_hash,
        'Content-Type': 'application/json'
    }
    
    print(f"📡 Sending POST to: {url}")
    
    try:
        response = requests.post(url, json=webhook_payload, headers=headers, timeout=30)
        print(f"📊 Response Status: {response.status_code}")
        print(f"📝 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook endpoint working correctly!")
            
            # Check if booking was created
            payment_order.refresh_from_db()
            print(f"💳 Payment status updated to: {payment_order.status}")
            
            try:
                cart = Cart.objects.get(cart_id=payment_order.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                if booking:
                    print(f"📋 ✅ Booking created: {booking.book_id}")
                    print(f"   📅 Date: {booking.selected_date}")
                    print(f"   💰 Amount: ₹{booking.total_amount}")
                else:
                    print("📋 ❌ No booking found")
            except Cart.DoesNotExist:
                print("🛒 ❌ Cart not found")
                
        else:
            print("❌ Webhook endpoint error!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Django server")
        print("💡 Make sure server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_live_webhook()
