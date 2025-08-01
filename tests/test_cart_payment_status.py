#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from accounts.models import User
from cart.models import Cart
from rest_framework_simplejwt.tokens import RefreshToken

def test_cart_payment_status():
    """Test cart payment status endpoint"""
    
    try:
        # Get test user
        user = User.objects.get(email="asliprinceraj@gmail.com")
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Get user's cart
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            print("❌ No cart found for user")
            return False
            
        print(f"✅ Testing cart payment status for cart: {cart.cart_id}")
        
        # Test status API call
        base_url = "http://127.0.0.1:8000"
        endpoint = f"{base_url}/api/payments/cart/status/{cart.cart_id}/"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"\n🔍 Testing status API call...")
        print(f"URL: {endpoint}")
        
        response = requests.get(endpoint, headers=headers, timeout=30)
        
        print(f"\n📤 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response: {json.dumps(data, indent=2)}")
            
            # Check if booking was created
            payment_data = data.get('data', {})
            if payment_data.get('payment_status') == 'SUCCESS':
                if payment_data.get('booking_created'):
                    print(f"🎉 Booking automatically created: {payment_data.get('booking_id')}")
                else:
                    print("⚠️ Payment successful but booking not created")
            else:
                print(f"ℹ️ Payment status: {payment_data.get('payment_status')}")
                
            return True
        else:
            print(f"❌ Error {response.status_code}")
            print(f"📤 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Cart Payment Status API...")
    success = test_cart_payment_status()
    
    if success:
        print("\n✅ Cart payment status test passed!")
    else:
        print("\n❌ Cart payment status test failed!")
