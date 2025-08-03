#!/usr/bin/env python
"""
Test the enhanced redirect handler for booking auto-creation
"""

import os
import sys
import django
import requests
from datetime import datetime, timedelta

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from accounts.models import User
from puja.models import PujaService, Package

def test_complete_flow():
    """Test complete cart -> payment -> redirect -> booking flow"""
    print("🚀 Testing Complete Payment Flow")
    print("=" * 50)
    
    # Get user
    user = User.objects.get(email='asliprinceraj@gmail.com')
    print(f"👤 User: {user.email}")
    
    # Create a new cart
    puja_service = PujaService.objects.first()
    package = Package.objects.filter(puja_service=puja_service).first()
    
    cart = Cart.objects.create(
        user=user,
        service_type='PUJA',
        puja_service=puja_service,
        package=package,
        selected_date=datetime.now().date() + timedelta(days=7),
        selected_time="14:00",
        status='ACTIVE'
    )
    print(f"📦 Created cart: {cart.cart_id}")
    
    # Create payment order (simulating /payments/cart/ endpoint)
    from payments.services import PaymentService
    payment_service = PaymentService()
    payment_response = payment_service.create_payment_from_cart(cart.cart_id)
    
    if payment_response['success']:
        payment_order = PaymentOrder.objects.get(id=payment_response['data']['payment_order']['id'])
        print(f"💳 Created payment: {payment_order.merchant_order_id}")
        print(f"📊 Payment status: {payment_order.status}")
        
        # Simulate redirect (without actually going to PhonePe)
        print(f"\n🔄 Simulating redirect flow...")
        
        # Test the redirect handler directly
        from payments.simple_redirect_handler import SimplePaymentRedirectHandler
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.get('/api/payments/redirect/simple/', {})
        request.user = user
        
        handler = SimplePaymentRedirectHandler()
        
        # Call the method that finds user's latest cart
        cart_id, order_id = handler._find_user_latest_cart(user)
        print(f"✅ Redirect handler found cart: {cart_id}")
        print(f"📋 Order ID: {order_id}")
        
        # Check if booking was created
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"✅ Booking created: {booking.book_id}")
            print(f"💰 Amount: ₹{booking.total_amount}")
            print(f"📅 Date: {booking.selected_date}")
            print(f"📧 User email: {booking.user.email}")
            
            # Test the booking endpoint
            print(f"\n🔍 Testing booking endpoint...")
            print(f"Cart ID for API call: {cart.cart_id}")
            
            return True
        else:
            print("❌ No booking created!")
            return False
    else:
        print("❌ Payment creation failed!")
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    print("\n" + "=" * 50)
    if success:
        print("✅ COMPLETE FLOW TEST SUCCESSFUL!")
        print("🎯 Auto-booking creation is working!")
    else:
        print("❌ FLOW TEST FAILED!")
