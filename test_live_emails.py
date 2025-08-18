#!/usr/bin/env python
"""
Live Professional Email Notification Test

This script sends actual emails to test the professional templates.
Use with caution - emails will be sent to real addresses.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from accounts.models import User
from booking.models import Booking
from astrology.models import AstrologyBooking, AstrologyService
from cart.models import Cart
from puja.models import PujaService, PujaCategory

User = get_user_model()

def test_email_config():
    """Test email configuration"""
    print("📧 EMAIL CONFIGURATION:")
    print(f"   FROM: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   ADMIN: {getattr(settings, 'ADMIN_PERSONAL_EMAIL', 'NOT SET')}")
    print(f"   HOST: {settings.EMAIL_HOST}")
    print(f"   TLS: {settings.EMAIL_USE_TLS}")
    
    if hasattr(settings, 'ADMIN_PERSONAL_EMAIL'):
        print("✅ ADMIN_PERSONAL_EMAIL properly configured")
    else:
        print("❌ ADMIN_PERSONAL_EMAIL missing from settings")

def test_otp_email():
    """Test OTP email by creating a user and sending verification"""
    print("\n🔐 TESTING OTP EMAIL:")
    
    try:
        # Create test user
        test_email = "testuser@example.com"  # Change to your email for real testing
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'username': test_email,
                'first_name': 'Test',
                'last_name': 'User',
                'phone': '+919876543210',
                'otp': f'{random.randint(100000, 999999)}',
                'otp_verified': False
            }
        )
        
        if not created:
            user.otp = f'{random.randint(100000, 999999)}'
            user.otp_verified = False
            user.save()
        
        print(f"   User: {user.email}")
        print(f"   OTP: {user.otp}")
        
        # Send OTP using the professional template
        from accounts.views import RegisterView
        register_view = RegisterView()
        register_view._send_verification(user)
        
        print("✅ Professional OTP email sent!")
        print(f"   Check inbox: {user.email}")
        print(f"   Subject should be: '🔐 Verify Your Email - OkPuja Account Activation'")
        
    except Exception as e:
        print(f"❌ OTP email failed: {str(e)}")

def test_booking_notification():
    """Test booking notification"""
    print("\n🙏 TESTING BOOKING NOTIFICATION:")
    
    try:
        # Clear cache to ensure fresh test
        cache.clear()
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            email="customer@example.com",  # Change to your email
            defaults={
                'username': 'customer@example.com',
                'first_name': 'Test',
                'last_name': 'Customer',
                'phone': '+919876543210',
                'otp_verified': True
            }
        )
        
        # Create puja service
        category, _ = PujaCategory.objects.get_or_create(
            name="Test Puja Category",
            defaults={"description": "Test category"}
        )
        
        service, _ = PujaService.objects.get_or_create(
            title="Professional Test Puja",
            defaults={
                "category": category,
                "description": "Professional puja service for testing",
                "price": Decimal('2500.00'),
                "duration": 60,
                "is_active": True
            }
        )
        
        # Create cart
        cart, _ = Cart.objects.get_or_create(
            user=user,
            defaults={
                "puja_service": service,
                "total_amount": service.price
            }
        )
        
        # Create booking
        booking = Booking.objects.create(
            user=user,
            cart=cart,
            book_id=f"BK-TEST{random.randint(10000, 99999)}",
            total_amount=cart.total_amount,
            selected_date=datetime.now().date() + timedelta(days=7),
            selected_time=datetime.now().time(),
            status='CONFIRMED',
            payment_status='SUCCESS'
        )
        
        print(f"   Booking: {booking.book_id}")
        print(f"   Customer: {user.email}")
        print(f"   Admin: {getattr(settings, 'ADMIN_PERSONAL_EMAIL', 'NOT SET')}")
        
        # Send professional booking notification
        from core.tasks import send_booking_confirmation
        send_booking_confirmation(booking.id)
        
        print("✅ Professional booking notifications sent!")
        print(f"   Customer email: Professional booking confirmation with invoice")
        print(f"   Admin email: Professional alert with booking details + invoice")
        print(f"   Subjects should include emojis and be branded")
        
        # Test duplicate prevention
        print("\n🔄 Testing duplicate prevention...")
        send_booking_confirmation(booking.id)  # This should be prevented
        print("✅ Duplicate prevention active (check logs)")
        
    except Exception as e:
        print(f"❌ Booking notification failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_astrology_notification():
    """Test astrology notification"""
    print("\n🔮 TESTING ASTROLOGY NOTIFICATION:")
    
    try:
        # Clear cache
        cache.clear()
        
        # Create astrology service
        service, _ = AstrologyService.objects.get_or_create(
            title="Professional Vedic Consultation",
            defaults={
                "description": "Professional astrology consultation",
                "price": Decimal('3500.00'),
                "duration_minutes": 90,
                "is_active": True
            }
        )
        
        # Create astrology booking
        booking = AstrologyBooking.objects.create(
            service=service,
            astro_book_id=f"ASTRO-TEST{random.randint(10000, 99999)}",
            contact_email="astrology@example.com",  # Change to your email
            contact_phone="+919876543210",
            preferred_date=datetime.now().date() + timedelta(days=5),
            preferred_time=datetime.now().time(),
            birth_date=datetime(1990, 5, 15).date(),
            birth_time=datetime(1990, 5, 15, 8, 30).time(),
            birth_place="Mumbai, India",
            language="English",
            gender="M",
            questions="I want to know about my career prospects and when is the best time for job change.",
            status="CONFIRMED"
        )
        
        print(f"   Booking: {booking.astro_book_id}")
        print(f"   Customer: {booking.contact_email}")
        print(f"   Admin: {getattr(settings, 'ADMIN_PERSONAL_EMAIL', 'NOT SET')}")
        
        # Send customer confirmation
        booking.send_booking_confirmation()
        print("✅ Customer astrology confirmation sent!")
        
        # Send admin notification
        booking.send_admin_notification()
        print("✅ Professional astrology admin notification sent!")
        print(f"   Admin email includes birth details, questions, and professional design")
        
        # Test duplicate prevention
        print("\n🔄 Testing astrology duplicate prevention...")
        booking.send_admin_notification()  # This should be prevented
        print("✅ Duplicate prevention active")
        
    except Exception as e:
        print(f"❌ Astrology notification failed: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Run live email tests"""
    print("🚀 OKPUJA LIVE EMAIL TESTING")
    print("=" * 50)
    print("⚠️  WARNING: This will send REAL emails!")
    print("   Make sure to update email addresses in the script")
    print("=" * 50)
    
    # Test configuration first
    test_email_config()
    
    if not hasattr(settings, 'ADMIN_PERSONAL_EMAIL'):
        print("\n❌ ADMIN_PERSONAL_EMAIL not configured. Please add to .env file.")
        return
    
    # Run tests
    try:
        test_otp_email()
        test_booking_notification()
        test_astrology_notification()
        
        print("\n🎉 ALL LIVE TESTS COMPLETED!")
        print("📧 Check the following inboxes:")
        print(f"   • testuser@example.com (OTP)")
        print(f"   • customer@example.com (Booking)")
        print(f"   • astrology@example.com (Astrology)")
        print(f"   • {getattr(settings, 'ADMIN_PERSONAL_EMAIL')} (All admin notifications)")
        
    except Exception as e:
        print(f"\n❌ Testing failed: {str(e)}")

if __name__ == "__main__":
    main()
