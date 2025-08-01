#!/usr/bin/env python
"""
Test Cart Payment API with correct cart_id (UUID)
"""
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

def test_corrected_cart_payment():
    """Test cart payment with correct cart_id UUID"""
    
    try:
        # Get test user
        user = User.objects.get(email="asliprinceraj@gmail.com")
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Get user's active cart
        cart = Cart.objects.filter(user=user, status=Cart.StatusChoices.ACTIVE).first()
        if not cart:
            print("❌ No active cart found for user")
            return False
            
        print(f"✅ Found active cart:")
        print(f"   Database ID: {cart.id}")
        print(f"   Cart ID (UUID): {cart.cart_id}")
        print(f"   Total: ₹{cart.total_price}")
        
        # Test payment API with correct cart_id
        base_url = "http://127.0.0.1:8000"
        endpoint = f"{base_url}/api/payments/cart/"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Use the cart_id UUID field, not the database ID
        payload = {
            'cart_id': cart.cart_id  # This is the correct field!
        }
        
        print(f"\\n🔍 Testing payment API...")
        print(f"URL: {endpoint}")
        print(f"Payload: {payload}")
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        print(f"\\n📤 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Success! Payment created/found:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Cart Payment API with Correct cart_id...")
    success = test_corrected_cart_payment()
    
    if success:
        print("\\n✅ Cart payment API test passed!")
    else:
        print("\\n❌ Cart payment API test failed!")
