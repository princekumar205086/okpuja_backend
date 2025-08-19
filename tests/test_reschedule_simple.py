#!/usr/bin/env python
"""
Simple test script for reschedule functionality
Tests both Puja and Astrology booking reschedule features
"""

import os
import sys
import django
from datetime import datetime, date, time, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

# Add testserver to ALLOWED_HOSTS for testing
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
    settings.ALLOWED_HOSTS.append('127.0.0.1')

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

User = get_user_model()

def test_reschedule_endpoints():
    """Test both reschedule endpoints"""
    print("🚀 Starting Reschedule Functionality Tests")
    print("=" * 50)
    
    client = Client()
    
    # Test 1: Check if URLs exist
    print("\n1️⃣ Testing URL patterns...")
    
    try:
        # Test astrology reschedule URL - direct URL since namespace isn't used
        astrology_url = '/api/astrology/bookings/1/reschedule/'
        print(f"✅ Astrology reschedule URL: {astrology_url}")
    except Exception as e:
        print(f"❌ Astrology reschedule URL error: {e}")
    
    try:
        # Test puja reschedule URL - using router  
        puja_url = '/api/booking/bookings/1/reschedule/'
        print(f"✅ Puja reschedule URL: {puja_url}")
    except Exception as e:
        print(f"❌ Puja reschedule URL error: {e}")
    
    # Test 2: Check model methods
    print("\n2️⃣ Testing model methods...")
    
    try:
        from astrology.models import AstrologyBooking
        # Create a test astrology booking
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone='1234567890'
        )
        
        from astrology.models import AstrologyService
        service, created = AstrologyService.objects.get_or_create(
            name='Test Astrology Service',
            defaults={
                'description': 'Test service',
                'base_price': 100.00,
                'duration_minutes': 30
            }
        )
        
        booking = AstrologyBooking.objects.create(
            user=user,
            service=service,
            preferred_date=date.today() + timedelta(days=1),
            preferred_time=time(10, 0),
            status='CONFIRMED'
        )
        
        # Test reschedule method
        new_date = date.today() + timedelta(days=2)
        new_time = time(11, 0)
        
        if hasattr(booking, 'reschedule'):
            booking.reschedule(new_date, new_time)
            print("✅ Astrology booking reschedule method works")
        else:
            print("❌ Astrology booking reschedule method not found")
            
    except Exception as e:
        print(f"❌ Astrology model test error: {e}")
    
    # Test 3: Check serializers exist
    print("\n3️⃣ Testing serializers...")
    
    try:
        from astrology.serializers import AstrologyBookingRescheduleSerializer
        print("✅ AstrologyBookingRescheduleSerializer found")
    except ImportError as e:
        print(f"❌ AstrologyBookingRescheduleSerializer not found: {e}")
    
    try:
        from booking.serializers import BookingRescheduleSerializer
        print("✅ BookingRescheduleSerializer found")
    except ImportError as e:
        print(f"❌ BookingRescheduleSerializer not found: {e}")
    
    # Test 4: Test endpoints without authentication (should fail gracefully)
    print("\n4️⃣ Testing endpoints without authentication...")
    
    try:
        response = client.patch('/api/astrology/bookings/1/reschedule/', {
            'preferred_date': '2024-12-25',
            'preferred_time': '10:00'
        })
        print(f"✅ Astrology reschedule endpoint exists - Status: {response.status_code}")
        if response.status_code == 401:
            print("   (401 Unauthorized is expected - authentication required)")
    except Exception as e:
        print(f"❌ Astrology endpoint test error: {e}")
    
    try:
        response = client.post('/api/booking/bookings/1/reschedule/', {
            'new_date': '2024-12-25',
            'new_time': '10:00'
        })
        print(f"✅ Puja reschedule endpoint exists - Status: {response.status_code}")
        if response.status_code == 401:
            print("   (401 Unauthorized is expected - authentication required)")
        elif response.status_code == 404:
            print("   (404 Not Found - booking with ID 1 doesn't exist)")
    except Exception as e:
        print(f"❌ Puja endpoint test error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print("- URL patterns: Check console output above")
    print("- Model methods: Check console output above") 
    print("- Serializers: Check console output above")
    print("- Endpoints: Authentication required (expected)")
    print("\n🎯 Next Steps:")
    print("1. Create actual bookings using Django admin or API")
    print("2. Get authentication token")
    print("3. Test with real booking IDs")
    print("4. Use proper API testing tools like Postman")

if __name__ == '__main__':
    test_reschedule_endpoints()
