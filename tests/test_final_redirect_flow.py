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
from cart.models import Cart
from booking.models import Booking
from accounts.models import User

def test_complete_redirect_flow():
    """Test the complete redirect flow with proper URLs"""
    print("=== TESTING COMPLETE REDIRECT FLOW ===\n")
    
    # 1. Create a test cart payment
    print("1. Creating test cart payment...")
    
    # Find a user and create test data if needed
    user = User.objects.first()
    if not user:
        print("❌ No users found. Create a user first.")
        return
    
    # Create test cart payment via API
    cart_payment_url = "http://127.0.0.1:8000/api/payments/cart/"
    
    # Find an active cart
    cart = Cart.objects.filter(user=user, status='ACTIVE').first()
    if not cart:
        print("❌ No active cart found for user. Create a cart first.")
        return
    
    cart_data = {
        'cart_id': str(cart.cart_id)
    }
    
    print(f"   Cart ID: {cart.cart_id}")
    print(f"   Cart total: ₹{cart.total_price}")
    
    try:
        # Create payment (this should now use the redirect handler URL)
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        client = Client()
        client.force_login(user)
        
        response = client.post('/api/payments/cart/', cart_data, content_type='application/json')
        response_data = response.json()
        
        if response_data.get('success'):
            payment_url = response_data['data']['payment_url']
            merchant_order_id = response_data['data']['payment_order']['merchant_order_id']
            
            print(f"   ✅ Payment created: {merchant_order_id}")
            print(f"   ✅ Payment URL generated")
            
            # Check the redirect URL in the payment order
            payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
            print(f"   ✅ Redirect URL in payment: {payment_order.redirect_url}")
            
            return payment_order
        else:
            print(f"   ❌ Payment creation failed: {response_data}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error creating payment: {e}")
        return None

def test_webhook_and_redirect():
    """Test webhook processing and redirect"""
    print(f"\n2. Testing webhook and redirect...")
    
    # Find a recent payment
    payment = PaymentOrder.objects.filter(cart_id__isnull=False).order_by('-created_at').first()
    if not payment:
        print("   ❌ No payments found to test")
        return
    
    print(f"   Testing with payment: {payment.merchant_order_id}")
    
    # Simulate webhook
    webhook_data = {
        'merchantOrderId': payment.merchant_order_id,
        'state': 'COMPLETED',
        'transactionId': f'TXN_{payment.merchant_order_id}',
        'amount': int(payment.amount * 100),
        'responseCode': 'SUCCESS'
    }
    
    webhook_url = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"
    
    try:
        response = requests.post(webhook_url, json=webhook_data)
        if response.status_code == 200:
            print(f"   ✅ Webhook processed successfully")
            
            # Check if booking was created
            if payment.cart_id:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                if booking:
                    print(f"   ✅ Booking created: {booking.book_id}")
                    return booking
                else:
                    print(f"   ❌ No booking created by webhook")
        else:
            print(f"   ❌ Webhook failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to webhook. Make sure Django server is running.")
    except Exception as e:
        print(f"   ❌ Webhook error: {e}")
    
    return None

def test_redirect_handler():
    """Test the redirect handler directly"""
    print(f"\n3. Testing redirect handler...")
    
    # Find a successful payment with booking
    successful_payment = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).first()
    
    if not successful_payment:
        print("   ❌ No successful payments found")
        return
    
    # Test redirect handler
    redirect_url = f"http://127.0.0.1:8000/api/payments/redirect/?merchantOrderId={successful_payment.merchant_order_id}"
    
    try:
        response = requests.get(redirect_url, allow_redirects=False)
        
        if response.status_code in [302, 301]:  # Redirect status codes
            redirect_location = response.headers.get('Location', '')
            print(f"   ✅ Redirect handler working")
            print(f"   ✅ Redirect location: {redirect_location}")
            
            # Check if book_id is in the redirect URL
            if 'book_id=' in redirect_location:
                print(f"   ✅ book_id parameter found in redirect URL")
            else:
                print(f"   ❌ book_id parameter missing from redirect URL")
                
        else:
            print(f"   ❌ Redirect handler failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to redirect handler. Make sure Django server is running.")
    except Exception as e:
        print(f"   ❌ Redirect handler error: {e}")

def show_final_status():
    """Show final status and URLs"""
    print(f"\n=== FINAL STATUS ===")
    
    # Show recent successful payments with bookings
    recent_payments = PaymentOrder.objects.filter(
        status='SUCCESS',
        cart_id__isnull=False
    ).order_by('-created_at')[:3]
    
    print(f"Recent successful cart payments:")
    for payment in recent_payments:
        try:
            cart = Cart.objects.get(cart_id=payment.cart_id)
            booking = Booking.objects.filter(cart=cart).first()
            
            print(f"\n  Payment: {payment.merchant_order_id}")
            print(f"  Status: {payment.status}")
            print(f"  Cart: {cart.status}")
            print(f"  Booking: {'YES' if booking else 'NO'}")
            
            if booking:
                final_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}"
                print(f"  ✅ Final redirect URL: {final_url}")
            else:
                print(f"  ❌ No booking - redirect will be: http://localhost:3000/confirmbooking")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n🎯 KEY POINTS:")
    print(f"  1. Payment redirect_url should be: http://localhost:8000/api/payments/redirect/")
    print(f"  2. PhonePe webhook URL should be: http://localhost:8000/api/payments/webhook/phonepe/")
    print(f"  3. Final user redirect should be: http://localhost:3000/confirmbooking?book_id=BK-XXX")
    print(f"  4. Make sure to configure these URLs in your PhonePe merchant dashboard")

if __name__ == "__main__":
    payment = test_complete_redirect_flow()
    booking = test_webhook_and_redirect()
    test_redirect_handler()
    show_final_status()
