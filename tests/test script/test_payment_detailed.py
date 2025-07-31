#!/usr/bin/env python3
import requests
import json

def test_payment_detailed():
    """Test payment with detailed error analysis"""
    
    print("🧪 DETAILED PAYMENT ERROR TEST")
    print("=" * 50)
    
    # 1. Login
    print("1. Logging in...")
    login_response = requests.post('https://api.okpuja.com/api/auth/login/', json={
        'email': 'asliprinceraj@gmail.com',
        'password': 'testpass123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json()['access']
    print("✅ Login successful")
    
    # 2. Get cart 28 details
    print("2. Getting cart 28 details...")
    headers = {'Authorization': f'Bearer {token}'}
    
    cart_response = requests.get('https://api.okpuja.com/api/cart/carts/28/', headers=headers)
    if cart_response.status_code == 200:
        cart = cart_response.json()
        print(f"Cart details: Service={cart.get('puja_service', {}).get('title')}, Package={cart.get('package', {}).get('id')}, Total=₹{cart.get('total_price')}")
    else:
        print(f"❌ Couldn't get cart details: {cart_response.status_code}")
    
    # 3. Try payment with detailed logging
    print("3. Attempting payment...")
    
    payment_data = {
        'cart_id': 28,
        'method': 'PHONEPE',
        'address_id': 2
    }
    
    try:
        response = requests.post(
            'https://api.okpuja.com/api/payments/payments/process-cart/',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=payment_data,
            timeout=60
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Payment initiated successfully!")
        else:
            print("❌ Payment failed")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_payment_detailed()
