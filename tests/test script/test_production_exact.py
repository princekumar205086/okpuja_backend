#!/usr/bin/env python3
import requests
import json

def test_production_api_call_exactly():
    """Test the exact API call that production is making"""
    
    print("🧪 TESTING EXACT PRODUCTION API CALL")
    print("=" * 50)
    
    # 1. Login to get token
    print("1. Getting authentication token...")
    login_response = requests.post('https://api.okpuja.com/api/auth/login/', json={
        'email': 'asliprinceraj@gmail.com',
        'password': 'testpass123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json()['access']
    print("✅ Login successful")
    
    # 2. Make the exact payment request that our test script makes
    print("2. Making payment request...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test WITHOUT address_id first (since our local test didn't include it)
    payment_data = {
        'cart_id': 29,
        'method': 'PHONEPE'
    }
    
    print(f"Request: {json.dumps(payment_data, indent=2)}")
    
    try:
        response = requests.post(
            'https://api.okpuja.com/api/payments/payments/process-cart/',
            headers=headers,
            json=payment_data,
            timeout=60
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ SUCCESS! Payment initiated without address_id")
            response_data = response.json()
            print(f"Payment URL: {response_data.get('payment_url', 'Not found')}")
        else:
            print("❌ FAILED without address_id")
            
            # Now try WITH address_id
            print("\n3. Trying with address_id...")
            payment_data['address_id'] = 2
            
            response2 = requests.post(
                'https://api.okpuja.com/api/payments/payments/process-cart/',
                headers=headers,
                json=payment_data,
                timeout=60
            )
            
            print(f"Response Status: {response2.status_code}")
            print(f"Response: {response2.text}")
            
            if response2.status_code in [200, 201]:
                print("✅ SUCCESS! Payment initiated with address_id")
                response_data = response2.json()
                print(f"Payment URL: {response_data.get('payment_url', 'Not found')}")
            else:
                print("❌ FAILED with address_id")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_production_api_call_exactly()
