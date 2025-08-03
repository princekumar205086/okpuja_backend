"""
Test PhonePe Webhook with Correct Authentication
Tests the webhook endpoint with the password: Okpuja2025
"""

import requests
import json
import base64

# Webhook configuration
WEBHOOK_URL = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"
USERNAME = "okpuja_webhook_user"
PASSWORD = "Okpuja2025"

def test_webhook_authentication():
    """Test webhook with correct authentication"""
    
    # Create Basic Auth header
    credentials = f"{USERNAME}:{PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    # Test webhook payload
    test_payload = {
        "merchantId": "M22KEWU5BO1I2",
        "transactionId": "TEST_TXN_AUTH_123",
        "amount": 10000,
        "status": "SUCCESS",
        "paymentInstrument": {
            "type": "UPI"
        },
        "merchantOrderId": "CART_test-auth-cart-id_123456"
    }
    
    print("🔐 Testing PhonePe Webhook Authentication")
    print(f"📍 URL: {WEBHOOK_URL}")
    print(f"👤 Username: {USERNAME}")
    print(f"🔑 Password: {PASSWORD}")
    print(f"🔒 Auth Header: Basic {encoded_credentials}")
    print("\n" + "="*50)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"📄 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 SUCCESS: Webhook authentication working!")
            print("✅ PhonePe can now send notifications to your endpoint")
        elif response.status_code == 401:
            print("\n❌ AUTHENTICATION FAILED: Check username/password")
        else:
            print(f"\n⚠️  Unexpected response: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Make sure Django server is running")
        print("   Run: python manage.py runserver")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_wrong_password():
    """Test with wrong password to verify security"""
    
    credentials = f"{USERNAME}:wrong_password"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    test_payload = {"test": "data"}
    
    print("\n🔒 Testing Security (Wrong Password)")
    print("="*50)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ SECURITY OK: Wrong password correctly rejected")
        else:
            print("⚠️  SECURITY ISSUE: Wrong password not rejected")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Server not running")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_webhook_authentication()
    test_wrong_password()
    
    print("\n" + "="*50)
    print("🏁 WEBHOOK TESTING COMPLETE")
    print("\nNext steps:")
    print("1. ✅ Webhook created in PhonePe dashboard")
    print("2. ✅ Authentication configured")
    print("3. 🔄 Test with real PhonePe payments")
    print("4. 🌐 Update webhook URL to production domain")
