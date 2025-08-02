#!/usr/bin/env python
"""
Test redirect handler with INITIATED payment
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_redirect_handler():
    """Test redirect handler with simulated request"""
    print("🔄 Testing Redirect Handler")
    print("=" * 40)
    
    from payments.simple_redirect_handler import SimplePaymentRedirectHandler
    from django.test import RequestFactory
    from accounts.models import User
    from payments.models import PaymentOrder
    from booking.models import Booking
    
    # Get user and payment
    user = User.objects.get(email='asliprinceraj@gmail.com')
    cart_id = '82c841e4-60c0-440d-9854-3eec8042aff0'
    
    payment = PaymentOrder.objects.filter(cart_id=cart_id).first()
    print(f"💳 Payment status: {payment.status}")
    
    # Check current booking status
    booking = Booking.objects.filter(cart__cart_id=cart_id).first()
    print(f"📦 Booking exists: {booking.book_id if booking else 'NO'}")
    
    # Create simulated request
    factory = RequestFactory()
    request = factory.get('/api/payments/redirect/simple/', {})
    request.user = user
    
    # Test the redirect handler
    handler = SimplePaymentRedirectHandler()
    
    print(f"\n🔍 Testing _find_user_latest_cart method...")
    cart_id_result, order_id_result = handler._find_user_latest_cart(user, request)
    
    print(f"✅ Returned cart_id: {cart_id_result}")
    print(f"📋 Returned order_id: {order_id_result}")
    
    # Check if booking was created
    payment.refresh_from_db()
    booking = Booking.objects.filter(cart__cart_id=cart_id).first()
    
    print(f"\n📊 Final Results:")
    print(f"💳 Payment status: {payment.status}")
    print(f"📦 Booking created: {booking.book_id if booking else 'NO'}")
    
    if booking:
        print(f"👤 Booking user: {booking.user.email}")
        print(f"💰 Amount: ₹{booking.total_amount}")
        print(f"📅 Date: {booking.selected_date}")
        print(f"🕐 Time: {booking.selected_time}")
        
        # Test the booking endpoint
        print(f"\n🌐 Booking API endpoint should now work:")
        print(f"GET /api/booking/bookings/by-cart/{cart_id}/")
        
        return True
    
    return False

if __name__ == "__main__":
    success = test_redirect_handler()
    print("\n" + "=" * 40)
    if success:
        print("✅ REDIRECT HANDLER TEST SUCCESSFUL!")
        print("🎯 Auto-booking creation is working!")
        print("📧 Email notifications should be sent!")
    else:
        print("❌ REDIRECT HANDLER TEST FAILED!")
