#!/usr/bin/env python
"""
Test the cart payment API endpoint directly
"""
import os
import sys
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_cart_payment_api():
    """Test cart payment API endpoint"""
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        from cart.models import Cart
        from rest_framework_simplejwt.tokens import RefreshToken
        
        User = get_user_model()
        
        # Get test user
        user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        if not user:
            print("❌ Test user not found")
            return False
        
        # Get cart
        cart = Cart.objects.filter(user=user, status=Cart.StatusChoices.ACTIVE).first()
        if not cart:
            print("❌ No active cart found")
            return False
        
        print(f"✅ Testing with cart: {cart.cart_id}")
        
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Create test client
        client = Client()
        
        # Prepare request data
        request_data = {
            'cart_id': cart.cart_id,
            'redirect_url': 'http://localhost:3000/confirmbooking'
        }
        
        # Make API request
        response = client.post(
            '/api/payments/cart/',
            data=json.dumps(request_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.content.decode()}")
        
        if response.status_code == 201:
            response_data = response.json()
            print("✅ API call successful!")
            print(f"Payment Order ID: {response_data['data']['payment_order']['id']}")
            return True
        else:
            print("❌ API call failed!")
            if response.status_code == 500:
                print("Internal server error - check Django logs")
            return False
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔗 Testing Cart Payment API Endpoint\n")
    success = test_cart_payment_api()
    
    if success:
        print("\n🎉 API test passed!")
    else:
        print("\n❌ API test failed!")
