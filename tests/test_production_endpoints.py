#!/usr/bin/env python
"""
PhonePe V2 Production Endpoint Discovery
Testing different production endpoint formats to find the correct ones
"""

import requests
import json

def test_production_endpoints():
    """Test different production endpoint formats"""
    
    print("Testing PhonePe V2 Production Endpoints")
    print("=" * 60)
    
    # Different production endpoint formats to test
    base_urls = [
        "https://api.phonepe.com",
        "https://api.phonepe.com/apis/hermes",
        "https://api.phonepe.com/apis/pg-sandbox",
        "https://api.phonepe.com/pg",
        "https://api.phonepe.com/v1"
    ]
    
    endpoints = [
        "/oauth2/v2/token",
        "/pg/v1/pay", 
        "/pg/v1/status",
        "/apis/hermes/oauth2/v2/token",
        "/apis/hermes/pg/v1/pay",
        "/apis/pg-sandbox/pg/v1/pay"
    ]
    
    # Test credentials
    test_data = {
        "grant_type": "client_credentials",
        "client_id": "SU2507311635477696235898",
        "client_secret": "1f59672d-e31c-4898-9caf-19ab54bcaaab"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "X-MERCHANT-ID": "M22KEWU5BO1I2"
    }
    
    # Test OAuth endpoints
    print("\n🔍 Testing OAuth Endpoints:")
    print("-" * 40)
    
    for base_url in base_urls:
        for endpoint in ["/oauth2/v2/token", "/apis/hermes/oauth2/v2/token"]:
            url = base_url + endpoint
            print(f"\nTesting: {url}")
            
            try:
                response = requests.post(url, data=test_data, headers=headers, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 404:
                    print("❌ Not found")
                elif response.status_code in [400, 401]:
                    print("✅ Endpoint exists! (OAuth error as expected)")
                    try:
                        data = response.json()
                        print(f"Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"Response: {response.text[:100]}...")
                elif response.status_code == 200:
                    print("✅ Success!")
                    try:
                        data = response.json() 
                        print(f"Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"Response: {response.text[:100]}...")
                else:
                    print(f"⚠️  Status: {response.status_code}")
                    print(f"Response: {response.text[:100]}...")
                    
            except requests.exceptions.Timeout:
                print("❌ Timeout")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Test Payment endpoints 
    print(f"\n🔍 Testing Payment Endpoints:")
    print("-" * 40)
    
    payment_test_data = {
        "request": "eyJ0ZXN0IjoidGVzdCJ9"  # Base64 encoded test data
    }
    
    payment_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-MERCHANT-ID": "M22KEWU5BO1I2",
        "X-VERIFY": "test###1"
    }
    
    for base_url in base_urls:
        for endpoint in ["/pg/v1/pay", "/apis/hermes/pg/v1/pay", "/apis/pg-sandbox/pg/v1/pay"]:
            url = base_url + endpoint
            print(f"\nTesting: {url}")
            
            try:
                response = requests.post(url, json=payment_test_data, headers=payment_headers, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 404:
                    print("❌ Not found")
                elif response.status_code in [400, 401]:
                    print("✅ Endpoint exists! (Payment error as expected)")
                    try:
                        data = response.json()
                        print(f"Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"Response: {response.text[:100]}...")
                elif response.status_code == 200:
                    print("✅ Success!")
                    try:
                        data = response.json()
                        print(f"Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"Response: {response.text[:100]}...")
                else:
                    print(f"⚠️  Status: {response.status_code}")
                    print(f"Response: {response.text[:100]}...")
                    
            except requests.exceptions.Timeout:
                print("❌ Timeout")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_production_endpoints()
