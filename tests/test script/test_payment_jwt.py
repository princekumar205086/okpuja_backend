#!/usr/bin/env python3
"""
Test the payment endpoint using the Django test client with proper JWT auth
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from django.test import Client
from accounts.models import User, Address
from cart.models import Cart
import json
from rest_framework_simplejwt.tokens import RefreshToken

def test_payment_with_jwt():
    print("🔍 Testing Payment API with JWT Authentication")
    print("=" * 50)
    
    # Get test data
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ Test user not found")
        return
    
    address = Address.objects.filter(user=user).first()
    if not address:
        print("❌ No address found for user")
        return
    
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        print("❌ No cart found for user")
        return
    
    print(f"✅ User: {user.email}")
    print(f"✅ Address: {address.id} - {address.city}")
    print(f"✅ Cart: {cart.id}")
    
    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    # Test with REST client
    client = Client()
    
    # Make authenticated request
    response = client.post('/api/payments/cart/', 
        data=json.dumps({
            'cart_id': cart.id,
            'address_id': address.id
        }),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {access_token}'
    )
    
    print(f"\n💳 Payment API Request:")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print("✅ Payment API Success!")
            print(f"Payment URL: {result.get('payment_url', 'N/A')}")
            print(f"Success: {result.get('success', False)}")
        except:
            print("Response content:", response.content.decode())
    elif response.status_code == 401:
        print("❌ Authentication failed")
    elif response.status_code == 400:
        try:
            result = response.json()
            print(f"❌ Bad Request: {result}")
        except:
            print("❌ Bad Request - Raw response:", response.content.decode())
    else:
        print(f"❌ Failed with status {response.status_code}")
        print("Response:", response.content.decode()[:200])

if __name__ == "__main__":
    test_payment_with_jwt()
