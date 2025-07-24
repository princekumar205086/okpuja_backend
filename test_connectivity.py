#!/usr/bin/env python3
import requests
import json

def test_production_phonepe_connectivity():
    """Test if production can reach PhonePe API endpoints"""
    
    print("🧪 TESTING PRODUCTION PHONEPE CONNECTIVITY")
    print("=" * 50)
    
    # Login to get a session on production
    print("1. Logging into production...")
    login_response = requests.post('https://backend.okpuja.com/api/auth/login/', json={
        'email': 'asliprinceraj@gmail.com',
        'password': 'testpass123'
    })
    token = login_response.json()['access']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Create a test endpoint that makes a PhonePe API call from production server
    # For now, let's try to see if we can get any detailed error info
    
    print("2. Testing payment with detailed error capture...")
    
    # Make multiple requests to see if we get any variation in error
    for i in range(3):
        print(f"\n--- Attempt {i+1} ---")
        
        payment_data = {
            'cart_id': 28,
            'method': 'PHONEPE'
        }
        
        try:
            response = requests.post(
                'https://backend.okpuja.com/api/payments/payments/process-cart/',
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 400:
                error_data = response.json()
                error_details = error_data.get('details', '')
                print(f"Error: {error_details}")
                
                # Check if it's exactly the same error
                if 'Payment initiation failed' in error_details:
                    print("❌ Same payment initiation error")
                else:
                    print(f"❌ Different error: {error_details}")
            else:
                print(f"✅ Different status: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
        except Exception as e:
            print(f"❌ Request exception: {e}")

    print("\n🔍 CONCLUSION:")
    print("The error is consistent across attempts, suggesting a systematic issue")
    print("Most likely causes:")
    print("1. Production server cannot reach PhonePe API (network/firewall)")
    print("2. Production PhonePe credentials are different/invalid")
    print("3. Production environment has different settings")
    print("4. Production server timezone or locale issues")

if __name__ == "__main__":
    test_production_phonepe_connectivity()
