#!/usr/bin/env python3
"""
Test Enhanced Admin Email with Google Maps Integration
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from accounts.models import User, Address
from booking.models import Booking
from core.tasks import send_booking_confirmation
from django.test import RequestFactory
import json

def test_enhanced_admin_email():
    """Test enhanced admin email with Google Maps integration"""
    
    print("🧪 Testing Enhanced Admin Email with Google Maps")
    print("=" * 50)
    
    try:
        # Get a test user and booking
        user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        if not user:
            print("❌ Test user not found")
            return
        
        print(f"✅ Found user: {user.email}")
        
        # Get or create a test address with landmark
        address, created = Address.objects.get_or_create(
            user=user,
            defaults={
                'address_line1': '123 Temple Street',
                'address_line2': 'Near Shiva Mandir',
                'city': 'Varanasi',
                'state': 'Uttar Pradesh',
                'postal_code': '221001',
                'country': 'India',
                'landmark': 'Kashi Vishwanath Temple',
                'is_default': True
            }
        )
        
        if created:
            print(f"✅ Created test address with landmark: {address.get_full_address()}")
        else:
            print(f"✅ Using existing address: {address.get_full_address()}")
        
        # Get a test booking
        booking = Booking.objects.filter(user=user).first()
        if not booking:
            print("❌ No booking found for testing")
            return
        
        print(f"✅ Found booking: {booking.book_id}")
        
        # Update booking with the test address
        booking.address = address
        booking.save()
        print(f"✅ Updated booking with address: {address.get_full_address()}")
        
        # Test the email sending
        print("\n📧 Sending enhanced admin notification email...")
        
        # Call the task directly (not async for testing)
        result = send_booking_confirmation(booking.id)
        
        print(f"✅ Email task result: {result}")
        
        print("\n🎯 Admin email should now include:")
        print("  • Enhanced customer information with contact links")
        print("  • Google Maps navigation card")
        print("  • Clickable location for easy navigation")
        print("  • Complete service details")
        print("  • Professional branding with OkPuja styling")
        
        print("\n🗺️ Google Maps Integration Features:")
        print(f"  • Full Address: {address.get_full_address()}")
        print("  • Clickable navigation card")
        print("  • Direct Google Maps links")
        print("  • Mobile-responsive design")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_admin_email()
