#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

import requests
import json
from django.conf import settings

def test_complete_durga_flow():
    """Test complete flow: Login → Cart → Payment → Redirect with NEW booking"""
    
    base_url = "http://127.0.0.1:8000/api"
    
    print("=== TESTING COMPLETE DURGA PUJA FLOW ===\n")
    
    # Step 1: Login
    print("🔐 Step 1: Login")
    login_data = {
        "email": "asliprinceraj@gmail.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{base_url}/auth/login/", json=login_data)
    if response.status_code == 200:
        auth_data = response.json()
        token = auth_data['access']
        print(f"✅ Login successful")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    else:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    # Step 2: Create NEW Cart
    print(f"\n💰 Step 2: Create NEW Cart (Different service)")
    cart_data = {
        "service_type": "PUJA",
        "puja_service": 13,  # Durga Puja
        "package_id": 11,    # Basic package
        "selected_date": "2025-09-20",  # Different date
        "selected_time": "10:00"        # Different time
    }
    
    response = requests.post(f"{base_url}/cart/carts/", json=cart_data, headers=headers)
    if response.status_code == 201:
        cart_response = response.json()
        new_cart_id = cart_response['cart_id']
        print(f"✅ New cart created: {new_cart_id}")
        print(f"   Service: {cart_response['puja_service']['title']}")
        print(f"   Date: {cart_response['selected_date']}")
        print(f"   Time: {cart_response['selected_time']}")
        print(f"   Price: ₹{cart_response['total_price']}")
    else:
        print(f"❌ Cart creation failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 3: Create Payment
    print(f"\n💳 Step 3: Create Payment for NEW Cart")
    payment_data = {
        "cart_id": new_cart_id
    }
    
    response = requests.post(f"{base_url}/payments/cart/", json=payment_data, headers=headers)
    if response.status_code == 201:
        payment_response = response.json()
        payment_url = payment_response['data']['payment_order']['phonepe_payment_url']
        order_id = payment_response['data']['payment_order']['merchant_order_id']
        
        print(f"✅ Payment created: {order_id}")
        print(f"   PhonePe URL: {payment_url}")
    else:
        print(f"❌ Payment creation failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 4: Simulate Payment Success and Redirect
    print(f"\n🔄 Step 4: Simulate Payment Success")
    
    # Import Django models to mark payment as successful
    from payments.models import PaymentOrder
    from booking.models import Booking
    from cart.models import Cart
    from payments.services import WebhookService
    
    # Get the payment and mark as successful
    payment = PaymentOrder.objects.get(merchant_order_id=order_id)
    print(f"   Payment status before: {payment.status}")
    
    # Mark as successful
    payment.mark_success(
        phonepe_transaction_id=f'TXN_NEW_DURGA_{order_id[-8:]}',
        phonepe_response={
            'success': True,
            'code': 'PAYMENT_SUCCESS',
            'message': 'Your payment is successful.',
            'data': {
                'merchantTransactionId': order_id,
                'transactionId': f'TXN_NEW_DURGA_{order_id[-8:]}',
                'amount': int(payment.amount * 100),
                'state': 'COMPLETED',
                'responseCode': 'SUCCESS'
            }
        }
    )
    
    print(f"   Payment status after: {payment.status}")
    
    # Create booking via webhook service
    webhook_service = WebhookService()
    booking = webhook_service._create_booking_from_cart(payment)
    
    if booking:
        print(f"✅ Booking created: {booking.book_id}")
        
        # Test redirect handler
        print(f"\n🌐 Step 5: Test Redirect Handler")
        
        from payments.simple_redirect_handler import SimplePaymentRedirectHandler
        from accounts.models import User
        
        # Create mock request
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.GET = {}
        
        user = User.objects.get(email='asliprinceraj@gmail.com')
        mock_request = MockRequest(user)
        handler = SimplePaymentRedirectHandler()
        
        # Test redirect logic
        booking_id, found_order_id = handler._find_user_latest_booking(user)
        
        if booking_id and found_order_id:
            print(f"✅ Redirect handler found:")
            print(f"   Booking ID: {booking_id}")
            print(f"   Order ID: {found_order_id}")
            
            # Check if it's the NEW booking
            if booking_id == booking.book_id and found_order_id == order_id:
                print(f"\n🎉 SUCCESS! Frontend will receive NEW booking:")
                
                redirect_url = f"http://localhost:3000/confirmbooking?book_id={booking_id}&order_id={found_order_id}&redirect_source=phonepe"
                print(f"   {redirect_url}")
                
                print(f"\n📋 NEW Booking Details:")
                print(f"   ID: {booking.book_id}")
                print(f"   Service: {booking.cart.puja_service.title}")
                print(f"   Date: {booking.cart.selected_date}")
                print(f"   Time: {booking.cart.selected_time}")
                print(f"   Status: {booking.status}")
                
            else:
                print(f"❌ Redirect handler found wrong booking")
                print(f"   Expected: {booking.book_id}")
                print(f"   Found: {booking_id}")
        else:
            print(f"❌ Redirect handler failed")
    
    else:
        print(f"❌ Booking creation failed")

def test_booking_api():
    """Test the booking API endpoint"""
    print(f"\n=== TESTING BOOKING API ===\n")
    
    # Get the latest Durga booking
    from booking.models import Booking
    from accounts.models import User
    
    user = User.objects.get(email='asliprinceraj@gmail.com')
    latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
    
    if latest_booking:
        print(f"📋 Testing with booking: {latest_booking.book_id}")
        
        # Test API endpoint
        api_url = f"http://127.0.0.1:8000/api/booking/bookings/by-id/{latest_booking.book_id}/"
        
        response = requests.get(api_url)
        if response.status_code == 200:
            booking_data = response.json()
            print(f"✅ API response successful")
            print(f"   Booking ID: {booking_data.get('book_id')}")
            print(f"   Status: {booking_data.get('status')}")
            print(f"   Total: ₹{booking_data.get('total_amount', 'N/A')}")
        else:
            print(f"❌ API failed: {response.status_code}")

if __name__ == "__main__":
    test_complete_durga_flow()
    test_booking_api()
