#!/usr/bin/env python
"""
Comprehensive test script for reschedule functionality for both Puja and Astrology bookings.

This script tests:
1. Authentication with admin credentials
2. Creating test bookings 
3. Testing reschedule endpoints for both systems
4. Provides complete endpoint documentation with payloads

Admin credentials: admin@okpuja.com / admin@123
User credentials: aslprinceraj@gmail.com / testpass123
"""

import os
import sys
import json
import requests
from datetime import datetime, date, time, timedelta
from django.core.wsgi import get_wsgi_application

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
application = get_wsgi_application()

from django.contrib.auth import get_user_model
from booking.models import Booking
from astrology.models import AstrologyBooking, AstrologyService
from puja.models import PujaService, PujaBooking
from django.test import Client

User = get_user_model()

class RescheduleEndpointTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.admin_token = None
        self.user_token = None
        self.client = Client()
        
        print("🚀 RESCHEDULE ENDPOINT TESTING SUITE")
        print("=" * 60)
        
    def authenticate_admin(self):
        """Authenticate admin user and get token"""
        print("\n1️⃣ AUTHENTICATING ADMIN USER")
        print("-" * 40)
        
        login_url = f"{self.base_url}/api/auth/login/"
        admin_credentials = {
            "email": "admin@okpuja.com",
            "password": "admin@123"
        }
        
        try:
            response = requests.post(login_url, json=admin_credentials, timeout=10)
            print(f"   🔑 Login URL: {login_url}")
            print(f"   📧 Email: {admin_credentials['email']}")
            print(f"   🔐 Password: {admin_credentials['password']}")
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access')
                print(f"   ✅ Admin authentication successful!")
                print(f"   🎫 Token: {self.admin_token[:50]}...")
                return True
            else:
                print(f"   ❌ Admin authentication failed!")
                print(f"   📄 Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return False
    
    def authenticate_user(self):
        """Authenticate regular user and get token"""
        print("\n2️⃣ AUTHENTICATING REGULAR USER")
        print("-" * 40)
        
        login_url = f"{self.base_url}/api/auth/login/"
        user_credentials = {
            "email": "aslprinceraj@gmail.com",
            "password": "testpass123"
        }
        
        try:
            response = requests.post(login_url, json=user_credentials, timeout=10)
            print(f"   🔑 Login URL: {login_url}")
            print(f"   📧 Email: {user_credentials['email']}")
            print(f"   🔐 Password: {user_credentials['password']}")
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('access')
                print(f"   ✅ User authentication successful!")
                print(f"   🎫 Token: {self.user_token[:50]}...")
                return True
            else:
                print(f"   ❌ User authentication failed!")
                print(f"   📄 Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return False
    
    def get_sample_bookings(self):
        """Get sample booking IDs for testing"""
        print("\n3️⃣ GETTING SAMPLE BOOKING IDS")
        print("-" * 40)
        
        # Check for existing bookings
        puja_bookings = PujaBooking.objects.all()[:3]
        astrology_bookings = AstrologyBooking.objects.all()[:3]
        main_bookings = Booking.objects.all()[:3]
        
        print(f"   📋 Puja Bookings Found: {puja_bookings.count()}")
        for booking in puja_bookings:
            print(f"      - ID: {booking.id}, User: {booking.user.email if booking.user else 'N/A'}")
        
        print(f"   ⭐ Astrology Bookings Found: {astrology_bookings.count()}")
        for booking in astrology_bookings:
            print(f"      - ID: {booking.id}, User: {booking.user.email if booking.user else 'N/A'}")
        
        print(f"   🎯 Main Bookings Found: {main_bookings.count()}")
        for booking in main_bookings:
            print(f"      - ID: {booking.id}, User: {booking.user.email if booking.user else 'N/A'}")
        
        return {
            'puja': list(puja_bookings.values_list('id', flat=True)),
            'astrology': list(astrology_bookings.values_list('id', flat=True)),
            'main': list(main_bookings.values_list('id', flat=True))
        }
    
    def test_puja_reschedule(self, booking_id):
        """Test puja booking reschedule endpoint"""
        print(f"\n4️⃣ TESTING PUJA RESCHEDULE (ID: {booking_id})")
        print("-" * 40)
        
        endpoint = f"{self.base_url}/api/puja/bookings/{booking_id}/reschedule/"
        future_date = (datetime.now() + timedelta(days=7)).date()
        
        payload = {
            "new_date": str(future_date),
            "new_time": "14:00:00",
            "reason": "Testing reschedule functionality"
        }
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        print(f"   🎯 Endpoint: {endpoint}")
        print(f"   📦 Method: POST")
        print(f"   📋 Payload: {json.dumps(payload, indent=6)}")
        print(f"   🔑 Headers: Authorization: Bearer {self.admin_token[:30]}...")
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
            if response.status_code == 200:
                print("   ✅ Puja reschedule successful!")
            elif response.status_code == 404:
                print("   ⚠️  Booking not found (expected if no bookings exist)")
            elif response.status_code == 401:
                print("   ⚠️  Authentication required")
            else:
                print("   ℹ️  Other response received")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
    
    def test_astrology_reschedule(self, booking_id):
        """Test astrology booking reschedule endpoint"""
        print(f"\n5️⃣ TESTING ASTROLOGY RESCHEDULE (ID: {booking_id})")
        print("-" * 40)
        
        endpoint = f"{self.base_url}/api/astrology/bookings/{booking_id}/reschedule/"
        future_date = (datetime.now() + timedelta(days=7)).date()
        
        payload = {
            "preferred_date": str(future_date),
            "preferred_time": "15:00:00",
            "reason": "Testing reschedule functionality"
        }
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        print(f"   🎯 Endpoint: {endpoint}")
        print(f"   📦 Method: PATCH")
        print(f"   📋 Payload: {json.dumps(payload, indent=6)}")
        print(f"   🔑 Headers: Authorization: Bearer {self.admin_token[:30]}...")
        
        try:
            response = requests.patch(endpoint, json=payload, headers=headers, timeout=10)
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
            if response.status_code == 200:
                print("   ✅ Astrology reschedule successful!")
            elif response.status_code == 404:
                print("   ⚠️  Booking not found (expected if no bookings exist)")
            elif response.status_code == 401:
                print("   ⚠️  Authentication required")
            else:
                print("   ℹ️  Other response received")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
    
    def test_main_booking_reschedule(self, booking_id):
        """Test main booking reschedule endpoint"""
        print(f"\n6️⃣ TESTING MAIN BOOKING RESCHEDULE (ID: {booking_id})")
        print("-" * 40)
        
        endpoint = f"{self.base_url}/api/booking/bookings/{booking_id}/reschedule/"
        future_date = (datetime.now() + timedelta(days=7)).date()
        
        payload = {
            "new_date": str(future_date),
            "new_time": "16:00:00",
            "reason": "Testing reschedule functionality"
        }
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        print(f"   🎯 Endpoint: {endpoint}")
        print(f"   📦 Method: POST")
        print(f"   📋 Payload: {json.dumps(payload, indent=6)}")
        print(f"   🔑 Headers: Authorization: Bearer {self.admin_token[:30]}...")
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            print(f"   📊 Status Code: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
            if response.status_code == 200:
                print("   ✅ Main booking reschedule successful!")
            elif response.status_code == 404:
                print("   ⚠️  Booking not found (expected if no bookings exist)")
            elif response.status_code == 401:
                print("   ⚠️  Authentication required")
            else:
                print("   ℹ️  Other response received")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
    
    def print_endpoint_documentation(self):
        """Print comprehensive endpoint documentation"""
        print("\n" + "=" * 60)
        print("📚 COMPLETE RESCHEDULE ENDPOINT DOCUMENTATION")
        print("=" * 60)
        
        print("\n🔐 AUTHENTICATION:")
        print("-" * 20)
        print("Admin Credentials: admin@okpuja.com / admin@123")
        print("User Credentials: aslprinceraj@gmail.com / testpass123")
        print()
        print("Login Endpoint: POST /api/auth/login/")
        print("Payload: {\"email\": \"admin@okpuja.com\", \"password\": \"admin@123\"}")
        print("Response: {\"access\": \"TOKEN\", \"refresh\": \"REFRESH_TOKEN\"}")
        print("Usage: Authorization: Bearer {TOKEN}")
        
        print("\n📋 RESCHEDULE ENDPOINTS:")
        print("-" * 25)
        
        print("\n1️⃣ PUJA BOOKING RESCHEDULE:")
        print("   Endpoint: POST /api/puja/bookings/{id}/reschedule/")
        print("   Headers: Authorization: Bearer {TOKEN}")
        print("   Payload:")
        print("   {")
        print("       \"new_date\": \"2025-12-25\",")
        print("       \"new_time\": \"14:00:00\",")
        print("       \"reason\": \"Schedule change requested\"")
        print("   }")
        
        print("\n2️⃣ ASTROLOGY BOOKING RESCHEDULE:")
        print("   Endpoint: PATCH /api/astrology/bookings/{id}/reschedule/")
        print("   Headers: Authorization: Bearer {TOKEN}")
        print("   Payload:")
        print("   {")
        print("       \"preferred_date\": \"2025-12-25\",")
        print("       \"preferred_time\": \"15:00:00\",")
        print("       \"reason\": \"Schedule change requested\"")
        print("   }")
        
        print("\n3️⃣ MAIN BOOKING RESCHEDULE:")
        print("   Endpoint: POST /api/booking/bookings/{id}/reschedule/")
        print("   Headers: Authorization: Bearer {TOKEN}")
        print("   Payload:")
        print("   {")
        print("       \"new_date\": \"2025-12-25\",")
        print("       \"new_time\": \"16:00:00\",")
        print("       \"reason\": \"Schedule change requested\"")
        print("   }")
        
        print("\n🔒 PERMISSIONS:")
        print("-" * 15)
        print("- Only admin can reschedule any booking")
        print("- Users can reschedule their own bookings")
        print("- Cannot reschedule completed/cancelled bookings")
        print("- Cannot reschedule to past dates")
        
        print("\n📝 cURL EXAMPLES:")
        print("-" * 17)
        
        print("\n# Get Admin Token:")
        print("curl -X POST http://127.0.0.1:8000/api/auth/login/ \\")
        print("  -H \"Content-Type: application/json\" \\")
        print("  -d '{\"email\": \"admin@okpuja.com\", \"password\": \"admin@123\"}'")
        
        print("\n# Reschedule Puja Booking:")
        print("curl -X POST http://127.0.0.1:8000/api/puja/bookings/1/reschedule/ \\")
        print("  -H \"Authorization: Bearer YOUR_TOKEN\" \\")
        print("  -H \"Content-Type: application/json\" \\")
        print("  -d '{\"new_date\": \"2025-12-25\", \"new_time\": \"14:00:00\", \"reason\": \"Schedule change\"}'")
        
        print("\n# Reschedule Astrology Booking:")
        print("curl -X PATCH http://127.0.0.1:8000/api/astrology/bookings/1/reschedule/ \\")
        print("  -H \"Authorization: Bearer YOUR_TOKEN\" \\")
        print("  -H \"Content-Type: application/json\" \\")
        print("  -d '{\"preferred_date\": \"2025-12-25\", \"preferred_time\": \"15:00:00\", \"reason\": \"Schedule change\"}'")
        
        print("\n# Reschedule Main Booking:")
        print("curl -X POST http://127.0.0.1:8000/api/booking/bookings/1/reschedule/ \\")
        print("  -H \"Authorization: Bearer YOUR_TOKEN\" \\")
        print("  -H \"Content-Type: application/json\" \\")
        print("  -d '{\"new_date\": \"2025-12-25\", \"new_time\": \"16:00:00\", \"reason\": \"Schedule change\"}'")
    
    def run_complete_test(self):
        """Run complete test suite"""
        print("Starting comprehensive reschedule endpoint test...")
        
        # Authenticate users
        admin_auth = self.authenticate_admin()
        user_auth = self.authenticate_user()
        
        if not admin_auth:
            print("❌ Cannot proceed without admin authentication")
            return
        
        # Get sample booking IDs
        booking_ids = self.get_sample_bookings()
        
        # Test each type of reschedule endpoint
        if booking_ids['puja']:
            self.test_puja_reschedule(booking_ids['puja'][0])
        else:
            self.test_puja_reschedule(1)  # Test with ID 1 anyway
        
        if booking_ids['astrology']:
            self.test_astrology_reschedule(booking_ids['astrology'][0])
        else:
            self.test_astrology_reschedule(1)  # Test with ID 1 anyway
        
        if booking_ids['main']:
            self.test_main_booking_reschedule(booking_ids['main'][0])
        else:
            self.test_main_booking_reschedule(1)  # Test with ID 1 anyway
        
        # Print documentation
        self.print_endpoint_documentation()
        
        print("\n" + "=" * 60)
        print("🎉 RESCHEDULE ENDPOINT TESTING COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    tester = RescheduleEndpointTester()
    tester.run_complete_test()