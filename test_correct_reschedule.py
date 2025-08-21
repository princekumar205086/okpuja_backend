#!/usr/bin/env python3
"""
Test the correct reschedule endpoint for booking ID 28
"""

import requests
import json
from datetime import datetime

def test_booking_reschedule():
    """Test the correct reschedule endpoint"""
    
    base_url = "https://api.okpuja.com"
    
    # Your auth token (from the admin login)
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU1NzgxNTg4LCJpYXQiOjE3NTU3NzQzODgsImp0aSI6ImNhMzg0ZWE1N2I3YTQyY2RiNDQ4NmRjNDA4OTczYWM1IiwidXNlcl9pZCI6MSwicm9sZSI6IkFETUlOIiwiYWNjb3VudF9zdGF0dXMiOiJBQ1RJVkUiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0.Ew6tKGGgXPaO0m_Ee9xogO3twlBaCJ_As-DvJeje5XE"
    
    # Test data for rescheduling
    reschedule_data = {
        "selected_date": "2025-08-27",
        "selected_time": "16:00:00", 
        "reason": "Schedule change requested"
    }
    
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Testing Booking Reschedule Endpoints...")
    print("=" * 60)
    
    # Test 1: Wrong endpoint (what you were using)
    print("\n1. Testing WRONG endpoint (PujaBooking):")
    print(f"   URL: {base_url}/api/puja/bookings/28/reschedule/")
    
    try:
        response = requests.post(
            f"{base_url}/api/puja/bookings/28/reschedule/",
            headers=headers,
            json=reschedule_data,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Correct endpoint (regular Booking)
    print("\n2. Testing CORRECT endpoint (regular Booking):")
    print(f"   URL: {base_url}/api/booking/bookings/28/reschedule/")
    
    try:
        response = requests.post(
            f"{base_url}/api/booking/bookings/28/reschedule/",
            headers=headers,
            json=reschedule_data,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS! Booking rescheduled successfully")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Admin endpoint (alternative)
    print("\n3. Testing ADMIN endpoint (alternative):")
    print(f"   URL: {base_url}/api/booking/admin/bookings/28/reschedule/")
    
    try:
        response = requests.post(
            f"{base_url}/api/booking/admin/bookings/28/reschedule/",
            headers=headers,
            json=reschedule_data,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS! Booking rescheduled successfully via admin endpoint")
        else:
            print(f"   ❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print("   • Booking ID 28 exists in the 'Booking' model (booking app)")
    print("   • You were using the wrong endpoint for 'PujaBooking' model (puja app)")
    print("   • Use: POST /api/booking/bookings/28/reschedule/")
    print("   • Or:  POST /api/booking/admin/bookings/28/reschedule/")

if __name__ == "__main__":
    test_booking_reschedule()