#!/usr/bin/env python
"""
Test booking endpoint with the cart that just had booking created
"""

import requests
import json

def test_booking_endpoint():
    """Test the booking endpoint"""
    print("🌐 Testing Booking API Endpoint")
    print("=" * 40)
    
    # Test data from our previous successful test
    cart_id = "82c841e4-60c0-440d-9854-3eec8042aff0"
    
    # You'll need to get a fresh token, but let's try with existing one
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU0MDc4MjI2LCJpYXQiOjE3NTQwNzQ2MjYsImp0aSI6IjFjNmYyNGRkNDFkZjRiZDI4ZDE3MDZiZWI5Y2I3MDU1IiwidXNlcl9pZCI6Miwicm9sZSI6IlVTRVIiLCJhY2NvdW50X3N0YXR1cyI6IkFDVElWRSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfQ.nGlJYnIAhpBMJM5AkThYQlA5u2YWpxMb7hirkeLPRcU"
    
    # Test the booking endpoint
    url = f"http://127.0.0.1:8000/api/booking/bookings/by-cart/{cart_id}/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"📞 Making request to: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Booking found:")
            print(f"   📦 Booking ID: {data.get('book_id')}")
            print(f"   👤 User: {data.get('user_email')}")
            print(f"   💰 Amount: ₹{data.get('total_amount')}")
            print(f"   📅 Date: {data.get('selected_date')}")
            print(f"   📋 Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_booking_endpoint()
    print("\n" + "=" * 40)
    if success:
        print("✅ BOOKING ENDPOINT TEST SUCCESSFUL!")
        print("🎯 Auto-booking creation and retrieval working!")
    else:
        print("❌ BOOKING ENDPOINT TEST FAILED!")
        print("💡 Check if server is running and token is valid")
