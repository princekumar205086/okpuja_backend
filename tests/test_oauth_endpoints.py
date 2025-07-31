#!/usr/bin/env python
"""
PhonePe V2 OAuth Endpoint Discovery
Tests different OAuth endpoint formats to find the correct one
"""

import requests
import json

def test_oauth_endpoints():
    """Test different OAuth endpoint formats"""
    
    print("Testing PhonePe V2 OAuth Endpoints")
    print("=" * 50)
    
    # Different OAuth endpoint formats to test
    endpoints = [
        "https://api-preprod.phonepe.com/oauth2/v2/token",
        "https://api-preprod.phonepe.com/apis/hermes/oauth2/v2/token", 
        "https://api-preprod.phonepe.com/apis/oauth2/v2/token",
        "https://api-preprod.phonepe.com/apis/pg-sandbox/oauth2/v2/token",
        "https://api-preprod.phonepe.com/v2/oauth2/token",
        "https://api-preprod.phonepe.com/auth/oauth2/v2/token"
    ]
    
    # Use dummy credentials to test endpoint availability
    test_data = {
        "grant_type": "client_credentials",
        "client_id": "test",
        "client_secret": "test"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    for endpoint in endpoints:
        print(f"\nTesting: {endpoint}")
        print("-" * len(endpoint))
        
        try:
            response = requests.post(
                endpoint, 
                data=test_data, 
                headers=headers,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            # Check if we get a proper OAuth error (400/401) vs 404
            if response.status_code == 404:
                print("❌ Endpoint not found (404)")
            elif response.status_code in [400, 401]:
                print("✅ Endpoint exists! (Got OAuth error as expected)")
                try:
                    error_data = response.json()
                    print(f"Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response: {response.text[:200]}...")
            elif response.status_code == 200:
                print("✅ Endpoint accessible!")
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"Response: {response.text[:200]}...")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectTimeout:
            print("❌ Connection timeout")
        except requests.exceptions.ConnectionError:
            print("❌ Connection error")  
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_oauth_endpoints()
