#!/usr/bin/env python
import os
import django
import requests
import json

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_all_endpoints():
    print("🧪 TESTING ALL PAYMENT ENDPOINTS")
    print("="*60)
    
    # Test data
    cart_id = "5fa44890-71a8-492c-a49e-7a40f0aa391b"  # Your successful payment cart
    api_base = "http://127.0.0.1:8000/api"
    
    try:
        # First login to get token
        print("🔐 Getting authentication token...")
        login_response = requests.post(f"{api_base}/auth/login/", json={
            "email": "asliprinceraj@gmail.com",
            "password": "testpass123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
            
        token = login_response.json()['access']
        headers = {'Authorization': f'Bearer {token}'}
        print(f"✅ Authentication successful")
        
        # Test the booking endpoint
        print(f"\n📋 Testing booking endpoint...")
        booking_response = requests.get(
            f"{api_base}/booking/bookings/by-cart/{cart_id}/",
            headers=headers
        )
        
        print(f"   Status Code: {booking_response.status_code}")
        if booking_response.status_code == 200:
            booking_data = booking_response.json()
            print(f"✅ Booking response:")
            print(json.dumps(booking_data, indent=2)[:500] + "...")
        else:
            print(f"❌ Booking response: {booking_response.text}")
        
        # Test payment status endpoint
        print(f"\n💳 Testing payment status endpoint...")
        payment_response = requests.get(
            f"{api_base}/payments/cart/status/{cart_id}/",
            headers=headers
        )
        
        print(f"   Status Code: {payment_response.status_code}")
        if payment_response.status_code == 200:
            payment_data = payment_response.json()
            print(f"✅ Payment response:")
            print(json.dumps(payment_data, indent=2))
        else:
            print(f"❌ Payment response: {payment_response.text}")
        
        # Test the new manual verification endpoint
        print(f"\n🔧 Testing manual verification endpoint...")
        verification_response = requests.post(
            f"{api_base}/payments/verify-and-complete/",
            headers=headers,
            json={"cart_id": cart_id}
        )
        
        print(f"   Status Code: {verification_response.status_code}")
        if verification_response.status_code == 200:
            verification_data = verification_response.json()
            print(f"✅ Verification response:")
            print(json.dumps(verification_data, indent=2))
        else:
            print(f"❌ Verification response: {verification_response.text}")
        
        # Test redirect endpoint
        print(f"\n🔗 Testing redirect endpoint...")
        redirect_response = requests.get(
            f"{api_base}/payments/redirect/simple/",
            headers=headers,
            allow_redirects=False
        )
        
        print(f"   Status Code: {redirect_response.status_code}")
        if redirect_response.status_code == 302:
            redirect_url = redirect_response.headers.get('Location', 'No Location header')
            print(f"✅ Redirect URL: {redirect_url}")
        else:
            print(f"❌ Redirect response: {redirect_response.text}")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_endpoints()
