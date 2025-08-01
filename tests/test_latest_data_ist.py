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
import pytz

def test_latest_booking_redirect():
    """Test redirect handler with the LATEST booking"""
    print("=== TESTING LATEST BOOKING REDIRECT ===\n")
    
    # Get user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    print(f"👤 User: {user.email}")
    
    # Get the latest cart and booking
    latest_cart_id = "d3417c2a-d644-427b-bf3d-8794f7d178fe"
    
    try:
        cart = Cart.objects.get(cart_id=latest_cart_id)
        print(f"🛒 Latest Cart: {cart.cart_id}")
        print(f"   Service: {cart.puja_service.title}")
        print(f"   Status: {cart.status}")
        print(f"   Date: {cart.selected_date}")
        print(f"   Time: {cart.selected_time}")
        
        # Get payment
        payment = PaymentOrder.objects.filter(cart_id=cart.cart_id).first()
        if payment:
            print(f"💳 Payment: {payment.merchant_order_id}")
            print(f"   Status: {payment.status}")
        
        # Get booking
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"📋 Booking: {booking.book_id}")
            print(f"   Status: {booking.status}")
            
            # Convert to IST
            ist = pytz.timezone('Asia/Kolkata')
            booking_created_ist = booking.created_at.astimezone(ist)
            print(f"   Created (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        print(f"\n=== TESTING REDIRECT HANDLER ===")
        
        # Import the redirect handler logic
        from payments.simple_redirect_handler import SimplePaymentRedirectHandler
        
        # Create a mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.GET = {}
        
        mock_request = MockRequest(user)
        handler = SimplePaymentRedirectHandler()
        
        # Test the redirect logic
        booking_id, order_id = handler._find_user_latest_booking(user)
        
        if booking_id and order_id:
            print(f"✅ Redirect handler found:")
            print(f"   Booking ID: {booking_id}")
            print(f"   Order ID: {order_id}")
            
            expected_url = f"http://localhost:3000/confirmbooking?book_id={booking_id}&order_id={order_id}&redirect_source=phonepe"
            print(f"\n🌐 Expected redirect URL:")
            print(f"   {expected_url}")
            
            # Check if this matches our LATEST booking
            if booking and booking_id == booking.book_id:
                print(f"\n✅ SUCCESS: Redirect handler found the LATEST booking!")
                print(f"   Booking matches latest cart data")
                print(f"   Service: {cart.puja_service.title}")
                print(f"   Date: {cart.selected_date} {cart.selected_time}")
            else:
                print(f"\n❌ ERROR: Redirect handler found different booking")
                if booking:
                    print(f"   Expected: {booking.book_id}")
                print(f"   Found: {booking_id}")
        else:
            print(f"❌ Redirect handler failed to find booking")
        
    except Cart.DoesNotExist:
        print(f"❌ Cart {latest_cart_id} not found")

def test_booking_api_with_auth():
    """Test booking API with authentication"""
    print(f"\n=== TESTING BOOKING API WITH AUTH ===\n")
    
    import requests
    
    # Login first to get token
    login_data = {
        "email": "asliprinceraj@gmail.com",
        "password": "testpass123"
    }
    
    login_response = requests.post("http://127.0.0.1:8000/api/auth/login/", json=login_data)
    if login_response.status_code == 200:
        auth_data = login_response.json()
        token = auth_data['access']
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get latest booking
        from booking.models import Booking
        user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
        
        if latest_booking:
            print(f"📋 Testing API with booking: {latest_booking.book_id}")
            
            api_url = f"http://127.0.0.1:8000/api/booking/bookings/by-id/{latest_booking.book_id}/"
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                booking_data = response.json()
                print(f"✅ API response successful")
                print(f"   Booking ID: {booking_data.get('book_id')}")
                print(f"   Status: {booking_data.get('status')}")
                print(f"   Service: {booking_data.get('service_name', 'N/A')}")
                print(f"   Total: ₹{booking_data.get('total_amount', 'N/A')}")
                
                # Show what frontend will receive
                print(f"\n📱 Frontend will receive:")
                print(f"   {response.json()}")
            else:
                print(f"❌ API failed: {response.status_code}")
                print(f"   Response: {response.text}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")

def show_latest_user_data():
    """Show latest user data in IST"""
    print(f"\n=== LATEST USER DATA (IST) ===\n")
    
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    # Latest cart
    latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
    if latest_cart:
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = latest_cart.created_at.astimezone(ist)
        
        print(f"🛒 LATEST CART:")
        print(f"   ID: {latest_cart.cart_id}")
        print(f"   Service: {latest_cart.puja_service.title}")
        print(f"   Date: {latest_cart.selected_date} {latest_cart.selected_time}")
        print(f"   Status: {latest_cart.status}")
        print(f"   Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Latest booking
    latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
    if latest_booking:
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = latest_booking.created_at.astimezone(ist)
        
        service_name = "Unknown Service"
        if latest_booking.cart and latest_booking.cart.puja_service:
            service_name = latest_booking.cart.puja_service.title
        
        print(f"\n📋 LATEST BOOKING:")
        print(f"   ID: {latest_booking.book_id}")
        print(f"   Service: {service_name}")
        print(f"   Status: {latest_booking.status}")
        print(f"   Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Check if latest cart and booking match
        if latest_cart and latest_booking.cart and latest_booking.cart.cart_id == latest_cart.cart_id:
            print(f"   ✅ Matches latest cart - Real-time data!")
        else:
            print(f"   ⚠️ Does not match latest cart")

if __name__ == "__main__":
    show_latest_user_data()
    test_latest_booking_redirect()
    test_booking_api_with_auth()
