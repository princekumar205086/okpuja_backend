#!/usr/bin/env python3
"""
Test Payment Initiation API - Fix the UserAddress import issue
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

# Override ALLOWED_HOSTS for testing
from django.conf import settings
settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

from accounts.models import User, Address
from cart.models import Cart
from django.test import Client
from django.contrib.auth import get_user_model
import json

def test_payment_initiation_api():
    """Test the actual payment API endpoint"""
    
    print("🔍 Testing Payment Initiation API")
    print("=" * 50)
    
    # Get test user
    try:
        user = User.objects.get(email='asliprinceraj@gmail.com')
        print(f"✅ User: {user.email}")
    except User.DoesNotExist:
        print("❌ User not found")
        return
    
    # Get user's address
    address = Address.objects.filter(user=user).first()
    if not address:
        print("❌ No address found")
        return
    print(f"✅ Address: {address.id} - {address.city}")
    
    # Get user's cart
    cart = Cart.objects.filter(user=user, status='ACTIVE').first()
    if not cart:
        print("❌ No active cart found")
        return
    print(f"✅ Cart: {cart.id}")
    
    # Test API call
    client = Client()
    
    # Login user (simulate authentication)
    client.force_login(user)
    
    # Make payment initiation request
    print(f"\n💳 Testing Payment API...")
    print(f"POST /api/payments/cart/")
    print(f"Data: cart_id={cart.id}, address_id={address.id}")
    
    response = client.post('/api/payments/cart/', {
        'cart_id': cart.id,
        'address_id': address.id
    }, content_type='application/json')
    
    print(f"Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        
        if response_data.get('success'):
            print("✅ Payment initiation successful!")
            if 'payment_order' in response_data:
                payment_order = response_data['payment_order']
                print(f"✅ Payment Order ID: {payment_order.get('id', 'N/A')}")
        else:
            print(f"❌ Payment initiation failed: {response_data.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Failed to parse response: {e}")
        print(f"Raw response: {response.content}")

if __name__ == "__main__":
    test_payment_initiation_api()
