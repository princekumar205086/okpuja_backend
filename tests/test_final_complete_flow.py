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
import pytz

def test_complete_flow_with_cleanup():
    """Test complete flow including automatic cart cleanup"""
    
    base_url = "http://127.0.0.1:8000/api"
    
    print("=== TESTING COMPLETE FLOW WITH AUTO-CLEANUP ===\n")
    
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
    print(f"\n💰 Step 2: Create FINAL TEST Cart")
    cart_data = {
        "service_type": "PUJA",
        "puja_service": 13,  # Durga Puja
        "package_id": 11,    # Basic package
        "selected_date": "2025-10-01",  # Final test date
        "selected_time": "15:30"        # Final test time
    }
    
    response = requests.post(f"{base_url}/cart/carts/", json=cart_data, headers=headers)
    if response.status_code == 201:
        cart_response = response.json()
        final_cart_id = cart_response['cart_id']
        print(f"✅ Final test cart created: {final_cart_id}")
        print(f"   Service: {cart_response['puja_service']['title']}")
        print(f"   Date: {cart_response['selected_date']}")
        print(f"   Time: {cart_response['selected_time']}")
        print(f"   Price: ₹{cart_response['total_price']}")
        
        # Show IST creation time
        ist = pytz.timezone('Asia/Kolkata')
        created_utc = cart_response['created_at']
        print(f"   Created (IST): {created_utc}")
    else:
        print(f"❌ Cart creation failed: {response.status_code}")
        return
    
    # Step 3: Create Payment
    print(f"\n💳 Step 3: Create Payment for Final Cart")
    payment_data = {
        "cart_id": final_cart_id
    }
    
    response = requests.post(f"{base_url}/payments/cart/", json=payment_data, headers=headers)
    if response.status_code == 201:
        payment_response = response.json()
        order_id = payment_response['data']['payment_order']['merchant_order_id']
        
        print(f"✅ Payment created: {order_id}")
        print(f"   Status: {payment_response['data']['payment_order']['status']}")
    else:
        print(f"❌ Payment creation failed: {response.status_code}")
        return
    
    # Step 4: Simulate Payment Success and Booking Creation
    print(f"\n🔄 Step 4: Simulate Payment Success & Booking Creation")
    
    from payments.models import PaymentOrder
    from booking.models import Booking
    from cart.models import Cart
    from payments.services import WebhookService
    from accounts.models import User
    
    # Get the payment and mark as successful
    payment = PaymentOrder.objects.get(merchant_order_id=order_id)
    print(f"   Payment status before: {payment.status}")
    
    # Mark as successful
    payment.mark_success(
        phonepe_transaction_id=f'TXN_FINAL_{order_id[-8:]}',
        phonepe_response={
            'success': True,
            'code': 'PAYMENT_SUCCESS',
            'message': 'Your payment is successful.',
            'data': {
                'merchantTransactionId': order_id,
                'transactionId': f'TXN_FINAL_{order_id[-8:]}',
                'amount': int(payment.amount * 100),
                'state': 'COMPLETED',
                'responseCode': 'SUCCESS'
            }
        }
    )
    
    print(f"   Payment status after: {payment.status}")
    
    # Create booking via webhook service (this will auto-cleanup old carts)
    webhook_service = WebhookService()
    booking = webhook_service._create_booking_from_cart(payment)
    
    if booking:
        print(f"✅ Booking created: {booking.book_id}")
        
        # Show IST creation time
        ist = pytz.timezone('Asia/Kolkata')
        booking_created_ist = booking.created_at.astimezone(ist)
        print(f"   Created (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Test redirect handler
        print(f"\n🌐 Step 5: Test Final Redirect")
        
        from payments.simple_redirect_handler import SimplePaymentRedirectHandler
        
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
            
            # Check if it's the FINAL booking
            if booking_id == booking.book_id and found_order_id == order_id:
                print(f"\n🎉 SUCCESS! Frontend will receive FINAL booking:")
                
                redirect_url = f"http://localhost:3000/confirmbooking?book_id={booking_id}&order_id={found_order_id}&redirect_source=phonepe"
                print(f"   {redirect_url}")
                
                # Test booking API
                print(f"\n📡 Step 6: Test Booking API")
                api_url = f"http://127.0.0.1:8000/api/booking/bookings/by-id/{booking.book_id}/"
                
                response = requests.get(api_url, headers=headers)
                if response.status_code == 200:
                    booking_data = response.json()
                    print(f"✅ Booking API working")
                    print(f"   Service: {booking_data['data']['cart']['puja_service']['title']}")
                    print(f"   Date: {booking_data['data']['selected_date']}")
                    print(f"   Time: {booking_data['data']['selected_time']}")
                    print(f"   Status: {booking_data['data']['status']}")
                    print(f"   Total: ₹{booking_data['data']['total_amount']}")
                else:
                    print(f"❌ Booking API failed: {response.status_code}")
                
                print(f"\n📊 Step 7: Show Current Database State")
                show_final_state(user)
                
            else:
                print(f"❌ Redirect handler found wrong booking")
        else:
            print(f"❌ Redirect handler failed")
    
    else:
        print(f"❌ Booking creation failed")

def show_final_state(user):
    """Show final state of database"""
    from cart.models import Cart
    from booking.models import Booking
    import pytz
    
    ist = pytz.timezone('Asia/Kolkata')
    
    # Active carts
    active_carts = Cart.objects.filter(user=user, status='ACTIVE').count()
    converted_carts = Cart.objects.filter(user=user, status='CONVERTED').count()
    
    print(f"   📦 User Carts: {active_carts} ACTIVE, {converted_carts} CONVERTED")
    
    # Latest booking
    latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
    if latest_booking:
        created_ist = latest_booking.created_at.astimezone(ist)
        service_name = "Unknown Service"
        if latest_booking.cart and latest_booking.cart.puja_service:
            service_name = latest_booking.cart.puja_service.title
        
        print(f"   📋 Latest Booking: {latest_booking.book_id}")
        print(f"      Service: {service_name}")
        print(f"      Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"      Status: {latest_booking.status}")
    
    # Total bookings
    total_bookings = Booking.objects.filter(user=user).count()
    print(f"   📈 Total Bookings: {total_bookings}")

if __name__ == "__main__":
    test_complete_flow_with_cleanup()
