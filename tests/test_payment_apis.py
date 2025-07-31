#!/usr/bin/env python
"""
Quick API Test for New Payments App
Test the REST API endpoints
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "testuser"  # Replace with actual username
PASSWORD = "testpass"  # Replace with actual password


def get_auth_token():
    """Get JWT token for authentication"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


def test_payment_apis():
    """Test payment API endpoints"""
    print("🧪 Testing Payment APIs")
    print("=" * 40)
    
    # Get auth token
    print("🔑 Getting authentication token...")
    token = get_auth_token()
    
    if not token:
        print("❌ Cannot test APIs without authentication")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test health check
    print(f"\n💓 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/pay/health/", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test payment creation
    print(f"\n💳 Testing payment creation...")
    try:
        payment_data = {
            "amount": 10000,  # ₹100
            "redirect_url": "https://okpuja.com/payment/success",
            "description": "API Test Payment",
            "metadata": {"test": True}
        }
        
        response = requests.post(f"{BASE_URL}/api/pay/create/", 
                               headers=headers, json=payment_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Payment created successfully")
            print(f"Order ID: {data['data']['merchant_order_id']}")
            print(f"Payment URL: {data['data'].get('payment_url', 'No URL')}")
            
            # Test status check
            order_id = data['data']['merchant_order_id']
            print(f"\n📊 Testing status check...")
            
            status_response = requests.get(f"{BASE_URL}/api/pay/status/{order_id}/", 
                                         headers=headers)
            print(f"Status: {status_response.status_code}")
            print(f"Response: {status_response.json()}")
            
        else:
            print(f"❌ Payment creation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Payment creation error: {e}")
    
    # Test payment list
    print(f"\n📋 Testing payment list...")
    try:
        response = requests.get(f"{BASE_URL}/api/pay/list/", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['data'])} payments")
        else:
            print(f"❌ Payment list failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Payment list error: {e}")


def main():
    """Main test function"""
    print("🚀 Quick API Test for New Payments App")
    print("🔗 Testing REST API endpoints")
    print("=" * 50)
    
    print(f"📍 Base URL: {BASE_URL}")
    print(f"👤 Username: {USERNAME}")
    
    test_payment_apis()
    
    print(f"\n{'=' * 50}")
    print(f"✅ API testing completed!")
    print(f"💡 Check Django server logs for detailed information")
    print(f"🔧 Update USERNAME/PASSWORD in script for your environment")


if __name__ == "__main__":
    main()
