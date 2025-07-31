#!/usr/bin/env python
"""
Production Payment Test with Manual Amount
Test payment initiation by creating payment directly with amount
"""
import requests
import json
from datetime import datetime, timedelta

# Production API Configuration
PRODUCTION_BASE_URL = 'https://api.okpuja.com/api'

# Test User Credentials
TEST_EMAIL = 'asliprinceraj@gmail.com'
TEST_PASSWORD = 'testpass123'

def get_access_token():
    """Get JWT access token for authentication"""
    response = requests.post(f'{PRODUCTION_BASE_URL}/auth/login/', {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        return data.get('access')
    return None

def create_direct_payment(token):
    """Create payment directly with amount instead of cart"""
    print("💳 Creating payment directly with amount...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    payment_data = {
        'amount': 500.00,  # Test with ₹500
        'currency': 'INR',
        'method': 'PHONEPE',
        'description': 'Test payment for Ganesh Puja'
    }
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/', 
                           json=payment_data, 
                           headers=headers)
    
    print(f"Payment Response Status: {response.status_code}")
    print(f"Payment Response: {response.text}")
    
    if response.status_code == 201:
        payment = response.json()
        return payment
    return None

def test_phonepe_gateway_directly():
    """Test PhonePe gateway configuration by checking if it's loading correctly"""
    print("⚙️ Testing PhonePe gateway configuration...")
    
    # This would test our gateway implementation directly
    # but from production we can only test through the API
    
    # Let's check if there are any settings endpoints
    response = requests.get(f'{PRODUCTION_BASE_URL}/payments/methods/')
    
    print(f"Payment Methods Response: {response.status_code}")
    if response.status_code == 200:
        print(f"Available methods: {response.json()}")

def create_cart_and_force_amount(token):
    """Create cart and then manually update the payment amount"""
    print("🛒 Creating cart first...")
    
    headers = {'Authorization': f'Bearer {token}'}
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Create cart with any service
    cart_data = {
        'puja_service': 8,
        'package': 2,  # Try package 2 (₹5000)
        'quantity': 1,
        'selected_date': tomorrow,
        'selected_time': '10:00:00',
        'special_instructions': 'Test booking - forced amount'
    }
    
    response = requests.post(f'{PRODUCTION_BASE_URL}/cart/carts/', 
                           json=cart_data, 
                           headers=headers)
    
    if response.status_code == 201:
        cart = response.json()
        cart_id = cart['id']
        print(f"✅ Cart created: ID={cart_id}, Total=₹{cart.get('total_amount', 0)}")
        
        # Now try to create payment with process-cart but see full error
        print("💳 Attempting payment with detailed error tracking...")
        
        payment_data = {
            'cart_id': cart_id,
            'address_id': 1,
            'method': 'PHONEPE'
        }
        
        response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/process-cart/', 
                               json=payment_data, 
                               headers=headers)
        
        print(f"Payment Status: {response.status_code}")
        print(f"Payment Headers: {dict(response.headers)}")
        print(f"Payment Response: {response.text}")
        
        # If it's a validation error, let's try to modify the request
        if response.status_code == 400 and 'min_value' in response.text:
            print("\n🔧 Detected amount validation error. Trying alternative approach...")
            
            # Create a manual payment entry first
            manual_payment_data = {
                'amount': 500.00,
                'currency': 'INR', 
                'method': 'PHONEPE',
                'description': f'Manual payment for cart {cart_id}'
            }
            
            manual_response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/', 
                                          json=manual_payment_data, 
                                          headers=headers)
            
            print(f"Manual Payment Status: {manual_response.status_code}")
            print(f"Manual Payment Response: {manual_response.text}")
            
            return manual_response
    
    return response

def main():
    print("🧪 Production Payment Gateway Test")
    print("=" * 40)
    
    # Get token
    token = get_access_token()
    if not token:
        print("❌ Failed to get access token")
        return
    
    print("✅ Got access token")
    
    # Test 1: Check payment methods
    test_phonepe_gateway_directly()
    
    # Test 2: Try direct payment creation
    print("\n" + "="*40)
    direct_payment = create_direct_payment(token)
    
    # Test 3: Try cart approach with error analysis
    print("\n" + "="*40)
    cart_response = create_cart_and_force_amount(token)

if __name__ == "__main__":
    main()
