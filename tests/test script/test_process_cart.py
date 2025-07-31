#!/usr/bin/env python
"""
Test Process Cart Endpoint with V2 Integration
This script tests the exact endpoint that's failing in the frontend
"""

import requests
import json

def test_process_cart_endpoint():
    """Test the process-cart endpoint"""
    print("🧪 Testing Process Cart Endpoint")
    print("=" * 50)
    
    # Your production backend URL
    base_url = "https://api.okpuja.com"
    endpoint = f"{base_url}/api/payments/payments/process-cart/"
    
    # Test payload (similar to what frontend sends)
    payload = {
        "cart_id": 13,
        "method": "PHONEPE"
    }
    
    # Headers from your browser request
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUzNDU2OTUwLCJpYXQiOjE3NTM0NTMzNTAsImp0aSI6ImQxMjgxM2QyM2EyZjQ5MDI5YTZjZTEyZjMzNzczNWJhIiwidXNlcl9pZCI6Nywicm9sZSI6IlVTRVIiLCJhY2NvdW50X3N0YXR1cyI6IkFDVElWRSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfQ.qlzTPNzrmlXst-Ke954WqX05deE2XE99KorC4we-lno",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    
    print(f"🌐 Endpoint: {endpoint}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    print(f"🔑 Using Authorization header: {headers['Authorization'][:50]}...")
    print()
    
    try:
        print("📡 Making request...")
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200 or response.status_code == 201:
            response_data = response.json()
            print(f"✅ SUCCESS! Payment initiated")
            print(f"📝 Response: {json.dumps(response_data, indent=2)}")
            
            if 'payment_url' in response_data:
                print(f"🔗 Payment URL: {response_data['payment_url']}")
                print("🎉 V2 Integration is working on production!")
            
        else:
            print(f"❌ Error Status: {response.status_code}")
            print(f"📝 Response Body: {response.text}")
            
            # Try to parse error response
            try:
                error_data = response.json()
                print(f"🔍 Parsed Error: {json.dumps(error_data, indent=2)}")
            except:
                print("📝 Raw Error Response:", response.text)
                
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("💡 This might indicate the production server is down or network issues")
        
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
        print("💡 The server took too long to respond")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_local_endpoint():
    """Test the local development endpoint"""
    print("\n🏠 Testing Local Development Endpoint")
    print("=" * 50)
    
    # Local development URL
    base_url = "http://127.0.0.1:8000"
    endpoint = f"{base_url}/api/payments/payments/process-cart/"
    
    payload = {
        "cart_id": 13,
        "method": "PHONEPE"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUzNDU2OTUwLCJpYXQiOjE3NTM0NTMzNTAsImp0aSI6ImQxMjgxM2QyM2EyZjQ5MDI5YTZjZTEyZjMzNzczNWJhIiwidXNlcl9pZCI6Nywicm9sZSI6IlVTRVIiLCJhY2NvdW50X3N0YXR1cyI6IkFDVElWRSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfQ.qlzTPNzrmlXst-Ke954WqX05deE2XE99KorC4we-lno"
    }
    
    print(f"🌐 Local Endpoint: {endpoint}")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Local endpoint is working!")
            response_data = response.json()
            print(f"📝 Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"❌ Local endpoint error: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Local server not running on http://127.0.0.1:8000")
        print("💡 Make sure Django development server is running")
    except Exception as e:
        print(f"❌ Local test error: {e}")

def main():
    """Main test function"""
    print("🚀 Process Cart Endpoint Test")
    print("=" * 60)
    print("This script tests the process-cart endpoint that's failing in your frontend")
    print()
    
    # Test production endpoint
    test_process_cart_endpoint()
    
    # Test local endpoint
    test_local_endpoint()
    
    print("\n🏁 Test Complete")
    print("=" * 60)
    print("💡 If production test succeeds, the V2 integration is working!")
    print("💡 If it fails, check the Django logs on your production server")

if __name__ == "__main__":
    main()
