#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User
from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from django.utils import timezone
import pytz

def test_new_durga_redirect():
    """Test redirect handler with the NEW Durga Puja booking"""
    print("=== TESTING NEW DURGA PUJA REDIRECT ===\n")
    
    # Get user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    print(f"👤 User: {user.email}")
    
    # Get the Durga cart from Swagger test
    durga_cart_id = "05ad3448-8faf-4101-8542-64c16cff44b2"
    
    try:
        cart = Cart.objects.get(cart_id=durga_cart_id)
        print(f"🛒 Cart: {cart.cart_id}")
        print(f"   Service: {cart.puja_service.title}")
        print(f"   Status: {cart.status}")
        
        # Get payment for this cart
        payment = PaymentOrder.objects.filter(cart_id=cart.cart_id).first()
        if payment:
            print(f"💳 Payment: {payment.merchant_order_id}")
            print(f"   Status: {payment.status}")
        else:
            print("❌ No payment found")
            return
        
        # Get booking for this cart
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"📋 Booking: {booking.book_id}")
            print(f"   Status: {booking.status}")
            
            # Convert to IST
            ist = pytz.timezone('Asia/Kolkata')
            booking_created_ist = booking.created_at.astimezone(ist)
            print(f"   Created (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            print("❌ No booking found")
            return
        
        print(f"\n=== SIMULATING REDIRECT HANDLER ===")
        
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
            
            # Check if this matches our NEW Durga booking
            if booking_id == booking.book_id:
                print(f"\n✅ SUCCESS: Redirect handler found the NEW Durga Puja booking!")
                print(f"   Frontend will now show the correct booking details")
            else:
                print(f"\n❌ ERROR: Redirect handler found different booking")
                print(f"   Expected: {booking.book_id}")
                print(f"   Found: {booking_id}")
        else:
            print(f"❌ Redirect handler failed to find booking")
        
    except Cart.DoesNotExist:
        print(f"❌ Cart {durga_cart_id} not found")

def show_all_user_bookings():
    """Show all bookings for the user to verify data"""
    print(f"\n=== ALL USER BOOKINGS (IST) ===\n")
    
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    bookings = Booking.objects.filter(user=user).order_by('-created_at')
    ist = pytz.timezone('Asia/Kolkata')
    
    for booking in bookings:
        created_ist = booking.created_at.astimezone(ist)
        service_name = "Unknown Service"
        if booking.cart and booking.cart.puja_service:
            service_name = booking.cart.puja_service.title
        
        print(f"📋 {booking.book_id} - {service_name}")
        print(f"   Status: {booking.status}")
        print(f"   Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Cart: {booking.cart.cart_id if booking.cart else 'No cart'}")
        print("")

if __name__ == "__main__":
    test_new_durga_redirect()
    show_all_user_bookings()
