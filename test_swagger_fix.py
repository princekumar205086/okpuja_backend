#!/usr/bin/env python3

"""
Quick test script to verify Swagger documentation is working
"""

import requests
import sys

def test_swagger_docs():
    print("Testing Swagger documentation endpoints...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test endpoints
    endpoints = [
        f"{base_url}/api/docs/",
        f"{base_url}/api/docs/?format=openapi"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n🔄 Testing: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS: {endpoint}")
                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                print(f"   Content Length: {len(response.content)} bytes")
            else:
                print(f"❌ ERROR: {endpoint}")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:500]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR: {endpoint}")
            print("   Server might not be running")
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {endpoint}")
            print(f"   Error: {str(e)}")
    
    print("\n" + "="*50)
    print("Swagger documentation test completed!")

if __name__ == "__main__":
    test_swagger_docs()
