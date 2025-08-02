#!/usr/bin/env python
import os
import django
import hashlib
import json
import requests

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

def test_webhook_auth():
    """Test the webhook authentication calculation"""
    print("🔐 TESTING WEBHOOK AUTHENTICATION")
    print("="*50)
    
    # Get credentials
    username = getattr(settings, 'PHONEPE_WEBHOOK_USERNAME', 'okpuja_webhook_user')
    password = getattr(settings, 'PHONEPE_WEBHOOK_PASSWORD', 'Okpuja2025')
    
    # Calculate SHA256 hash
    credentials_string = f"{username}:{password}"
    expected_hash = hashlib.sha256(credentials_string.encode('utf-8')).hexdigest()
    
    print(f"📱 Username: {username}")
    print(f"🔑 Password: {password}")
    print(f"📝 Credentials String: {credentials_string}")
    print(f"🔐 SHA256 Hash: {expected_hash}")
    
    return expected_hash

def create_test_webhook_payload(merchant_order_id):
    """Create a test webhook payload according to PhonePe V2 format"""
    return {
        "event": "checkout.order.completed",
        "payload": {
            "orderId": f"OMO{merchant_order_id[-15:]}",
            "merchantId": "M22G7HGSSB3SC",
            "merchantOrderId": merchant_order_id,
            "state": "COMPLETED",
            "amount": 80000,  # ₹800 in paisa
            "expireAt": 1724866793837,
            "metaInfo": {
                "udf1": "",
                "udf2": "",
                "udf3": "",
                "udf4": ""
            },
            "paymentDetails": [
                {
                    "paymentMode": "UPI_QR",
                    "transactionId": f"TXN{merchant_order_id[-8:]}",
                    "timestamp": 1724866793837,
                    "amount": 80000,
                    "state": "COMPLETED",
                    "splitInstruments": [
                        {
                            "amount": 80000,
                            "rail": {
                                "type": "UPI",
                                "upiTransactionId": f"upi{merchant_order_id[-6:]}",
                                "vpa": "test@ybl"
                            },
                            "instrument": {
                                "type": "ACCOUNT",
                                "accountType": "SAVINGS",
                                "accountNumber": "121212121212"
                            }
                        }
                    ]
                }
            ]
        }
    }

def test_webhook_processing():
    """Test webhook processing with actual payment order"""
    print("\n🔔 TESTING WEBHOOK PROCESSING")
    print("="*50)
    
    # Find a recent payment order with cart
    payment_order = PaymentOrder.objects.filter(
        cart_id__isnull=False,
        status__in=['INITIATED', 'PENDING']
    ).order_by('-created_at').first()
    
    if not payment_order:
        print("❌ No suitable payment order found for testing")
        return False
    
    print(f"📦 Testing with payment order: {payment_order.merchant_order_id}")
    print(f"🛒 Cart ID: {payment_order.cart_id}")
    print(f"💰 Amount: ₹{payment_order.amount}")
    print(f"📊 Current Status: {payment_order.status}")
    
    # Check if booking already exists
    try:
        cart = Cart.objects.get(cart_id=payment_order.cart_id)
        existing_booking = Booking.objects.filter(cart=cart).first()
        print(f"📋 Existing booking: {existing_booking.book_id if existing_booking else 'None'}")
    except Cart.DoesNotExist:
        print("❌ Cart not found")
        return False
    
    # Create webhook payload
    webhook_payload = create_test_webhook_payload(payment_order.merchant_order_id)
    
    # Process webhook
    from payments.services import WebhookService
    webhook_service = WebhookService()
    
    print(f"\n🔄 Processing webhook...")
    result = webhook_service.process_payment_webhook(webhook_payload)
    
    if result['success']:
        print(f"✅ Webhook processed successfully!")
        print(f"   Event: {result.get('event_type')}")
        print(f"   State: {result.get('state')}")
        
        # Check if booking was created
        payment_order.refresh_from_db()
        print(f"   Updated payment status: {payment_order.status}")
        
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"   ✅ Booking created/found: {booking.book_id}")
            print(f"   📅 Date: {booking.selected_date}")
            print(f"   ⏰ Time: {booking.selected_time}")
            print(f"   💰 Amount: ₹{booking.total_amount}")
        else:
            print(f"   ❌ No booking found after webhook processing")
        
        return True
    else:
        print(f"❌ Webhook processing failed: {result['error']}")
        return False

def test_local_webhook_endpoint():
    """Test the local webhook endpoint"""
    print("\n🌐 TESTING LOCAL WEBHOOK ENDPOINT")
    print("="*50)
    
    # Calculate auth hash
    auth_hash = test_webhook_auth()
    
    # Find a payment order to test with
    payment_order = PaymentOrder.objects.filter(
        cart_id__isnull=False,
        status__in=['INITIATED', 'PENDING']
    ).first()
    
    if not payment_order:
        print("❌ No payment order available for testing")
        return
    
    # Create webhook payload
    webhook_payload = create_test_webhook_payload(payment_order.merchant_order_id)
    
    # Prepare request
    url = "http://localhost:8000/api/payments/phonepe/callback/"
    headers = {
        'Authorization': auth_hash,
        'Content-Type': 'application/json'
    }
    
    print(f"📡 Sending webhook to: {url}")
    print(f"🔐 Auth Hash: {auth_hash}")
    print(f"📦 Order ID: {payment_order.merchant_order_id}")
    
    try:
        response = requests.post(url, json=webhook_payload, headers=headers, timeout=10)
        print(f"📊 Response Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook endpoint working!")
        else:
            print("❌ Webhook endpoint error")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to local server")
        print("💡 Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🧪 PHONEPE V2 WEBHOOK TESTING")
    print("="*50)
    
    # Test authentication
    test_webhook_auth()
    
    # Test webhook processing
    test_webhook_processing()
    
    # Test local endpoint (optional - requires server running)
    # test_local_webhook_endpoint()
    
    print("\n🎉 WEBHOOK TESTING COMPLETED!")
