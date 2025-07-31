#!/usr/bin/env python
"""
PhonePe V2 API Testing Script
Tests OAuth2 authentication and payment creation with V2 credentials
"""

import os
import sys
import django

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

import requests
import json
from django.conf import settings

def test_phonepe_v2_oauth():
    """Test PhonePe V2 OAuth2 authentication"""
    print("🔐 Testing PhonePe V2 OAuth2 Authentication")
    print("=" * 60)
    
    # OAuth2 endpoint
    auth_url = f"{settings.PHONEPE_AUTH_BASE_URL}/v1/oauth/token"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'User-Agent': 'okpuja-backend/1.0'
    }
    
    data = {
        'client_id': settings.PHONEPE_CLIENT_ID,
        'client_version': settings.PHONEPE_CLIENT_VERSION,
        'client_secret': settings.PHONEPE_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    
    print(f"🌐 Auth URL: {auth_url}")
    print(f"📋 Client ID: {settings.PHONEPE_CLIENT_ID}")
    print(f"📋 Client Version: {settings.PHONEPE_CLIENT_VERSION}")
    print(f"🔑 Client Secret: {settings.PHONEPE_CLIENT_SECRET[:10]}...")
    print()
    
    try:
        response = requests.post(auth_url, headers=headers, data=data, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Body: {response.text}")
        print()
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_at = token_data.get('expires_at')
            
            print(f"✅ OAuth2 SUCCESS!")
            print(f"🎫 Access Token: {access_token[:50]}...")
            print(f"⏰ Expires At: {expires_at}")
            print()
            return access_token
        else:
            print(f"❌ OAuth2 FAILED!")
            print(f"💥 Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None

def test_phonepe_v2_payment(access_token):
    """Test PhonePe V2 payment creation"""
    if not access_token:
        print("⚠️ Skipping payment test - no access token")
        return
    
    print("💳 Testing PhonePe V2 Payment Creation")
    print("=" * 60)
    
    # Payment endpoint
    payment_url = f"{settings.PHONEPE_PAYMENT_BASE_URL}/checkout/v2/pay"
    
    # Test payment payload
    payload = {
        "merchantOrderId": "TEST123456789",
        "amount": 1000,  # ₹10.00
        "expireAfter": 1200,
        "paymentFlow": {
            "type": "PG_CHECKOUT",
            "message": "Test payment for OkPuja integration",
            "merchantUrls": {
                "redirectUrl": "https://www.okpuja.com/payment-success"
            }
        },
        "metaInfo": {
            "udf1": "test_payment",
            "udf2": "okpuja_integration",
            "udf3": "v2_api_test",
            "udf4": "phonepe_test",
            "udf5": "amount_10"
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'O-Bearer {access_token}',
        'Accept': 'application/json',
        'User-Agent': 'okpuja-backend/1.0'
    }
    
    print(f"🌐 Payment URL: {payment_url}")
    print(f"💰 Test Amount: ₹{payload['amount']/100}")
    print(f"📋 Merchant Order ID: {payload['merchantOrderId']}")
    print(f"🔑 Authorization: O-Bearer {access_token[:20]}...")
    print()
    
    try:
        response = requests.post(payment_url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Body: {response.text}")
        print()
        
        if response.status_code == 200:
            payment_data = response.json()
            order_id = payment_data.get('orderId')
            redirect_url = payment_data.get('redirectUrl')
            
            print(f"✅ PAYMENT CREATION SUCCESS!")
            print(f"🆔 Order ID: {order_id}")
            print(f"🔗 Redirect URL: {redirect_url}")
            print()
            
            if redirect_url:
                print("🎉 Payment URL generated successfully!")
                print("✅ You can now test frontend payment flow with this URL")
            
            return payment_data
        else:
            print(f"❌ PAYMENT CREATION FAILED!")
            print(f"💥 Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None

def test_connectivity():
    """Test basic connectivity to PhonePe domains"""
    print("🌐 Testing Connectivity to PhonePe Domains")
    print("=" * 60)
    
    endpoints = [
        settings.PHONEPE_AUTH_BASE_URL,
        settings.PHONEPE_PAYMENT_BASE_URL,
        "https://api-preprod.phonepe.com",
        "https://api.phonepe.com"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"✅ {endpoint}: Connected (Status: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection refused")
        except Exception as e:
            print(f"⚠️ {endpoint}: {str(e)}")
    
    print()

def main():
    """Main test function"""
    print("🚀 PhonePe V2 API Integration Test")
    print("=" * 60)
    print(f"Environment: {settings.PHONEPE_ENV}")
    print(f"Client ID: {settings.PHONEPE_CLIENT_ID}")
    print(f"Auth Base URL: {settings.PHONEPE_AUTH_BASE_URL}")
    print(f"Payment Base URL: {settings.PHONEPE_PAYMENT_BASE_URL}")
    print()
    
    # Test 1: Basic connectivity
    test_connectivity()
    
    # Test 2: OAuth2 authentication
    access_token = test_phonepe_v2_oauth()
    
    # Test 3: Payment creation
    if access_token:
        test_phonepe_v2_payment(access_token)
    
    print("🏁 Test Complete!")
    print("=" * 60)
    
    if access_token:
        print("✅ V2 Integration is working correctly!")
        print("💡 Next steps:")
        print("   1. Test payment from your frontend")
        print("   2. Monitor webhook callbacks")
        print("   3. Verify payment status updates")
    else:
        print("❌ V2 Integration needs attention!")
        print("💡 Check:")
        print("   1. Network connectivity")
        print("   2. Credential accuracy")
        print("   3. Firewall settings")

if __name__ == "__main__":
    main()
