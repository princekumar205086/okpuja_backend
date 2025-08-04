#!/usr/bin/env python
"""
Create test user for astrology booking tests
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from astrology.models import AstrologyService

User = get_user_model()

def create_test_data():
    """Create test user and service"""
    print("Creating test data...")
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        email="astrotest@example.com",
        defaults={
            'username': 'astrotest',
            'phone': '9123456789',
            'is_active': True,
            'account_status': 'ACTIVE'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.email_verified = True
        user.otp_verified = True
        user.save()
        print(f"✅ Created test user: {user.email}")
    else:
        user.set_password('testpass123')
        user.email_verified = True
        user.otp_verified = True
        user.save()
        print(f"✅ Updated test user password and verification: {user.email}")
    
    # Create or get test service
    service, created = AstrologyService.objects.get_or_create(
        title="Test Gemstone Consultation",
        defaults={
            'service_type': 'GEMSTONE',
            'description': 'Professional gemstone recommendation for testing',
            'price': 1999.00,
            'duration_minutes': 60,
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created test service: {service.title}")
    else:
        print(f"✅ Found existing test service: {service.title}")
    
    print(f"\nTest Credentials:")
    print(f"Email: {user.email}")
    print(f"Password: testpass123")
    print(f"Service ID: {service.id}")
    print(f"Service Price: ₹{service.price}")

if __name__ == "__main__":
    create_test_data()
