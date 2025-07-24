#!/usr/bin/env python
"""
Simple Production Test - No Promo Code
Test cart creation without promo code to avoid negative pricing
"""
import requests
import json

PRODUCTION_BASE_URL = 'https://backend.okpuja.com/api'
TEST_EMAIL = 'asliprinceraj@gmail.com'
TEST_PASSWORD = 'testpass123'

def get_access_token():
    response = requests.post(f'{PRODUCTION_BASE_URL}/auth/login/', {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get('access')
    return None

def test_cart_variations(token):
    """Test different cart creation approaches"""
    print("🧪 Testing cart variations...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    test_cases = [
        {
            'name': 'Service 8 + Package 2 (no promo)',
            'data': {
                'puja_service': 8,
                'package': 2,
                'quantity': 1,
                'selected_date': '2025-07-20',
                'selected_time': '10:00:00',
                'special_instructions': 'Test without promo'
            }
        },
        {
            'name': 'Service 8 + Package 1 (no promo)', 
            'data': {
                'puja_service': 8,
                'package': 1,
                'quantity': 1,
                'selected_date': '2025-07-20',
                'selected_time': '10:00:00',
                'special_instructions': 'Test package 1'
            }
        },
        {
            'name': 'Service 8 only (no package)',
            'data': {
                'puja_service': 8,
                'quantity': 1,
                'selected_date': '2025-07-20',
                'selected_time': '10:00:00',
                'special_instructions': 'Test service only'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        
        response = requests.post(f'{PRODUCTION_BASE_URL}/cart/carts/', 
                               json=test_case['data'], 
                               headers=headers)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            cart = response.json()
            package = cart.get('package')
            total = cart.get('total_price', '0.00')
            
            print(f"✅ Cart ID: {cart['id']}")
            print(f"   Package: {package['id'] if package else 'None'}")
            print(f"   Total: ₹{total}")
            
            if float(total) > 0:
                print(f"🎉 FOUND WORKING CONFIGURATION!")
                
                # Test payment immediately
                payment_data = {
                    'cart_id': cart['id'],
                    'address_id': 1,
                    'method': 'PHONEPE'
                }
                
                payment_response = requests.post(f'{PRODUCTION_BASE_URL}/payments/payments/process-cart/', 
                                               json=payment_data, 
                                               headers=headers)
                
                print(f"Payment Status: {payment_response.status_code}")
                print(f"Payment Response: {payment_response.text}")
                
                if payment_response.status_code == 201:
                    payment = payment_response.json()
                    print(f"🎉 PAYMENT SUCCESSFUL!")
                    print(f"   Payment URL: {payment.get('payment_url')}")
                    return payment
        else:
            print(f"❌ Failed: {response.text}")
    
    return None

def main():
    print("🔧 Simple Production Test - No Promo Code")
    print("=" * 50)
    
    token = get_access_token()
    if not token:
        print("❌ Failed to get token")
        return
    
    print("✅ Got access token")
    
    payment = test_cart_variations(token)
    
    if payment:
        print(f"\n🎉 SUCCESS: Production payment flow working!")
        print(f"🔗 Complete payment at: {payment.get('payment_url')}")
    else:
        print(f"\n❌ No working configuration found")
        print(f"   Package-service relationships need to be fixed in production database")

if __name__ == "__main__":
    main()
